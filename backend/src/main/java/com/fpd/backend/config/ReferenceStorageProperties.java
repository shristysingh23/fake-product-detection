package com.fpd.backend.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "reference-storage")
public class ReferenceStorageProperties {
	private String localDirectory = "storage/reference-images";
	private long maxFileSize = 10L * 1024 * 1024;

	public String getLocalDirectory() { return localDirectory; }
	public void setLocalDirectory(String localDirectory) { this.localDirectory = localDirectory; }
	public long getMaxFileSize() { return maxFileSize; }
	public void setMaxFileSize(long maxFileSize) { this.maxFileSize = maxFileSize; }
}
