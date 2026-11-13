package com.fpd.backend.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.multipart.support.MissingServletRequestPartException;
import org.springframework.web.bind.MethodArgumentNotValidException;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;

import com.fpd.backend.dto.response.ApiErrorResponse;

@RestControllerAdvice
public class GlobalExceptionHandler {

	@ExceptionHandler(ProductNotFoundException.class)
	public ResponseEntity<ApiErrorResponse> handleProductNotFound(ProductNotFoundException exception) {
		return error(HttpStatus.NOT_FOUND, exception.getMessage());
	}

	@ExceptionHandler(MethodArgumentNotValidException.class)
	public ResponseEntity<ApiErrorResponse> handleMethodArgumentNotValid(
			MethodArgumentNotValidException exception) {
		String message = exception.getBindingResult().getFieldErrors().stream()
				.filter(fieldError -> hasText(fieldError.getDefaultMessage()))
				.findFirst()
				.map(this::fieldValidationMessage)
				.orElse("Request validation failed.");

		return error(HttpStatus.BAD_REQUEST, message);
	}

	@ExceptionHandler(ConstraintViolationException.class)
	public ResponseEntity<ApiErrorResponse> handleConstraintViolation(
			ConstraintViolationException exception) {
		String message = exception.getConstraintViolations().stream()
				.map(ConstraintViolation::getMessage)
				.filter(this::hasText)
				.findFirst()
				.orElse("Request validation failed.");

		return error(HttpStatus.BAD_REQUEST, message);
	}

	@ExceptionHandler(MethodArgumentTypeMismatchException.class)
	public ResponseEntity<ApiErrorResponse> handleMethodArgumentTypeMismatch(
			MethodArgumentTypeMismatchException exception) {
		String message = switch (exception.getName()) {
			case "page" -> "Page must be a non-negative integer.";
			case "size" -> "Size must be an integer between 1 and 100.";
			default -> "Invalid value for request parameter '" + exception.getName() + "'.";
		};

		return error(HttpStatus.BAD_REQUEST, message);
	}

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
				.body(ApiErrorResponse.from(status, message));
	}

	private String fieldValidationMessage(FieldError fieldError) {
		return fieldError.getField() + " " + fieldError.getDefaultMessage();
	}

	private boolean hasText(String value) {
		return value != null && !value.isBlank();
	}
}
