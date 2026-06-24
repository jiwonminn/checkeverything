"""Google ADK trust analysis graph — claim extraction then claim-to-source matching."""

from google.adk.agents import LlmAgent, SequentialAgent

from backend.claim_matcher import CLAIM_MATCH_INSTRUCTION
from backend.gemini_client import get_model
from backend.trust_models import ClaimMatchingDraft, TrustAnalysisDraft
from backend.trust_prompts import TRUST_ANALYSIS_INSTRUCTION

_MODEL = get_model()

trust_extractor_agent = LlmAgent(
    name="trust_extractor_agent",
    model=_MODEL,
    description="Extracts factual claims and category credibility scores from AI responses.",
    instruction=TRUST_ANALYSIS_INSTRUCTION,
    output_schema=TrustAnalysisDraft,
    output_key="trust_draft",
)

trust_matcher_agent = LlmAgent(
    name="trust_matcher_agent",
    model=_MODEL,
    description="Matches extracted claims against fetched source excerpts.",
    instruction=f"""You are the claim-to-source matching step for CheckEverything trust analysis.

Read the extracted trust_draft from session state (claims list).
Use the AI response text and checked source metadata from the user message.

{CLAIM_MATCH_INSTRUCTION}
""",
    output_schema=ClaimMatchingDraft,
    output_key="claim_matches",
)

trust_root_agent = SequentialAgent(
    name="checkeverything_trust_root",
    description="Extract claims and category scores, then match claims to cited sources.",
    sub_agents=[trust_extractor_agent, trust_matcher_agent],
)
