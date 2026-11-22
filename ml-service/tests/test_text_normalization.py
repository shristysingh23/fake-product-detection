"""Tests for deterministic OCR text normalization using synthetic strings."""

import pytest

from app.text_normalization import normalize_text


def test_normalizes_uppercase_and_lowercase_with_casefold():
    assert normalize_text("MAGGI maggi") == "maggi maggi"


def test_trims_leading_and_trailing_spaces():
    assert normalize_text("   Product Name   ") == "product name"


def test_collapses_multiple_spaces():
    assert normalize_text("Product     Name") == "product name"


def test_collapses_tabs_newlines_and_unicode_whitespace():
    assert normalize_text("Product\t\nName\u00a0Model") == "product name model"


def test_standardizes_punctuation_and_special_characters_as_separators():
    assert normalize_text("Brand—Name™ / Product®: A&B!") == (
        "brand nametm product a b"
    )


def test_nfkc_normalizes_compatibility_characters():
    assert normalize_text("ＰＲＯＤＵＣＴ　１２") == "product 12"


def test_empty_string_returns_empty_string():
    assert normalize_text("") == ""


def test_none_returns_empty_string():
    assert normalize_text(None) == ""


def test_preserves_product_names_and_meaningful_numbers():
    assert normalize_text("iPhone 15 Pro") == "iphone 15 pro"


def test_preserves_model_identifier_digits_and_unit_tokens():
    assert normalize_text("500 ml") == "500 ml"
    assert normalize_text("2.4 GHz") == "2 4 ghz"
    assert normalize_text("AB-123") == "ab 123"


def test_repeated_calls_are_deterministic():
    text = "  ＡＢ-123\t500 ml\n"

    assert normalize_text(text) == normalize_text(text) == "ab 123 500 ml"


def test_does_not_map_unrelated_words_to_a_catalog_value():
    assert normalize_text("unrelated sample words") == "unrelated sample words"


def test_rejects_non_string_values_other_than_none():
    with pytest.raises(TypeError, match="string or None"):
        normalize_text(123)  # type: ignore[arg-type]
