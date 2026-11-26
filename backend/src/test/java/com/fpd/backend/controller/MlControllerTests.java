package com.fpd.backend.controller;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.Base64;
import javax.imageio.ImageIO;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import com.fpd.backend.client.MlServiceClient;
import com.fpd.backend.dto.response.AnalyzeResponseDto;
import com.fpd.backend.exception.GlobalExceptionHandler;
import com.fpd.backend.service.ImageUploadValidator;

class MlControllerTests {

	private MockMvc mockMvc;
	private MlServiceClient mlServiceClient;

	@BeforeEach
	void setUp() {
		mlServiceClient = mock(MlServiceClient.class);
		mockMvc = MockMvcBuilders
				.standaloneSetup(new MlController(mlServiceClient, new ImageUploadValidator()))
				.setControllerAdvice(new GlobalExceptionHandler())
				.build();
	}

	@Test
	void acceptsValidPngUpload() throws Exception {
		MockMultipartFile file = imageFile("image.png", "image/png", "png");
		when(mlServiceClient.analyze(eq(file.getBytes()), eq("image.png"), eq("image/png")))
				.thenReturn(new AnalyzeResponseDto("MAGGI", "2-Minute Noodles", "ANALYSIS_PENDING"));

		mockMvc.perform(multipart("/api/ml/analyze").file(file))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.brand").value("MAGGI"))
				.andExpect(jsonPath("$.status").value("ANALYSIS_PENDING"));
	}

	@Test
	void acceptsValidJpegUpload() throws Exception {
		MockMultipartFile file = imageFile("image.jpg", "image/jpeg", "jpg");
		when(mlServiceClient.analyze(eq(file.getBytes()), eq("image.jpg"), eq("image/jpeg")))
				.thenReturn(new AnalyzeResponseDto("MAGGI", "2-Minute Noodles", "ANALYSIS_PENDING"));

		mockMvc.perform(multipart("/api/ml/analyze").file(file))
				.andExpect(status().isOk());
	}

	@Test
	void acceptsValidWebpUpload() throws Exception {
		MockMultipartFile file = webpImageFile();
		when(mlServiceClient.analyze(eq(file.getBytes()), eq("image.webp"), eq("image/webp")))
				.thenReturn(new AnalyzeResponseDto("MAGGI", "2-Minute Noodles", "ANALYSIS_PENDING"));

		mockMvc.perform(multipart("/api/ml/analyze").file(file))
				.andExpect(status().isOk());
	}

	@Test
	void rejectsEmptyUpload() throws Exception {
		MockMultipartFile file = new MockMultipartFile(
				"image", "empty.png", "image/png", new byte[0]);

		mockMvc.perform(multipart("/api/ml/analyze").file(file))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.message").value("The uploaded image is empty."));

		verifyNoInteractions(mlServiceClient);
	}

	@Test
	void rejectsUnsupportedFileType() throws Exception {
		MockMultipartFile file = new MockMultipartFile(
				"image", "notes.txt", "text/plain", "hello".getBytes());

		mockMvc.perform(multipart("/api/ml/analyze").file(file))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.message")
						.value("Unsupported file type. Upload a JPEG, PNG or WebP image."));

		verifyNoInteractions(mlServiceClient);
	}

	@Test
	void rejectsInvalidImageBytes() throws Exception {
		MockMultipartFile file = new MockMultipartFile(
				"image", "image.png", "image/png", "not-an-image".getBytes());

		mockMvc.perform(multipart("/api/ml/analyze").file(file))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.message")
						.value("The uploaded file content does not match the declared image type."));

		verifyNoInteractions(mlServiceClient);
	}

	@Test
	void rejectsImageOverTenMegabytes() throws Exception {
		MockMultipartFile file = new MockMultipartFile(
				"image", "large.png", "image/png",
				new byte[(int) (ImageUploadValidator.MAX_FILE_SIZE + 1)]);

		mockMvc.perform(multipart("/api/ml/analyze").file(file))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.message")
						.value("The uploaded image must not exceed 10 MB."));

		verifyNoInteractions(mlServiceClient);
	}

	@Test
	void rejectsMissingImagePart() throws Exception {
		mockMvc.perform(multipart("/api/ml/analyze"))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.message").value("The required image part is missing."));

		verifyNoInteractions(mlServiceClient);
	}

	private MockMultipartFile imageFile(String name, String contentType, String format)
			throws Exception {
		ByteArrayOutputStream output = new ByteArrayOutputStream();
		BufferedImage image = new BufferedImage(2, 2, BufferedImage.TYPE_INT_RGB);
		ImageIO.write(image, format, output);
		return new MockMultipartFile("image", name, contentType, output.toByteArray());
	}

	private MockMultipartFile webpImageFile() throws Exception {
		byte[] webp = Base64.getDecoder().decode(
				"UklGRjwAAABXRUJQVlA4IDAAAADQAQCdASoCAAIAAUAmJaACdLoB+AADsAD+8ut//NgVzXPv9//S4P0uD9Lg/9KQAAA=");
		return new MockMultipartFile(
				"image", "image.webp", "image/webp", webp);
	}
}
