"""Tests for catalog loading and validation using test-only product fixtures."""

import json

import pytest

from app import catalog
from app.catalog import (
    CatalogLoadError,
    CatalogValidationError,
    ProductRecord,
    load_product_catalog,
)


def product_record(**overrides):
    record = {
        "product_id": "test-product-001",
        "brand": "Test Brand",
        "product_name": "Test Product",
        "category": "Test Category",
        "brand_aliases": ["TB"],
        "product_aliases": ["Test Item"],
    }
    record.update(overrides)
    return record


def write_catalog(path, products=None, schema_version=1):
    path.write_text(
        json.dumps({"schema_version": schema_version, "products": products or []}),
        encoding="utf-8",
    )
    return path


def test_loads_valid_empty_catalog(tmp_path):
    path = write_catalog(tmp_path / "products.json")

    result = load_product_catalog(path)

    assert result == ()


def test_loads_valid_product_record(tmp_path):
    path = write_catalog(tmp_path / "products.json", [product_record()])

    result = load_product_catalog(path)

    assert result == (
        ProductRecord(
            product_id="test-product-001",
            brand="Test Brand",
            product_name="Test Product",
            category="Test Category",
            brand_aliases=("TB",),
            product_aliases=("Test Item",),
        ),
    )


@pytest.mark.parametrize(
    "field",
    [
        "product_id",
        "brand",
        "product_name",
        "category",
        "brand_aliases",
        "product_aliases",
    ],
)
def test_rejects_missing_product_fields(tmp_path, field):
    record = product_record()
    del record[field]
    path = write_catalog(tmp_path / "products.json", [record])

    with pytest.raises(CatalogValidationError, match="missing fields"):
        load_product_catalog(path)


def test_rejects_duplicate_product_ids(tmp_path):
    first = product_record()
    second = product_record(brand="Other Test Brand", product_name="Other Test Product")
    path = write_catalog(tmp_path / "products.json", [first, second])

    with pytest.raises(CatalogValidationError, match="Duplicate product_id"):
        load_product_catalog(path)


@pytest.mark.parametrize(
    ("field", "value"),
    [("brand", "  "), ("product_name", "")],
)
def test_rejects_empty_canonical_brand_or_product_name(tmp_path, field, value):
    path = write_catalog(tmp_path / "products.json", [product_record(**{field: value})])

    with pytest.raises(CatalogValidationError, match=f"{field} must be a non-empty string"):
        load_product_catalog(path)


@pytest.mark.parametrize("category", [1, [], {}])
def test_rejects_non_string_non_null_category(tmp_path, category):
    path = write_catalog(tmp_path / "products.json", [product_record(category=category)])

    with pytest.raises(CatalogValidationError, match="category must be a string or null"):
        load_product_catalog(path)


def test_accepts_null_category(tmp_path):
    path = write_catalog(tmp_path / "products.json", [product_record(category=None)])

    result = load_product_catalog(path)

    assert result[0].category is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("brand_aliases", "Test Brand"),
        ("product_aliases", ["Test Item", 7]),
        ("brand_aliases", [""]),
    ],
)
def test_rejects_invalid_alias_types_or_empty_aliases(tmp_path, field, value):
    path = write_catalog(tmp_path / "products.json", [product_record(**{field: value})])

    with pytest.raises(CatalogValidationError):
        load_product_catalog(path)


def test_rejects_conflicting_normalized_brand_aliases(tmp_path):
    first = product_record(brand="First Test Brand", brand_aliases=["Shared Alias"])
    second = product_record(
        product_id="test-product-002",
        brand="Second Test Brand",
        product_name="Another Test Product",
        brand_aliases=["shared-alias"],
    )
    path = write_catalog(tmp_path / "products.json", [first, second])

    with pytest.raises(CatalogValidationError, match="Conflicting normalized brand alias"):
        load_product_catalog(path)


def test_rejects_product_alias_collision_within_same_brand(tmp_path):
    first = product_record(brand="Shared Test Brand", product_aliases=["Shared Item"])
    second = product_record(
        product_id="test-product-002",
        brand="Shared Test Brand",
        product_name="Another Test Product",
        product_aliases=["shared-item"],
    )
    path = write_catalog(tmp_path / "products.json", [first, second])

    with pytest.raises(CatalogValidationError, match="Conflicting normalized product alias"):
        load_product_catalog(path)


def test_rejects_invalid_json(tmp_path):
    path = tmp_path / "products.json"
    path.write_text('{"schema_version":', encoding="utf-8")

    with pytest.raises(CatalogLoadError, match="contains invalid JSON"):
        load_product_catalog(path)


def test_rejects_catalog_that_is_not_valid_utf8(tmp_path):
    path = tmp_path / "products.json"
    path.write_bytes(b"\xff\xfe\xfa")

    with pytest.raises(CatalogLoadError, match="is not valid UTF-8"):
        load_product_catalog(path)


def test_rejects_unsupported_schema_version(tmp_path):
    path = write_catalog(tmp_path / "products.json", schema_version=2)

    with pytest.raises(CatalogValidationError, match="Unsupported catalog schema_version"):
        load_product_catalog(path)


def test_rejects_missing_catalog_file(tmp_path):
    path = tmp_path / "missing-products.json"

    with pytest.raises(CatalogLoadError, match="Could not read product catalog"):
        load_product_catalog(path)


def test_default_catalog_is_loaded_once_per_process(tmp_path, monkeypatch):
    path = write_catalog(tmp_path / "products.json", [product_record()])
    catalog.get_product_catalog.cache_clear()
    monkeypatch.setattr(catalog, "DEFAULT_CATALOG_PATH", path)
    read_count = 0
    original_read_catalog = catalog._read_catalog

    def count_reads(catalog_path):
        nonlocal read_count
        read_count += 1
        return original_read_catalog(catalog_path)

    monkeypatch.setattr(catalog, "_read_catalog", count_reads)
    try:
        first = catalog.get_product_catalog()
        second = catalog.get_product_catalog()
    finally:
        catalog.get_product_catalog.cache_clear()

    assert first is second
    assert read_count == 1
