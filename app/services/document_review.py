import io
import json
from dataclasses import dataclass
from uuid import uuid4

from pypdf import PdfReader

from app.schemas import DocumentReview
from app.services.llm import LLMUnavailable, OllamaCloudClient, parse_json_object


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    content_type: str
    file_name: str


def extract_document(file_name: str, content_type: str, content: bytes) -> ExtractedDocument:
    if content_type == "application/pdf":
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif content_type in {"image/jpeg", "image/png"}:
        text = "Image uploaded. OCR is not enabled in this MVP; visual evidence must be confirmed by a human reviewer."
    else:
        raise ValueError("Supported document types are PDF, JPG, and PNG")
    return ExtractedDocument(text=text[:20000], content_type=content_type, file_name=file_name)


REVIEW_SYSTEM = """You are a document pre-validation assistant for an industrial approvals platform.
Review only the supplied document text and metadata. Do not decide legal eligibility or claim that a document is legally valid.
Return JSON with exactly these keys: score (integer 0-100), summary, strengths (array of strings), issues (array of strings), recommendations (array of strings).
Give constructive, specific feedback. State clearly when OCR or source text is unavailable."""


async def review_document(document: ExtractedDocument, llm: OllamaCloudClient) -> DocumentReview:
    context = json.dumps({"file_name": document.file_name, "content_type": document.content_type, "text": document.text})
    try:
        raw = await llm.generate(context, REVIEW_SYSTEM)
        result = parse_json_object(raw)
        return DocumentReview(
            review_id=uuid4(), file_name=document.file_name, content_type=document.content_type,
            status="reviewed", extracted_text_preview=document.text[:500], model=llm.model, **result,
        )
    except LLMUnavailable:
        raise
    except (ValueError, json.JSONDecodeError, TypeError) as exc:
        raise ValueError("The AI returned an invalid document review") from exc