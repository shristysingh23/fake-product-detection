package com.fpd.backend.storage;

import java.io.InputStream;

public interface ReferenceImageStorage {
	StoredImage store(String storageKey, String contentType, long contentLength, InputStream input);
	void delete(String storageKey);
	byte[] read(String storageKey);
	boolean exists(String storageKey);
	long lastModifiedNanos(String storageKey);

	record StoredImage(String storageKey, String imageUrl) {
	}
}
