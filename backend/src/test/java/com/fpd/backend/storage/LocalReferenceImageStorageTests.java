package com.fpd.backend.storage;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayInputStream;
import java.nio.file.Files;
import java.nio.file.Path;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import com.fpd.backend.config.ReferenceStorageProperties;
import com.fpd.backend.exception.StorageOperationException;

class LocalReferenceImageStorageTests {
	@TempDir
	Path tempDirectory;

	@Test
	void storesAndDeletesUnderConfiguredLocalDirectory() throws Exception {
		ReferenceStorageProperties properties = new ReferenceStorageProperties();
		properties.setLocalDirectory(tempDirectory.toString());
		LocalReferenceImageStorage storage = new LocalReferenceImageStorage(properties);
		byte[] bytes = {1, 2, 3};

		var saved = storage.store("references/3/file.png", "image/png",
				bytes.length, new ByteArrayInputStream(bytes));
		Path storedFile = tempDirectory.resolve("references/3/file.png");

		assertTrue(Files.exists(storedFile));
		assertEquals("references/3/file.png", saved.storageKey());
		assertNull(saved.imageUrl());
		assertTrue(storage.exists(saved.storageKey()));
		assertEquals(bytes.length, storage.read(saved.storageKey()).length);
		assertTrue(storage.lastModifiedNanos(saved.storageKey()) > 0);
		storage.delete(saved.storageKey());
		assertTrue(Files.notExists(storedFile));
		assertTrue(!storage.exists(saved.storageKey()));
	}

	@Test
	void rejectsStoragePathTraversal() {
		ReferenceStorageProperties properties = new ReferenceStorageProperties();
		properties.setLocalDirectory(tempDirectory.toString());
		LocalReferenceImageStorage storage = new LocalReferenceImageStorage(properties);

		assertThrows(StorageOperationException.class, () -> storage.store(
				"..\\outside.png", "image/png", 1, new ByteArrayInputStream(new byte[] {1})));
	}
}
