package com.fpd.backend.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.support.MissingServletRequestPartException;

import com.fpd.backend.dto.response.ApiErrorResponse;

@RestControllerAdvice
public class GlobalExceptionHandler {

	@ExceptionHandler(MlBadRequestException.class)
	public ResponseEntity<ApiErrorResponse> handleMlBadRequest() {
		return error(HttpStatus.BAD_REQUEST, "The ML service could not process the image.");
	}

	@ExceptionHandler(MissingServletRequestPartException.class)
	public ResponseEntity<ApiErrorResponse> handleMissingPart() {
		return error(HttpStatus.BAD_REQUEST, "The required image part is missing.");
	}

	@ExceptionHandler(MlServiceUnavailableException.class)
	public ResponseEntity<ApiErrorResponse> handleMlUnavailable() {
		return error(HttpStatus.SERVICE_UNAVAILABLE, "The ML service is unavailable.");
	}

	@ExceptionHandler(MlGatewayTimeoutException.class)
	public ResponseEntity<ApiErrorResponse> handleMlTimeout() {
		return error(HttpStatus.GATEWAY_TIMEOUT, "The ML service did not respond in time.");
	}

	@ExceptionHandler(MlUpstreamException.class)
	public ResponseEntity<ApiErrorResponse> handleMlUpstreamError() {
		return error(HttpStatus.BAD_GATEWAY, "The ML service returned an unexpected response.");
	}

	private ResponseEntity<ApiErrorResponse> error(HttpStatus status, String message) {
		return ResponseEntity.status(status)
				.body(new ApiErrorResponse(status.value(), status.getReasonPhrase(), message));
	}
}
