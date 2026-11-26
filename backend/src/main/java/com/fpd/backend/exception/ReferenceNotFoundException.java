package com.fpd.backend.exception;

public class ReferenceNotFoundException extends RuntimeException {
	public ReferenceNotFoundException(String message) {
		super(message);
	}
}
