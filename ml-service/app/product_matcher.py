"""Deterministic OCR text matching against the validated product catalog.

Scores are ranking aids, not probabilities or authenticity assessments. The
default thresholds are provisional starting points and require evaluation on
representative, verified product data before production use.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
import math
from numbers import Real
from typing import Any, Iterable, Mapping

from app.catalog import ProductRecord, get_product_catalog
from app.text_normalization import normalize_text


class MatchOutcome(str, Enum):
    IDENTIFIED = "IDENTIFIED"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_FOUND = "NOT_FOUND"


@dataclass(frozen=True, slots=True)
class MatcherConfig:
    """Weights and provisional thresholds for product matching."""

    brand_weight: float = 0.40
    product_weight: float = 0.60
    minimum_review_score: float = 0.70
    minimum_brand_score: float = 0.80
    minimum_product_score: float = 0.72
    minimum_identification_score: float = 0.82
    minimum_winning_margin: float = 0.06
    fuzzy_token_similarity: float = 0.82


DEFAULT_CONFIG = MatcherConfig()

# These tokens contribute little evidence by themselves. The set is deliberately
# small and conservative; catalog-specific generic terms can be added after
# evaluation, but no catalog records are modified here.
_GENERIC_PRODUCT_TOKENS = frozenset(
    "and for with the of original classic premium quality product products "
    "pack family value new best good size flavor flavour edition".split()
)


@dataclass(frozen=True, slots=True)
class CandidateScore:
    product_id: str
    brand: str
    product_name: str
    category: str | None
    brand_score: float
    product_score: float
    combined_score: float


@dataclass(frozen=True, slots=True)
class MatchResult:
    outcome: MatchOutcome
    brand: str
    product: str
    category: str | None
    product_id: str | None
    brand_score: float
    product_score: float
    combined_score: float
    candidates: tuple[CandidateScore, ...]


@dataclass(frozen=True, slots=True)
class _OcrText:
    original: str
    normalized: str
    confidence: float | None


def _read_ocr_lines(lines: Any) -> tuple[_OcrText, ...]:
    """Extract text/confidence from OcrResult.lines or iterable line records.

    Invalid line objects and non-string/empty text are ignored. Confidence is
    accepted only when it is a finite real number in [0, 1]; otherwise it is
    omitted and has a neutral value during scoring.
    """
    if hasattr(lines, "lines"):
        lines = lines.lines
    if lines is None or isinstance(lines, (str, bytes, Mapping)):
        return ()
    try:
        iterator = iter(lines)
    except TypeError:
        return ()

    result: list[_OcrText] = []
    for line in iterator:
        if isinstance(line, Mapping):
            text = line.get("text")
            confidence = line.get("confidence")
        else:
            text = getattr(line, "text", None)
            confidence = getattr(line, "confidence", None)
        if not isinstance(text, str):
            continue
        normalized = normalize_text(text)
        if not normalized:
            continue
        valid_confidence = None
        if isinstance(confidence, Real) and not isinstance(confidence, bool):
            value = float(confidence)
            if math.isfinite(value) and 0.0 <= value <= 1.0:
                valid_confidence = value
        result.append(_OcrText(text, normalized, valid_confidence))
    return tuple(result)


def _token_similarity(left: str, right: str, threshold: float) -> float:
    if left == right:
        return 1.0
    if min(len(left), len(right)) < 4:
        return 0.0
    ratio = SequenceMatcher(None, left, right, autojunk=False).ratio()
    return ratio if ratio >= threshold else 0.0


def _alias_score(alias: str, text_tokens: tuple[str, ...], config: MatcherConfig,
                 *, product: bool) -> tuple[float, frozenset[str]]:
    alias_tokens = tuple(normalize_text(alias).split())
    if not alias_tokens or not text_tokens:
        return 0.0, frozenset()

    # Product evidence must include a distinctive token. Generic packaging or
    # marketing words alone cannot identify a product.
    distinctive = tuple(
        token for token in alias_tokens if token not in _GENERIC_PRODUCT_TOKENS
    ) if product else alias_tokens
    if product and not distinctive:
        return 0.0, frozenset()

    weights = [0.12 if product and token in _GENERIC_PRODUCT_TOKENS else 1.0
               for token in alias_tokens]
    total_weight = sum(weights)
    matched_weight = 0.0
    matched_tokens: set[str] = set()
    for alias_token, weight in zip(alias_tokens, weights):
        best = max(
            (_token_similarity(alias_token, observed, config.fuzzy_token_similarity)
             for observed in text_tokens),
            default=0.0,
        )
        if best:
            matched_weight += weight * best
            matched_tokens.add(alias_token)

    if product and not any(token in matched_tokens for token in distinctive):
        return 0.0, frozenset()
    score = matched_weight / total_weight

    # A complete adjacent phrase is the strongest lexical evidence. The token
    # coverage calculation still allows lines to be split or reordered.
    width = len(alias_tokens)
    for start in range(max(0, len(text_tokens) - width + 1)):
        phrase = text_tokens[start:start + width]
        if phrase == alias_tokens:
            score = 1.0
            break
    return score, frozenset(matched_tokens)


def _confidence_factor(lines: tuple[_OcrText, ...]) -> float:
    valid = [line.confidence for line in lines if line.confidence is not None]
    # Missing/invalid confidence is neutral. Valid confidence can move lexical
    # evidence by at most five percent in either direction around neutral.
    confidence = sum(valid) / len(valid) if valid else 0.5
    return 0.95 + 0.10 * confidence


def _best_alias_score(aliases: Iterable[str], tokens: tuple[str, ...],
                      config: MatcherConfig, *, product: bool) -> float:
    return max(
        (_alias_score(alias, tokens, config, product=product)[0] for alias in aliases),
        default=0.0,
    )


def identify_product(
    ocr_lines: Any,
    catalog: Iterable[ProductRecord] | None = None,
    *,
    config: MatcherConfig = DEFAULT_CONFIG,
) -> MatchResult:
    """Rank OCR evidence against catalog records and return a three-way result.

    When ``catalog`` is omitted, the validated process-cached catalog loader is
    used. Catalog loading/validation exceptions deliberately propagate.
    """
    lines = _read_ocr_lines(ocr_lines)
    records = tuple(get_product_catalog() if catalog is None else catalog)
    if any(not isinstance(record, ProductRecord) for record in records):
        raise TypeError("catalog must contain validated ProductRecord instances.")

    tokens = tuple(token for line in lines for token in line.normalized.split())
    if not tokens:
        return MatchResult(MatchOutcome.NOT_FOUND, "", "", None, None, 0, 0, 0, ())

    confidence_factor = _confidence_factor(lines)
    scored: list[CandidateScore] = []
    brand_scores: dict[str, float] = {}
    for record in records:
        brand_aliases = (record.brand, *record.brand_aliases)
        product_aliases = (record.product_name, *record.product_aliases)
        brand_score = _best_alias_score(brand_aliases, tokens, config, product=False)
        product_score = _best_alias_score(product_aliases, tokens, config, product=True)
        brand_score = min(1.0, brand_score * confidence_factor)
        product_score = min(1.0, product_score * confidence_factor)
        brand_scores[record.brand] = max(brand_scores.get(record.brand, 0.0), brand_score)
        combined = config.brand_weight * brand_score + config.product_weight * product_score
        scored.append(CandidateScore(
            record.product_id, record.brand, record.product_name, record.category,
            brand_score, product_score, combined,
        ))

    scored.sort(key=lambda candidate: (-candidate.combined_score, candidate.product_id))
    plausible = tuple(c for c in scored if c.combined_score >= config.minimum_review_score)
    if not plausible:
        supported_brands = [name for name, score in brand_scores.items()
                            if score >= config.minimum_brand_score]
        unique_brand = supported_brands[0] if len(supported_brands) == 1 else ""
        return MatchResult(MatchOutcome.NOT_FOUND, unique_brand, "", None, None,
                           brand_scores.get(unique_brand, 0.0), 0.0, 0.0, ())

    winner = plausible[0]
    second_score = plausible[1].combined_score if len(plausible) > 1 else 0.0
    margin = winner.combined_score - second_score
    meets_component_thresholds = (
        winner.brand_score >= config.minimum_brand_score
        and winner.product_score >= config.minimum_product_score
        and winner.combined_score >= config.minimum_identification_score
    )
    if meets_component_thresholds and margin >= config.minimum_winning_margin:
        return MatchResult(
            MatchOutcome.IDENTIFIED, winner.brand, winner.product_name,
            winner.category, winner.product_id, winner.brand_score,
            winner.product_score, winner.combined_score, plausible,
        )

    plausible_brands = {candidate.brand for candidate in plausible}
    shared_brand = next(iter(plausible_brands)) if len(plausible_brands) == 1 else ""
    return MatchResult(
        MatchOutcome.AMBIGUOUS, shared_brand, "", None, None,
        winner.brand_score if shared_brand else 0.0, winner.product_score,
        winner.combined_score, plausible,
    )
