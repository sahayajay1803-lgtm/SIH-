import re
from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    approval_id: str
    title: str
    content: str
    source: str

KNOWLEDGE_BASE = (
    KnowledgeChunk(
        chunk_id="factory-license-overview",
        approval_id="factory_license",
        title="Factory License overview",
        content="A factory license is included for the illustrative manufacturing workflow. Verify the competent authority, thresholds, forms, and required documents before applying.",
        source="Illustrative placeholder - verify with the competent authority",
    ),
    KnowledgeChunk(
        chunk_id="pollution-consent-overview",
        approval_id="pollution_consent",
        title="Consent to Establish overview",
        content="Consent to Establish is included for the illustrative industrial workflow where pollution impacts may occur. Confirm the applicable category and current Maharashtra Pollution Control Board process.",
        source="Illustrative placeholder - verify with the competent authority",
    ),
    KnowledgeChunk(
        chunk_id="local-body-noc-overview",
        approval_id="local_body_noc",
        title="Local Body No-Objection Certificate overview",
        content="A local body no-objection certificate is included for an illustrative new setup. Confirm the local authority, site requirements, and current application process.",
        source="Illustrative placeholder - verify with the competent authority",
    ),
    KnowledgeChunk(
        chunk_id="fire-noc-overview",
        approval_id="fire_noc",
        title="Fire Safety No-Objection Certificate overview",
        content="A fire safety no-objection certificate is included for the illustrative workflow when the profile crosses the demo scale trigger. Confirm the current fire department requirements and thresholds.",
        source="Illustrative placeholder - verify with the competent authority",
    ),
)


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 2}


def retrieve(approval_id: str, query: str = "", *, limit: int = 3) -> list[KnowledgeChunk]:
    """Return the most relevant source-labelled chunks for an already-selected approval."""
    query_tokens = _tokens(f"{approval_id} {query}")
    candidates = [chunk for chunk in KNOWLEDGE_BASE if chunk.approval_id == approval_id]
    ranked = sorted(
        candidates,
        key=lambda chunk: len(query_tokens & _tokens(f"{chunk.title} {chunk.content}")),
        reverse=True,
    )
    return ranked[: max(0, limit)]