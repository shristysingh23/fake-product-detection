package com.fpd.backend.service;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

import org.springframework.stereotype.Service;

import com.fpd.backend.dto.response.AnalyzeResponseDto;
import com.fpd.backend.dto.response.ProductCandidateDto;
import com.fpd.backend.entity.Product;
import com.fpd.backend.repository.ProductRepository;

@Service
public class ProductIdentificationService {

	private final ProductRepository productRepository;

	public ProductIdentificationService(ProductRepository productRepository) {
		this.productRepository = productRepository;
	}

	public AnalyzeResponseDto identify(AnalyzeResponseDto extraction) {
		List<ProductCandidateDto> candidates = new ArrayList<>();

		for (Product product : productRepository.findAll()) {
			String matchingBarcode = findMatchingBarcode(product, extraction);
			double score = scoreProduct(product, extraction);
			if (score >= 0.72) {
				candidates.add(new ProductCandidateDto(
						product.getId(),
						product.getBrand(),
						product.getProductName(),
						matchingBarcode,
						matchingEvidence(product, extraction, matchingBarcode),
						round(score),
						score >= 0.95 ? "IDENTIFIED" : "MULTIPLE_MATCHES"));
			}
		}

		candidates.sort(Comparator
				.comparingDouble(ProductCandidateDto::matchConfidence)
				.reversed()
				.thenComparing(ProductCandidateDto::productId));

		String status;
		if (candidates.isEmpty()) {
			status = "NOT_IDENTIFIED";
		} else if (candidates.size() == 1 && candidates.getFirst().matchConfidence() >= 0.95) {
			status = "IDENTIFIED";
		} else {
			status = "MULTIPLE_MATCHES";
		}

		ProductCandidateDto top = candidates.isEmpty() ? null : candidates.getFirst();
		return new AnalyzeResponseDto(
				top == null ? extraction.brand() : top.brand(),
				top == null ? extraction.product() : top.productName(),
				status,
				extraction.processingStatus(),
				extraction.extractedText(),
				extraction.barcodes(),
				extraction.qrCodes(),
				extraction.processingErrors(),
				candidates,
				extraction.preprocessing(),
				extraction.visualMatches() == null ? List.of() : extraction.visualMatches(),
				extraction.visualDetection());
	}

	private double scoreProduct(Product product, AnalyzeResponseDto extraction) {
		List<AnalyzeResponseDto.BarcodeDto> identifiers = new ArrayList<>();
		if (extraction.barcodes() != null) {
			identifiers.addAll(extraction.barcodes());
		}
		if (extraction.qrCodes() != null) {
			identifiers.addAll(extraction.qrCodes());
		}

		if (product.getBarcode() != null) {
			for (AnalyzeResponseDto.BarcodeDto identifier : identifiers) {
				if (normalize(identifier.value()).equals(normalize(product.getBarcode()))) {
					return 1.0;
				}
			}
		}

		double textScore = textMatchScore(product, extraction);
		double visualScore = visualMatchScore(product, extraction);
		return Math.max(textScore, visualScore);
	}

	private double textMatchScore(Product product, AnalyzeResponseDto extraction) {
		String brand = normalize(product.getBrand());
		String productName = normalize(product.getProductName());
		String extracted = extraction.extractedText() == null ? ""
				: extraction.extractedText().stream()
						.map(item -> normalize(item.text()))
						.reduce("", (left, right) -> left + " " + right);
		double score = 0.0;
		if (!brand.isBlank() && extracted.contains(brand)) {
			score += 0.35;
		}
		if (!productName.isBlank() && extracted.contains(productName)) {
			score += 0.55;
		}
		if (score >= 0.72) {
			return score;
		}

		if (!brand.isBlank()) {
			score = Math.max(score, similarity(extracted, brand) * 0.45);
		}
		if (!productName.isBlank()) {
			score = Math.max(score, similarity(extracted, productName) * 0.75);
		}
		return score;
	}

	private double visualMatchScore(Product product, AnalyzeResponseDto extraction) {
		if (product.getId() == null || extraction.visualMatches() == null) {
			return 0.0;
		}
		return extraction.visualMatches().stream()
				.filter(match -> product.getId().equals(match.productId()))
				.mapToDouble(match -> match.similarityScore())
				.max()
				.orElse(0.0);
	}

	private String matchingEvidence(
			Product product, AnalyzeResponseDto extraction, String matchingBarcode) {
		if (matchingBarcode != null) {
			return "Exact barcode match";
		}
		double textScore = textMatchScore(product, extraction);
		double visualScore = visualMatchScore(product, extraction);
		if (visualScore > 0.0 && visualScore >= textScore) {
			return "CLIP visual similarity";
		}
		return "Normalized brand/product text match";
	}

	private String findMatchingBarcode(Product product, AnalyzeResponseDto extraction) {
		if (product.getBarcode() == null) {
			return null;
		}
		List<AnalyzeResponseDto.BarcodeDto> identifiers = new ArrayList<>();
		if (extraction.barcodes() != null) {
			identifiers.addAll(extraction.barcodes());
		}
		if (extraction.qrCodes() != null) {
			identifiers.addAll(extraction.qrCodes());
		}
		for (AnalyzeResponseDto.BarcodeDto identifier : identifiers) {
			if (normalize(identifier.value()).equals(normalize(product.getBarcode()))) {
				return product.getBarcode();
			}
		}
		return null;
	}

	private double similarity(String left, String right) {
		if (left.isBlank() || right.isBlank()) {
			return 0.0;
		}
		int distance = levenshtein(normalize(left), normalize(right));
		int longest = Math.max(normalize(left).length(), normalize(right).length());
		return longest == 0 ? 0.0 : 1.0 - (double) distance / longest;
	}

	private int levenshtein(String left, String right) {
		int[] previous = new int[right.length() + 1];
		int[] current = new int[right.length() + 1];
		for (int i = 0; i <= right.length(); i++) {
			previous[i] = i;
		}
		for (int i = 1; i <= left.length(); i++) {
			current[0] = i;
			for (int j = 1; j <= right.length(); j++) {
				int cost = left.charAt(i - 1) == right.charAt(j - 1) ? 0 : 1;
				current[j] = Math.min(
						Math.min(previous[j] + 1, current[j - 1] + 1),
						previous[j - 1] + cost);
			}
			int[] swap = previous;
			previous = current;
			current = swap;
		}
		return previous[right.length()];
	}

	private String normalize(String value) {
		if (value == null) {
			return "";
		}
		return Normalizer.normalize(value, Normalizer.Form.NFKC)
				.toLowerCase(Locale.ROOT)
				.replaceAll("[^a-z0-9]+", " ")
				.trim();
	}

	private double round(double value) {
		return Math.round(value * 100.0) / 100.0;
	}
}
