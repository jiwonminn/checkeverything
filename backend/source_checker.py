"""Fetch and classify cited URLs for trust analysis."""

from __future__ import annotations

import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from backend.trust_models import CheckedSource, SourceCheckSummary, SourceQualityLevel

USER_AGENT = "CheckEverything/1.0 (trust-source-checker)"
FETCH_TIMEOUT_SEC = 8
MAX_SOURCES = 10
MAX_BODY_BYTES = 50_000

URL_PATTERN = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

HIGH_AUTHORITY_SUFFIXES = (".gov", ".edu", ".mil")
HIGH_AUTHORITY_DOMAINS = {
    "w3.org",
    "ieee.org",
    "iso.org",
    "nist.gov",
    "who.int",
    "cdc.gov",
    "nih.gov",
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "nature.com",
    "sciencedirect.com",
    "springer.com",
    "arxiv.org",
}
MEDIUM_HIGH_NEWS_DOMAINS = {
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
    "nytimes.com",
    "washingtonpost.com",
    "theguardian.com",
    "economist.com",
    "wsj.com",
    "ft.com",
}
LOW_MEDIUM_DOMAINS = {
    "reddit.com",
    "stackoverflow.com",
    "quora.com",
    "medium.com",
    "substack.com",
    "wordpress.com",
    "blogspot.com",
    "tumblr.com",
}


def extract_urls_from_text(text: str) -> list[str]:
    found: list[str] = []
    for match in URL_PATTERN.findall(text):
        url = match.rstrip(".,;:")
        if url not in found:
            found.append(url)
    return found


def merge_urls(explicit_urls: list[str], text: str) -> list[str]:
    merged: list[str] = []
    for url in [*explicit_urls, *extract_urls_from_text(text)]:
        normalized = url.strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
        if len(merged) >= MAX_SOURCES:
            break
    return merged


def parse_domain(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _domain_matches(domain: str, candidates: set[str]) -> bool:
    return domain in candidates or any(domain.endswith(f".{name}") for name in candidates)


def classify_domain(domain: str, reachable: bool) -> tuple[SourceQualityLevel, str]:
    if not domain:
        return "low", "Could not determine domain."
    if not reachable:
        return "low", "Broken or inaccessible citation."

    if domain.endswith(HIGH_AUTHORITY_SUFFIXES) or _domain_matches(domain, HIGH_AUTHORITY_DOMAINS):
        return "high", "Government, university, or primary authority source."

    if _domain_matches(domain, MEDIUM_HIGH_NEWS_DOMAINS):
        return "medium-high", "Major reputable news organization."

    if _domain_matches(domain, LOW_MEDIUM_DOMAINS):
        return "low-medium", "Forum, blog, or community source — verify independently."

    if domain.count(".") >= 2 and any(
        part in domain for part in ("blog", "forum", "community", "discuss")
    ):
        return "low-medium", "Informal or community-style source."

    if any(part in domain for part in ("docs.", "developer.", "support.")):
        return "medium", "Official product or developer documentation."

    return "medium", "Reachable source, but authority level is unclear."


def _extract_title(html: str) -> str | None:
    match = TITLE_PATTERN.search(html)
    if not match:
        return None
    title = unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return title[:200] if title else None


def fetch_url_metadata(url: str) -> CheckedSource:
    domain = parse_domain(url)
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=FETCH_TIMEOUT_SEC) as response:
            status_code = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
            body = response.read(MAX_BODY_BYTES)
            reachable = 200 <= status_code < 400
            title = None
            if "html" in content_type.lower():
                title = _extract_title(body.decode("utf-8", errors="ignore"))
    except HTTPError as exc:
        status_code = exc.code
        reachable = False
        title = None
    except (URLError, TimeoutError, ValueError):
        status_code = None
        reachable = False
        title = None

    quality, quality_note = classify_domain(domain, reachable)
    notes = quality_note
    if title:
        notes = f"{quality_note} Title: {title}"

    return CheckedSource(
        url=url,
        domain=domain or "unknown",
        reachable=reachable,
        status_code=status_code,
        title=title,
        source_quality=quality,
        notes=notes,
    )


def check_sources(urls: list[str]) -> list[CheckedSource]:
    return [fetch_url_metadata(url) for url in urls[:MAX_SOURCES]]


def is_primary_official_source(source: CheckedSource) -> bool:
    if not source.reachable:
        return False
    if source.domain.endswith(HIGH_AUTHORITY_SUFFIXES):
        return True
    return _domain_matches(source.domain, HIGH_AUTHORITY_DOMAINS)


def build_source_summary(sources: list[CheckedSource]) -> SourceCheckSummary:
    reachable_count = sum(1 for source in sources if source.reachable)
    primary_official_count = sum(1 for source in sources if is_primary_official_source(source))
    issues: list[str] = []

    unreachable = [source for source in sources if not source.reachable]
    if unreachable:
        count = len(unreachable)
        noun = "citation was" if count == 1 else "citations were"
        issues.append(f"Potential issue: {count} {noun} unreachable")

    low_quality = [
        source
        for source in sources
        if source.reachable and source.source_quality in ("low", "low-medium")
    ]
    if low_quality:
        count = len(low_quality)
        noun = "source may" if count == 1 else "sources may"
        issues.append(f"Potential issue: {count} {noun} need independent verification")

    return SourceCheckSummary(
        sources_checked=len(sources),
        reachable_count=reachable_count,
        primary_official_count=primary_official_count,
        issues=issues,
    )


def format_sources_for_prompt(sources: list[CheckedSource]) -> str:
    if not sources:
        return "(no sources checked)"
    lines = []
    for source in sources:
        title = source.title or "(no title)"
        lines.append(
            f"- {source.url}\n"
            f"  domain: {source.domain}\n"
            f"  reachable: {source.reachable}\n"
            f"  status_code: {source.status_code}\n"
            f"  title: {title}\n"
            f"  source_quality: {source.source_quality}\n"
            f"  notes: {source.notes}"
        )
    return "\n".join(lines)
