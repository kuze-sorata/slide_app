import pytest

from app.utils.json_extract import extract_json_object


def test_extract_json_object_from_wrapped_text() -> None:
    raw_text = '補足です {"deck_title":"test","slides":[]} 以上です'
    assert extract_json_object(raw_text) == '{"deck_title":"test","slides":[]}'


def test_extract_json_object_raises_when_missing() -> None:
    with pytest.raises(ValueError):
        extract_json_object("jsonなし")
