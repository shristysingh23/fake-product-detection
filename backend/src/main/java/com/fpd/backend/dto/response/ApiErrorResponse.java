package com.fpd.backend.dto.response;

import org.springframework.http.HttpStatus;

public record ApiErrorResponse(int status, String error, String message) {

	public static ApiErrorResponse from(HttpStatus status, String message) {
		return new ApiErrorResponse(status.value(), status.getReasonPhrase(), message);
	}
}
