"""Validated, cached access to the product reference catalog.

This module only loads reference records. It does not perform product matching.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from app.text_normalization import normalize_text


DEFAULT_CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "products.json"
SUPPORTED_SCHEMA_VERSION = 1
_ROOT_FIELDS = {"schema_version", "products"}
_PRODUCT_FIELDS = {
    "product_id",
    "brand",
    "product_name",
    "category",
    "brand_aliases",
    "product_aliases",
}


class CatalogError(ValueError):
    """Base exception for catalog read and validation failures."""


class CatalogLoadError(CatalogError):
    """Raised when the catalog file cannot be read or parsed as JSON."""


class CatalogValidationError(CatalogError):
    """Raised when catalog data does not satisfy the supported schema."""


@dataclass(frozen=True, slots=True)
class ProductRecord:
    """One validated product reference record."""

    product_id: str
    brand: str
    product_name: str
    category: str | None
    brand_aliases: tuple[str, ...]
    product_aliases: tuple[str, ...]


def _normalize_alias(value: str) -> str:
    """Normalize an alias for collision checks, without changing stored text."""
    return normalize_text(value)


def _required_text(value: Any, field: str, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CatalogValidationError(f"{location}.{field} must be a non-empty string.")
    return value.strip()


def _text_aliases(value: Any, field: str, location: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CatalogValidationError(f"{location}.{field} must be an array of strings.")

    aliases = []
    for index, alias in enumerate(value):
        item_location = f"{location}.{field}[{index}]"
        aliases.append(_required_text(alias, "value", item_location))
    return tuple(aliases)


def _check_normalizable(value: str, field: str, location: str) -> str:
    normalized = _normalize_alias(value)
    if not normalized:
        raise CatalogValidationError(
            f"{location}.{field} must contain at least one letter or digit."
        )
    return normalized


def _validate_catalog(data: Any, source: Path) -> tuple[ProductRecord, ...]:
    if not isinstance(data, dict):
        raise CatalogValidationError(f"Catalog root in {source} must be a JSON object.")
    if set(data) != _ROOT_FIELDS:
        missing = sorted(_ROOT_FIELDS - set(data))
        extra = sorted(set(data) - _ROOT_FIELDS)
        details = []
        if missing:
            details.append(f"missing fields: {', '.join(missing)}")
        if extra:
            details.append(f"unsupported fields: {', '.join(extra)}")
        raise CatalogValidationError(f"Invalid catalog root in {source} ({'; '.join(details)}).")

    schema_version = data["schema_version"]
    if type(schema_version) is not int or schema_version != SUPPORTED_SCHEMA_VERSION:
        raise CatalogValidationError(
            f"Unsupported catalog schema_version {schema_version!r} in {source}; "
            f"supported version is {SUPPORTED_SCHEMA_VERSION}."
        )

    products = data["products"]
    if not isinstance(products, list):
        raise CatalogValidationError(f"Catalog products in {source} must be an array.")

    records: list[ProductRecord] = []
    seen_product_ids: set[str] = set()
    brand_owners: dict[str, str] = {}
    product_alias_owners: dict[tuple[str, str], str] = {}

    for index, raw_record in enumerate(products):
        location = f"products[{index}]"
        if not isinstance(raw_record, dict):
            raise CatalogValidationError(f"{location} in {source} must be a JSON object.")

        if set(raw_record) != _PRODUCT_FIELDS:
            missing = sorted(_PRODUCT_FIELDS - set(raw_record))
            extra = sorted(set(raw_record) - _PRODUCT_FIELDS)
            details = []
            if missing:
                details.append(f"missing fields: {', '.join(missing)}")
            if extra:
                details.append(f"unsupported fields: {', '.join(extra)}")
            raise CatalogValidationError(
                f"Invalid {location} in {source} ({'; '.join(details)})."
            )

        product_id = _required_text(raw_record["product_id"], "product_id", location)
        if product_id in seen_product_ids:
            raise CatalogValidationError(f"Duplicate product_id {product_id!r} in {source}.")
        seen_product_ids.add(product_id)

        brand = _required_text(raw_record["brand"], "brand", location)
        product_name = _required_text(raw_record["product_name"], "product_name", location)
        category_value = raw_record["category"]
        if category_value is not None and not isinstance(category_value, str):
            raise CatalogValidationError(f"{location}.category must be a string or null.")
        category = category_value.strip() if isinstance(category_value, str) else None

        brand_aliases = _text_aliases(raw_record["brand_aliases"], "brand_aliases", location)
        product_aliases = _text_aliases(
            raw_record["product_aliases"], "product_aliases", location
        )

        normalized_brand = _check_normalizable(brand, "brand", location)
        for alias in (brand, *brand_aliases):
            normalized_alias = _check_normalizable(alias, "brand_aliases", location)
            existing_brand = brand_owners.get(normalized_alias)
            if existing_brand is not None and existing_brand != normalized_brand:
                raise CatalogValidationError(
                    f"Conflicting normalized brand alias {alias!r} in {source}: "
                    f"it maps to both {existing_brand!r} and {brand!r}."
                )
            brand_owners[normalized_alias] = normalized_brand

        for alias in (product_name, *product_aliases):
            normalized_alias = _check_normalizable(alias, "product_aliases", location)
            key = (normalized_brand, normalized_alias)
            existing_product_id = product_alias_owners.get(key)
            if existing_product_id is not None and existing_product_id != product_id:
                raise CatalogValidationError(
                    f"Conflicting normalized product alias {alias!r} in {source} "
                    f"for brand {brand!r}: it belongs to product IDs "
                    f"{existing_product_id!r} and {product_id!r}."
                )
            product_alias_owners[key] = product_id

        records.append(
            ProductRecord(
                product_id=product_id,
                brand=brand,
                product_name=product_name,
                category=category,
                brand_aliases=brand_aliases,
                product_aliases=product_aliases,
            )
        )

    return tuple(records)


def _read_catalog(path: Path) -> tuple[ProductRecord, ...]:
    try:
        catalog_text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise CatalogLoadError(f"Could not read product catalog {path}: {error}") from error
    except UnicodeError as error:
        raise CatalogLoadError(f"Product catalog {path} is not valid UTF-8: {error}") from error

    try:
        data = json.loads(catalog_text)
    except json.JSONDecodeError as error:
        raise CatalogLoadError(
            f"Product catalog {path} contains invalid JSON at line {error.lineno}, "
            f"column {error.colno}: {error.msg}."
        ) from error

    return _validate_catalog(data, path)


@lru_cache(maxsize=1)
def get_product_catalog() -> tuple[ProductRecord, ...]:
    """Return the default catalog, reading and validating it once per process.

    Restart the service after changing the catalog file. Loading failures are
    raised to the caller and must not be interpreted as a product no-match.
    """
    return _read_catalog(DEFAULT_CATALOG_PATH)


def load_product_catalog(path: str | Path | None = None) -> tuple[ProductRecord, ...]:
    """Load a catalog file, or return the cached default catalog when omitted."""
    if path is None:
        return get_product_catalog()
    return _read_catalog(Path(path))
