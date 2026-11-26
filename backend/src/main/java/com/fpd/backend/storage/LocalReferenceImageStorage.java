package com.fpd.backend.storage;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.FileTime;

import org.springframework.stereotype.Component;

import com.fpd.backend.config.ReferenceStorageProperties;
import com.fpd.backend.exception.StorageOperationException;

@Component
public class LocalReferenceImageStorage implements ReferenceImageStorage {
	private final ReferenceStorageProperties properties;

	public LocalReferenceImageStorage(ReferenceStorageProperties properties) {
		this.properties = properties;
	}

	@Override
	public StoredImage store(String storageKey, String contentType, long contentLength, java.io.InputStream input) {
		try {
			Path root = Path.of(properties.getLocalDirectory()).toAbsolutePath().normalize();
			Path target = root.resolve(storageKey).normalize();
			if (!target.startsWith(root)) {
				throw new StorageOperationException("The storage key is invalid.");
			}
			Files.createDirectories(target.getParent());
			Files.copy(input, target, StandardCopyOption.REPLACE_EXISTING);
			return new StoredImage(storageKey, null);
		}
		catch (IOException exception) {
			throw new StorageOperationException("Reference image could not be stored.", exception);
		}
	}

	@Override
	public void delete(String storageKey) {
		try {
			Path root = Path.of(properties.getLocalDirectory()).toAbsolutePath().normalize();
			Path target = root.resolve(storageKey).normalize();
			if (target.startsWith(root)) {
				Files.deleteIfExists(target);
			}
		}
		catch (IOException exception) {
			throw new StorageOperationException("Reference image could not be deleted.", exception);
		}
	}

	@Override
	public byte[] read(String storageKey) {
		try {
			return Files.readAllBytes(resolve(storageKey));
		}
		catch (IOException exception) {
			throw new StorageOperationException("Reference image could not be read.", exception);
		}
	}

	@Override
	public boolean exists(String storageKey) {
		return Files.isRegularFile(resolve(storageKey));
	}

	@Override
	public long lastModifiedNanos(String storageKey) {
		try {
			FileTime modified = Files.getLastModifiedTime(resolve(storageKey));
			return modified.to(java.util.concurrent.TimeUnit.NANOSECONDS);
		}
		catch (IOException exception) {
			throw new StorageOperationException("Reference image metadata could not be read.", exception);
		}
	}

	private Path resolve(String storageKey) {
		Path root = Path.of(properties.getLocalDirectory()).toAbsolutePath().normalize();
		Path target = root.resolve(storageKey).normalize();
		if (!target.startsWith(root)) {
			throw new StorageOperationException("The storage key is invalid.");
		}
		return target;
	}
}
