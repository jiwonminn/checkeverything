"""Match extracted claims against fetched source content."""

from google.genai import types

from backend.gemini_client import generate_with_fallback, get_client
from backend.source_checker import parse_domain
from backend.trust_models import (
    ClaimAnalysis,
    ClaimDraft,
    ClaimMatchingDraft,
    CheckedSource,
    SupportLabel,
)

MAX_CLAIMS_TO_MATCH = 8
SOURCE_EXCERPT_CHARS = 3_000

CLAIM_MATCH_INSTRUCTION = """You compare factual claims against fetched source excerpts for CheckEverything.

For each claim:
1. Choose the most relevant source URL from the provided sources, if any.
2. Compare the claim against the source title and excerpt only.
3. Return one support_label:
   - supported: the excerpt clearly supports the claim
   - weakly_supported: related but does not clearly prove the full claim
   - not_supported: the excerpt contradicts or fails to support the claim
   - unclear: insufficient excerpt evidence to decide
   - source_unavailable: no usable source content or no relevant source

Use cautious wording in evidence_note. Never say "false" or "misinformation".
If a source is unreachable or has no excerpt, use source_unavailable.
"""

SUPPORT_TO_STATUS = {
    "supported": "strongly_supported",
    "weakly_supported": "weakly_supported",
    "not_supported": "unsupported",
    "unclear": "unclear",
    "source_unavailable": "unclear",
}


def support_label_to_status(label: SupportLabel) -> str:
    return SUPPORT_TO_STATUS[label]


def _pick_related_source(claim: ClaimDraft, sources: list[CheckedSource]) -> CheckedSource | None:
    if claim.related_citations:
        citation_set = set(claim.related_citations)
        for source in sources:
            if source.url in citation_set:
                return source
    return None


def _format_sources_for_matching(sources: list[CheckedSource]) -> str:
    if not sources:
        return "(no sources available)"
    blocks = []
    for source in sources:
        excerpt = (source.page_text or "")[:SOURCE_EXCERPT_CHARS] or "(no extractable content)"
        blocks.append(
            f"URL: {source.url}\n"
            f"Domain: {source.domain}\n"
            f"Reachable: {source.reachable}\n"
            f"Title: {source.title or '(no title)'}\n"
            f"Excerpt:\n{excerpt}\n"
        )
    return "\n---\n".join(blocks)


def _format_claims_for_matching(claims: list[ClaimDraft]) -> str:
    lines = []
    for index, claim in enumerate(claims[:MAX_CLAIMS_TO_MATCH], start=1):
        citations = ", ".join(claim.related_citations) if claim.related_citations else "(none)"
        lines.append(f"{index}. Claim: {claim.text}\n   Related citations: {citations}")
    return "\n".join(lines)


def _fallback_match(claim: ClaimDraft, sources: list[CheckedSource]) -> ClaimAnalysis:
    related = _pick_related_source(claim, sources)
    if not sources or not related:
        return ClaimAnalysis(
            text=claim.text,
            status="unclear",
            citations=claim.related_citations,
            note=claim.note,
            matched_source=None,
            support_label="source_unavailable",
            evidence_note="No usable source content was available for this claim.",
        )
    if not related.reachable or not related.page_text:
        return ClaimAnalysis(
            text=claim.text,
            status="unclear",
            citations=claim.related_citations or [related.url],
            note=claim.note,
            matched_source=related.url,
            support_label="source_unavailable",
            evidence_note="Source unavailable or content could not be extracted.",
        )
    return ClaimAnalysis(
        text=claim.text,
        status=claim.status,
        citations=claim.related_citations or [related.url],
        note=claim.note,
        matched_source=related.url,
        support_label="unclear",
        evidence_note="Source content was fetched, but automated matching was unavailable.",
    )


def _merge_match(
    claim: ClaimDraft,
    match_item,
    sources: list[CheckedSource],
) -> ClaimAnalysis:
    matched_source = match_item.matched_source
    if matched_source:
        known_urls = {source.url for source in sources}
        if matched_source not in known_urls:
            matched_source = None

    support_label = match_item.support_label
    if matched_source:
        source = next((item for item in sources if item.url == matched_source), None)
        if source and (not source.reachable or not source.page_text):
            support_label = "source_unavailable"
    elif support_label != "source_unavailable" and not sources:
        support_label = "source_unavailable"

    citations = claim.related_citations[:]
    if matched_source and matched_source not in citations:
        citations.append(matched_source)

    return ClaimAnalysis(
        text=claim.text,
        status=support_label_to_status(support_label),
        citations=citations,
        note=claim.note,
        matched_source=matched_source,
        support_label=support_label,
        evidence_note=match_item.evidence_note,
    )


def match_claims_to_sources(
    claims: list[ClaimDraft],
    sources: list[CheckedSource],
) -> list[ClaimAnalysis]:
    """Compare claims against source excerpts using Gemini."""
    trimmed_claims = claims[:MAX_CLAIMS_TO_MATCH]
    if not trimmed_claims:
        return []

    if not sources:
        return [_fallback_match(claim, sources) for claim in trimmed_claims]

    usable_sources = [source for source in sources if source.reachable and source.page_text]
    if not usable_sources:
        return [_fallback_match(claim, sources) for claim in trimmed_claims]

    prompt = (
        "Claims to evaluate:\n"
        f"{_format_claims_for_matching(trimmed_claims)}\n\n"
        "Available sources:\n"
        f"{_format_sources_for_matching(sources)}"
    )

    client = get_client()
    response = generate_with_fallback(
        client,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=CLAIM_MATCH_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ClaimMatchingDraft,
            temperature=0.1,
        ),
    )
    draft = ClaimMatchingDraft.model_validate_json(response.text)
    matches_by_text = {item.claim_text.strip(): item for item in draft.matches}

    enriched: list[ClaimAnalysis] = []
    for claim in trimmed_claims:
        match_item = matches_by_text.get(claim.text.strip())
        if match_item is None:
            enriched.append(_fallback_match(claim, sources))
            continue
        enriched.append(_merge_match(claim, match_item, sources))
    return enriched


def build_support_summary(claims: list[ClaimAnalysis]) -> str:
    if not claims:
        return "No factual claims were extracted."
    counts = {
        "supported": 0,
        "weakly_supported": 0,
        "not_supported": 0,
        "unclear": 0,
        "source_unavailable": 0,
    }
    for claim in claims:
        label = claim.support_label or "unclear"
        counts[label] = counts.get(label, 0) + 1
    matched = counts["supported"] + counts["weakly_supported"]
    return (
        f"Claim-source matching: {matched}/{len(claims)} claims had supporting or partial source evidence. "
        f"{counts['source_unavailable']} source(s) unavailable."
    )


def domain_from_url(url: str | None) -> str | None:
    if not url:
        return None
    domain = parse_domain(url)
    return domain or None
