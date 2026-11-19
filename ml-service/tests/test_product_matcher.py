"""Deterministic matching tests with synthetic, temporary catalog records."""

import json

import pytest

from app.catalog import CatalogLoadError, load_product_catalog
from app.product_matcher import (
    MatchOutcome,
    MatcherConfig,
    identify_product,
)


def product(product_id, brand, name, *, brand_aliases=None, product_aliases=None):
    return {
        "product_id": product_id,
        "brand": brand,
        "product_name": name,
        "category": "Synthetic Test Category",
        "brand_aliases": brand_aliases or [],
        "product_aliases": product_aliases or [],
    }


def catalog_file(tmp_path, records):
    path = tmp_path / "products.json"
    path.write_text(json.dumps({"schema_version": 1, "products": records}), encoding="utf-8")
    return load_product_catalog(path)


@pytest.fixture
def sample_catalog(tmp_path):
    return catalog_file(tmp_path, [product(
        "test-noodle-1", "North Star Foods", "Spicy Rice Noodles 500g",
        brand_aliases=["NSF"], product_aliases=["Hot Rice Noodles 500g"],
    )])


def lines(*values):
    return [{"text": text, "confidence": confidence} for text, confidence in values]


def test_exact_brand_and_product_match(sample_catalog):
    result = identify_product(lines(("North Star Foods", .9), ("Spicy Rice Noodles 500g", .95)), sample_catalog)

    assert result.outcome is MatchOutcome.IDENTIFIED
    assert (result.brand, result.product, result.category) == (
        "North Star Foods", "Spicy Rice Noodles 500g", "Synthetic Test Category"
    )
    assert result.product_id == "test-noodle-1"


def test_matches_brand_alias(sample_catalog):
    result = identify_product(lines(("NSF", .9), ("Spicy Rice Noodles 500g", .9)), sample_catalog)

    assert result.outcome is MatchOutcome.IDENTIFIED
    assert result.brand == "North Star Foods"


def test_matches_product_alias(sample_catalog):
    result = identify_product(lines(("North Star Foods", .9), ("Hot Rice Noodles 500g", .9)), sample_catalog)

    assert result.outcome is MatchOutcome.IDENTIFIED
    assert result.product == "Spicy Rice Noodles 500g"


def test_case_and_punctuation_variation(sample_catalog):
    result = identify_product(
        lines(("NORTH-STAR FOODS!", .9), ("SPICY / RICE—NOODLES 500g", .9)), sample_catalog
    )

    assert result.outcome is MatchOutcome.IDENTIFIED


def test_minor_ocr_spelling_errors_are_supported(sample_catalog):
    result = identify_product(lines(("North Star Foods", .9), ("Spicy Rice Nood1es 500g", .9)), sample_catalog)

    assert result.outcome is MatchOutcome.IDENTIFIED


def test_product_number_is_preserved_and_matched(sample_catalog):
    result = identify_product(lines(("North Star Foods", .9), ("Spicy Rice Noodles 500g", .9)), sample_catalog)

    assert result.outcome is MatchOutcome.IDENTIFIED
    assert "500g" in result.product


def test_generic_words_do_not_identify_a_product(sample_catalog):
    result = identify_product(lines(("North Star Foods", .9), ("Original Product", .99)), sample_catalog)

    assert result.outcome is MatchOutcome.NOT_FOUND
    assert result.brand == "North Star Foods"
    assert result.product == ""


@pytest.mark.parametrize("ocr", [[], None, [{"text": "  ", "confidence": .9}]])
def test_empty_ocr_input_is_not_found(sample_catalog, ocr):
    assert identify_product(ocr, sample_catalog).outcome is MatchOutcome.NOT_FOUND


def test_unrelated_ocr_text_is_not_found(sample_catalog):
    result = identify_product(lines(("Garden Tools", .99), ("Steel Trowel", .99)), sample_catalog)

    assert result.outcome is MatchOutcome.NOT_FOUND
    assert not result.brand and not result.product


def test_brand_can_be_returned_without_product_identification(sample_catalog):
    result = identify_product(lines(("North Star Foods", .9), ("Delicious", .9)), sample_catalog)

    assert result.outcome is MatchOutcome.NOT_FOUND
    assert result.brand == "North Star Foods"
    assert result.product == ""


def test_ambiguous_products_from_same_brand_leave_product_empty(tmp_path):
    catalog = catalog_file(tmp_path, [
        product("cola-zero", "Bright Drinks", "Cola Zero"),
        product("cola-light", "Bright Drinks", "Cola Light"),
    ])

    result = identify_product(lines(("Bright Drinks", .9), ("Cola Zero", .9), ("Cola Light", .9)), catalog)

    assert result.outcome is MatchOutcome.AMBIGUOUS
    assert result.brand == "Bright Drinks"
    assert result.product == ""
    assert len(result.candidates) == 2


def test_ambiguous_candidates_from_different_brands_leave_brand_empty(tmp_path):
    catalog = catalog_file(tmp_path, [
        product("alpha", "Alpha Foods", "Oat Crunch"),
        product("beta", "Beta Foods", "Oat Crunch"),
    ])

    result = identify_product(lines(("Alpha Foods", .9), ("Beta Foods", .9), ("Oat Crunch", .9)), catalog)

    assert result.outcome is MatchOutcome.AMBIGUOUS
    assert result.brand == ""
    assert result.product == ""


def test_conflicting_product_evidence_is_ambiguous(tmp_path):
    catalog = catalog_file(tmp_path, [
        product("mint", "Green Leaf", "Mint Toothpaste"),
        product("herbal", "Green Leaf", "Herbal Toothpaste"),
    ])

    result = identify_product(lines(("Green Leaf", .9), ("Mint Toothpaste", .9), ("Herbal Toothpaste", .9)), catalog)

    assert result.outcome is MatchOutcome.AMBIGUOUS
    assert result.product == ""


@pytest.mark.parametrize("confidence", [None, "invalid", -1, 2, float("nan"), float("inf")])
def test_missing_or_invalid_confidence_is_safe(sample_catalog, confidence):
    result = identify_product([{"text": "North Star Foods", "confidence": confidence},
                               {"text": "Spicy Rice Noodles 500g"}], sample_catalog)

    assert result.outcome is MatchOutcome.IDENTIFIED


def test_ocr_confidence_does_not_override_weak_product_evidence(sample_catalog):
    result = identify_product(lines(("North Star Foods", 1.0), ("Original Product", 1.0)), sample_catalog)

    assert result.outcome is MatchOutcome.NOT_FOUND
    assert result.product == ""


def test_multiple_candidates_are_ranked_by_match_strength(tmp_path):
    catalog = catalog_file(tmp_path, [
        product("other", "North Star Foods", "Rice Crackers"),
        product("target", "North Star Foods", "Spicy Rice Noodles 500g"),
    ])

    result = identify_product(lines(("North Star Foods", .5), ("Spicy Rice Noodles 500g", .5)), catalog)

    assert result.outcome is MatchOutcome.IDENTIFIED
    assert result.candidates[0].product_id == "target"
    assert result.candidates[0].combined_score > result.candidates[1].combined_score


def test_winning_score_margin_is_required(tmp_path):
    catalog = catalog_file(tmp_path, [
        product("first", "One Brand", "Red Apple"),
        product("second", "One Brand", "Red Apples"),
    ])
    config = MatcherConfig(minimum_winning_margin=0.20)

    result = identify_product(lines(("One Brand", .9), ("Red Apple", .9)), catalog, config=config)

    assert result.outcome is MatchOutcome.AMBIGUOUS


def test_threshold_boundary_is_inclusive_and_above_boundary_is_not(tmp_path):
    catalog = catalog_file(tmp_path, [product("boundary", "One Brand", "Red Apple")])
    at_boundary = MatcherConfig(
        minimum_brand_score=1.0, minimum_product_score=1.0,
        minimum_identification_score=1.0, minimum_winning_margin=0.0,
    )
    above_boundary = MatcherConfig(
        minimum_brand_score=1.0001, minimum_product_score=1.0,
        minimum_identification_score=1.0, minimum_winning_margin=0.0,
    )
    ocr = lines(("One Brand", .5), ("Red Apple", .5))

    assert identify_product(ocr, catalog, config=at_boundary).outcome is MatchOutcome.IDENTIFIED
    assert identify_product(ocr, catalog, config=above_boundary).outcome is MatchOutcome.AMBIGUOUS


def test_invalid_catalog_loader_error_is_not_converted_to_not_found(monkeypatch):
    def fail_to_load():
        raise CatalogLoadError("synthetic catalog read failure")

    monkeypatch.setattr("app.product_matcher.get_product_catalog", fail_to_load)
    with pytest.raises(CatalogLoadError, match="synthetic catalog read failure"):
        identify_product(lines(("anything", .9)))


def test_unvalidated_catalog_records_are_rejected():
    with pytest.raises(TypeError, match="validated ProductRecord"):
        identify_product(lines(("anything", .9)), [{"brand": "raw"}])


def test_single_generic_product_token_never_identifies(tmp_path):
    catalog = catalog_file(tmp_path, [product("generic", "Generic Brand", "Original Product")])

    result = identify_product(lines(("Generic Brand", .99), ("Original", .99)), catalog)

    assert result.outcome is MatchOutcome.NOT_FOUND
    assert result.product == ""
