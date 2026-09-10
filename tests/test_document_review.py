from app.services.document_review import extract_document


def test_image_review_extracts_explicit_ocr_limitation():
    extracted = extract_document("license.png", "image/png", b"image-bytes")
    assert "OCR is not enabled" in extracted.text


def test_document_type_is_rejected():
    import pytest

    with pytest.raises(ValueError):
        extract_document("license.txt", "text/plain", b"text")