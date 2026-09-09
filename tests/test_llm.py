import pytest

from app.services.llm import parse_json_object


def test_parse_json_object_accepts_markdown_fenced_response():
    assert parse_json_object('```json\n{"reply":"ok"}\n```') == {"reply": "ok"}


def test_parse_json_object_extracts_json_from_short_prose():
    assert parse_json_object('Here is the result: {"reply":"ok"}') == {"reply": "ok"}


def test_parse_json_object_rejects_non_object_json():
    with pytest.raises(ValueError):
        parse_json_object("[\"not an object\"]")