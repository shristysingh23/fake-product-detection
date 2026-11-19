"""Checks the verified production catalog against representative OCR fixtures."""

import json
from pathlib import Path

from app.catalog import load_product_catalog
from app.product_matcher import MatchOutcome, identify_product


OCR_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "product_catalog_ocr.json"


def test_production_catalog_contains_exactly_three_valid_unique_records():
    products = load_product_catalog()

    assert len(products) == 3
    assert len({product.product_id for product in products}) == 3
    assert all(product.product_id.strip() for product in products)
    assert all(product.brand.strip() and product.product_name.strip() for product in products)
    assert {(product.brand, product.product_name) for product in products} == {
        ("MAGGI", "2-Minute Masala Noodles"),
        ("Dove", "Daily Shine Shampoo"),
        ("Amul", "Pasteurised Butter"),
    }


def test_representative_ocr_text_identifies_each_catalog_product():
    products = load_product_catalog()
    fixtures = json.loads(OCR_FIXTURE_PATH.read_text(encoding="utf-8"))
    expected_ids = {
        "maggi.jpg": "maggi-2-minute-masala-noodles",
        "dove.webp": "dove-daily-shine-shampoo",
        "amul.jpg": "amul-pasteurised-butter",
    }

    assert set(fixtures) == set(expected_ids)
    for filename, expected_product_id in expected_ids.items():
        match = identify_product(fixtures[filename], products)
        assert match.outcome is MatchOutcome.IDENTIFIED, filename
        assert match.product_id == expected_product_id
