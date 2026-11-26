package com.fpd.backend.controller;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.Instant;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import com.fpd.backend.dto.response.ReferenceImageResponseDto;
import com.fpd.backend.dto.response.VisualReferenceImageDto;
import com.fpd.backend.entity.ProductReferenceImage.ImageType;
import com.fpd.backend.exception.GlobalExceptionHandler;
import com.fpd.backend.service.ReferenceImageService;

class ReferenceVisualControllerTests {

	private MockMvc mockMvc;
	private ReferenceImageService imageService;

	@BeforeEach
	void setUp() {
		imageService = mock(ReferenceImageService.class);
		mockMvc = MockMvcBuilders
				.standaloneSetup(new ReferenceImageController(imageService))
				.setControllerAdvice(new GlobalExceptionHandler())
				.build();
	}

	@Test
	void exposesReferenceInventoryThroughSpringApi() throws Exception {
		when(imageService.findVisualReferences()).thenReturn(List.of(
				new VisualReferenceImageDto(
						5L, 12L, "Acme", "Cereal", "corn flakes", "123", "FRONT",
						"image/png", 100, 1234L, true)));

		mockMvc.perform(get("/api/ml/reference-images"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$[0].referenceImageId").value(5))
				.andExpect(jsonPath("$[0].productId").value(12))
				.andExpect(jsonPath("$[0].available").value(true));
	}

	@Test
	void servesStoredReferenceImageBytesThroughSpringApi() throws Exception {
		when(imageService.findById(5L)).thenReturn(new ReferenceImageResponseDto(
				5L, 2L, null, "key", ImageType.FRONT, null,
				"front.png", "image/png", 3L, Instant.EPOCH));
		when(imageService.readContent(5L)).thenReturn(new byte[] {1, 2, 3});

		mockMvc.perform(get("/api/ml/reference-images/5/content"))
				.andExpect(status().isOk())
				.andExpect(content().contentType(MediaType.IMAGE_PNG))
				.andExpect(content().bytes(new byte[] {1, 2, 3}));
	}
}
