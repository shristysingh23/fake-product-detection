package com.fpd.backend.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import com.fpd.backend.dto.response.AnalyzeResponseDto;
import com.fpd.backend.entity.Product;
import com.fpd.backend.repository.ProductRepository;

class ProductIdentificationServiceTests {

	@Test
	void exactBarcodeMatchIsIdentified() {
		ProductRepository repository = mock(ProductRepository.class);
		Product product = new Product("Maggi", "2-Minute Noodles", "Food", "8901234567890", "Maggi noodles");
		when(repository.findAll()).thenReturn(List.of(product));
		ProductIdentificationService service = new ProductIdentificationService(repository);

		AnalyzeResponseDto extraction = new AnalyzeResponseDto(
				null, null, "NOT_IDENTIFIED", "COMPLETED", List.of(),
				List.of(new AnalyzeResponseDto.BarcodeDto("EAN13", "8901234567890")),
				List.of(), List.of(), List.of(), null);

		AnalyzeResponseDto result = service.identify(extraction);

		assertEquals("IDENTIFIED", result.status());
		assertEquals(1, result.candidates().size());
		assertEquals("Exact barcode match", result.candidates().getFirst().matchingEvidence());
	}

	@Test
	void noReferenceMatchReturnsNotIdentified() {
		ProductRepository repository = mock(ProductRepository.class);
		Product product = new Product("Acme", "Cereal", "Food", null, null);
		when(repository.findAll()).thenReturn(List.of(product));
		ProductIdentificationService service = new ProductIdentificationService(repository);

		AnalyzeResponseDto extraction = new AnalyzeResponseDto(
				null, null, "NOT_IDENTIFIED", "COMPLETED",
				List.of(new AnalyzeResponseDto.TextRegionDto("unrelated text", 0.9)),
				List.of(), List.of(), List.of(), List.of(), null);

		assertEquals("NOT_IDENTIFIED", service.identify(extraction).status());
	}

	@Test
	void exactBarcodeCandidateRanksAboveConflictingVisualMatch() {
		ProductRepository repository = mock(ProductRepository.class);
		Product barcodeProduct = new Product("Brand A", "Item A", "Food", "111", null);
		Product visualProduct = new Product("Brand B", "Item B", "Food", null, null);
		ReflectionTestUtils.setField(barcodeProduct, "id", 1L);
		ReflectionTestUtils.setField(visualProduct, "id", 2L);
		when(repository.findAll()).thenReturn(List.of(barcodeProduct, visualProduct));
		ProductIdentificationService service = new ProductIdentificationService(repository);

		AnalyzeResponseDto extraction = new AnalyzeResponseDto(
				null, null, "NOT_IDENTIFIED", "COMPLETED", List.of(),
				List.of(new AnalyzeResponseDto.BarcodeDto("EAN13", "111")),
				List.of(), List.of(), List.of(), null,
				List.of(new com.fpd.backend.dto.response.VisualMatchDto(2L, 8L, 0.99)));

		AnalyzeResponseDto result = service.identify(extraction);

		assertEquals(1L, result.candidates().getFirst().productId());
		assertEquals("Exact barcode match", result.candidates().getFirst().matchingEvidence());
		assertEquals(0.99, result.visualMatches().getFirst().similarityScore());
	}

	@Test
	void visualMatchCanIdentifyCandidateWhenTextIsUnreadable() {
		ProductRepository repository = mock(ProductRepository.class);
		Product product = new Product("Brand", "Unknown", "Food", null, null);
		ReflectionTestUtils.setField(product, "id", 12L);
		when(repository.findAll()).thenReturn(List.of(product));
		ProductIdentificationService service = new ProductIdentificationService(repository);

		AnalyzeResponseDto extraction = new AnalyzeResponseDto(
				null, null, "NOT_IDENTIFIED", "COMPLETED", List.of(),
				List.of(), List.of(), List.of(), List.of(), null,
				List.of(new com.fpd.backend.dto.response.VisualMatchDto(12L, 5L, 0.96)));

		AnalyzeResponseDto result = service.identify(extraction);

		assertEquals("IDENTIFIED", result.status());
		assertEquals("CLIP visual similarity", result.candidates().getFirst().matchingEvidence());
	}

	@Test
	void visualDetectionEvidenceIsPreservedByProductIdentification() {
		ProductRepository repository = mock(ProductRepository.class);
		when(repository.findAll()).thenReturn(List.of());
		ProductIdentificationService service = new ProductIdentificationService(repository);
		Map<String, Object> visualDetection = Map.of(
				"outcome", "INCONCLUSIVE",
				"calibrationStatus", "NOT_CALIBRATED");

		AnalyzeResponseDto extraction = new AnalyzeResponseDto(
				null, null, "NOT_IDENTIFIED", "COMPLETED",
				List.of(), List.of(), List.of(), List.of(), List.of(),
				null, List.of(), visualDetection);

		assertEquals(visualDetection, service.identify(extraction).visualDetection());
	}
}
