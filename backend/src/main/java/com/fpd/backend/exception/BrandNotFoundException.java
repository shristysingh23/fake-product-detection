package com.fpd.backend.exception;

public class BrandNotFoundException extends RuntimeException {
	public BrandNotFoundException(String message) {
		super(message);
	}
}
