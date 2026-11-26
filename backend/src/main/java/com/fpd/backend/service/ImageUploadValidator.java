package com.fpd.backend.service;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.util.Locale;
import java.util.Set;

import javax.imageio.ImageIO;

import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import com.fpd.backend.exception.ImageValidationException;

@Component
public class ImageUploadValidator {

	public static final long MAX_FILE_SIZE = 10L * 1024 * 1024;
	private static final Set<String> SUPPORTED_TYPES =
			Set.of("image/jpeg", "image/png", "image/webp");

	public void validate(MultipartFile file) {
		validate(file, MAX_FILE_SIZE);
	}

	public void validate(MultipartFile file, long maxFileSize) {
		if (file == null || file.isEmpty()) {
			throw new ImageValidationException("The uploaded image is empty.");
		}
		if (file.getSize() > maxFileSize) {
			String message = maxFileSize == MAX_FILE_SIZE
					? "The uploaded image must not exceed 10 MB."
					: "The uploaded image exceeds the configured maximum file size.";
			throw new ImageValidationException(message);
		}

		String contentType = file.getContentType();
		if (contentType == null
				|| !SUPPORTED_TYPES.contains(contentType.toLowerCase(Locale.ROOT))) {
			throw new ImageValidationException(
					"Unsupported file type. Upload a JPEG, PNG or WebP image.");
		}

		try {
			byte[] bytes = file.getBytes();
			if (bytes.length == 0) {
				throw new ImageValidationException("The uploaded image is empty.");
			}
			if (bytes.length > MAX_FILE_SIZE) {
				throw new ImageValidationException(
						"The uploaded image must not exceed 10 MB.");
			}
			if (!matchesDeclaredFormat(bytes, contentType)) {
				throw new ImageValidationException(
						"The uploaded file content does not match the declared image type.");
			}

			BufferedImage image = ImageIO.read(new ByteArrayInputStream(bytes));
			if (image == null || image.getWidth() < 1 || image.getHeight() < 1) {
				throw new ImageValidationException(
						"The uploaded file does not contain a valid image.");
			}
		}
		catch (java.io.IOException | RuntimeException exception) {
			if (exception instanceof ImageValidationException validationException) {
				throw validationException;
			}
			throw new ImageValidationException(
					"The uploaded file does not contain a valid image.");
		}
	}

	private boolean matchesDeclaredFormat(byte[] bytes, String contentType) {
		String normalizedType = contentType.toLowerCase(Locale.ROOT);
		if ("image/jpeg".equals(normalizedType)) {
			return bytes.length >= 3
					&& (bytes[0] & 0xff) == 0xff
					&& (bytes[1] & 0xff) == 0xd8
					&& (bytes[2] & 0xff) == 0xff;
		}
		if ("image/png".equals(normalizedType)) {
			return bytes.length >= 8
					&& (bytes[0] & 0xff) == 0x89
					&& bytes[1] == 0x50
					&& bytes[2] == 0x4e
					&& bytes[3] == 0x47
					&& bytes[4] == 0x0d
					&& bytes[5] == 0x0a
					&& bytes[6] == 0x1a
					&& bytes[7] == 0x0a;
		}
		return bytes.length >= 12
				&& bytes[0] == 0x52
				&& bytes[1] == 0x49
				&& bytes[2] == 0x46
				&& bytes[3] == 0x46
				&& bytes[8] == 0x57
				&& bytes[9] == 0x45
				&& bytes[10] == 0x42
				&& bytes[11] == 0x50;
	}
}
