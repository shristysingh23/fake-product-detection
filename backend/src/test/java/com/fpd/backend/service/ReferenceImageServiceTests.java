package com.fpd.backend.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.times;

import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.Base64;
import java.util.List;
import java.util.Optional;

import javax.imageio.ImageIO;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;

import com.fpd.backend.config.ReferenceStorageProperties;
import com.fpd.backend.entity.Product;
import com.fpd.backend.entity.ProductReferenceImage;
import com.fpd.backend.entity.ProductVersion;
import com.fpd.backend.exception.ImageValidationException;
import com.fpd.backend.exception.ReferenceNotFoundException;
import com.fpd.backend.repository.ProductReferenceImageRepository;
import com.fpd.backend.repository.ProductVersionRepository;
import com.fpd.backend.storage.ReferenceImageStorage;

class ReferenceImageServiceTests {
	private ProductVersionRepository versionRepository;
	private ProductReferenceImageRepository imageRepository;
	private ReferenceImageStorage storage;
	private ReferenceImageService service;
	private ProductVersion version;

	@BeforeEach
	void setUp() {
		versionRepository = org.mockito.Mockito.mock(ProductVersionRepository.class);
		imageRepository = org.mockito.Mockito.mock(ProductReferenceImageRepository.class);
		storage = org.mockito.Mockito.mock(ReferenceImageStorage.class);
		ReferenceStorageProperties properties = new ReferenceStorageProperties();
		service = new ReferenceImageService(versionRepository, imageRepository,
				storage, properties, new ImageUploadValidator());
		Product product = new Product("Adidas", "Ultraboost", "Shoes", null, null);
		ReflectionTestUtils.setField(product, "id", 2L);
		version = new ProductVersion(product, "2025", "v2", null, null, null, true);
		ReflectionTestUtils.setField(version, "id", 5L);
		when(versionRepository.findById(5L)).thenReturn(Optional.of(version));
	}

	@Test
	void uploadsJpegPngAndWebpReferenceImages() throws Exception {
		for (MockMultipartFile image : List.of(
				image("front.jpg", "image/jpeg", "jpg"),
				image("back.png", "image/png", "png"),
				webpImage())) {
			when(storage.store(any(), eq(image.getContentType()), eq(image.getSize()), any()))
					.thenAnswer(invocation -> new ReferenceImageStorage.StoredImage(
							invocation.getArgument(0), "/storage/" + invocation.getArgument(0)));
			when(imageRepository.save(any(ProductReferenceImage.class)))
					.thenAnswer(invocation -> {
						ProductReferenceImage saved = invocation.getArgument(0);
						ReflectionTestUtils.setField(saved, "id", 10L);
						return saved;
					});

			var result = service.upload(5L, image, ProductReferenceImage.ImageType.FRONT, "front");
			assertEquals(5L, result.productVersionId());
			assertEquals(image.getContentType(), result.contentType());
		}
		verify(imageRepository, times(3)).save(any(ProductReferenceImage.class));
	}

	@Test
	void rejectsEmptyUnsupportedInvalidAndOversizedUploads() throws Exception {
		assertThrows(ImageValidationException.class,
				() -> service.upload(5L, new MockMultipartFile(
						"image", "empty.png", "image/png", new byte[0]),
						ProductReferenceImage.ImageType.FRONT, null));
		assertThrows(ImageValidationException.class,
				() -> service.upload(5L, new MockMultipartFile(
						"image", "doc.pdf", "application/pdf", new byte[] {1}),
						ProductReferenceImage.ImageType.LABEL, null));
		assertThrows(ImageValidationException.class,
				() -> service.upload(5L, new MockMultipartFile(
						"image", "bad.png", "image/png", "not image".getBytes()),
						ProductReferenceImage.ImageType.FRONT, null));
		assertThrows(ImageValidationException.class,
				() -> service.upload(5L, new MockMultipartFile(
						"image", "large.png", "image/png",
						new byte[(int) (10L * 1024 * 1024 + 1)]),
						ProductReferenceImage.ImageType.FRONT, null));
		verify(imageRepository, never()).save(any(ProductReferenceImage.class));
	}

	@Test
	void handlesMissingVersionAndReturnsImageMetadata() throws Exception {
		when(versionRepository.findById(404L)).thenReturn(Optional.empty());
		assertThrows(ReferenceNotFoundException.class, () -> service.upload(404L,
				image("front.png", "image/png", "png"),
				ProductReferenceImage.ImageType.FRONT, null));

		ProductReferenceImage image = new ProductReferenceImage(version, "key",
				"/storage/key", ProductReferenceImage.ImageType.FRONT,
				"front", "front.png", "image/png", 100);
		ReflectionTestUtils.setField(image, "id", 22L);
		when(imageRepository.findById(22L)).thenReturn(Optional.of(image));
		when(imageRepository.findByProductVersionIdOrderByIdAsc(5L)).thenReturn(List.of(image));

		assertEquals(22L, service.findById(22L).id());
		assertEquals(1, service.findByVersion(5L).size());
	}

	@Test
	void listsVisualReferenceMetadataAndReadsStoredBytes() {
		ProductReferenceImage image = new ProductReferenceImage(version, "key",
				null, ProductReferenceImage.ImageType.FRONT,
				"front", "front.png", "image/png", 100);
		ReflectionTestUtils.setField(image, "id", 22L);
		when(imageRepository.findAll()).thenReturn(List.of(image));
		when(storage.exists("key")).thenReturn(true);
		when(storage.lastModifiedNanos("key")).thenReturn(123L);
		when(imageRepository.findById(22L)).thenReturn(Optional.of(image));
		when(storage.read("key")).thenReturn(new byte[] {1, 2, 3});

		var reference = service.findVisualReferences().getFirst();

		assertEquals(22L, reference.referenceImageId());
		assertEquals(2L, reference.productId());
		assertEquals("Adidas", reference.brand());
		assertEquals("Ultraboost", reference.productName());
		assertEquals("FRONT", reference.imageType());
		assertEquals(123L, reference.lastModifiedNanos());
		assertEquals(true, reference.available());
		assertEquals(3, service.readContent(22L).length);
	}

	@Test
	void replacesReferenceImageBytesWithoutChangingItsIdentity() throws Exception {
		ProductReferenceImage existing = new ProductReferenceImage(version, "key",
				null, ProductReferenceImage.ImageType.FRONT,
				"front", "front.png", "image/png", 100);
		ReflectionTestUtils.setField(existing, "id", 22L);
		MockMultipartFile replacement = image("replacement.jpg", "image/jpeg", "jpg");
		when(imageRepository.findById(22L)).thenReturn(Optional.of(existing));
		when(imageRepository.save(any(ProductReferenceImage.class)))
				.thenAnswer(invocation -> invocation.getArgument(0));

		var updated = service.updateContent(22L, replacement);

		assertEquals(22L, updated.id());
		assertEquals("image/jpeg", updated.contentType());
		assertEquals(replacement.getSize(), updated.fileSize());
		assertEquals("replacement.jpg", updated.originalFilename());
		verify(storage).store(eq("key"), eq("image/jpeg"), eq(replacement.getSize()), any());
	}

	@Test
	void deletesStorageBeforeDeletingMetadata() {
		ProductReferenceImage image = new ProductReferenceImage(version, "key",
				null, ProductReferenceImage.ImageType.FRONT,
				"front", "front.png", "image/png", 100);
		when(imageRepository.findById(22L)).thenReturn(Optional.of(image));

		service.delete(22L);

		verify(storage).delete("key");
		verify(imageRepository).delete(image);
	}

	private MockMultipartFile image(String name, String contentType, String format)
			throws Exception {
		ByteArrayOutputStream output = new ByteArrayOutputStream();
		ImageIO.write(new BufferedImage(2, 2, BufferedImage.TYPE_INT_RGB), format, output);
		return new MockMultipartFile("image", name, contentType, output.toByteArray());
	}

	private MockMultipartFile webpImage() {
		byte[] data = Base64.getDecoder().decode(
				"UklGRjwAAABXRUJQVlA4IDAAAADQAQCdASoCAAIAAUAmJaACdLoB+AADsAD+8ut//NgVzXPv9//S4P0uD9Lg/9KQAAA=");
		return new MockMultipartFile("image", "logo.webp", "image/webp", data);
	}
}
