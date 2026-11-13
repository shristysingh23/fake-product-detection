package com.fpd.backend.exception;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.Set;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BeanPropertyBindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import com.fpd.backend.dto.response.ApiErrorResponse;

import jakarta.validation.ConstraintViolationException;

class GlobalExceptionHandlerTests {

	private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

	@Test
	void mapsMlErrorsToRequiredHttpStatuses() {
		assertStatus(HttpStatus.BAD_REQUEST, handler.handleMlBadRequest());
		assertStatus(HttpStatus.SERVICE_UNAVAILABLE, handler.handleMlUnavailable());
		assertStatus(HttpStatus.GATEWAY_TIMEOUT, handler.handleMlTimeout());
		assertStatus(HttpStatus.BAD_GATEWAY, handler.handleMlUpstreamError());
	}

	@Test
	void mapsProductNotFoundToNotFound() {
		String message = "Product with id 42 was not found.";
		ResponseEntity<ApiErrorResponse> response =
				handler.handleProductNotFound(new ProductNotFoundException(message));

		assertStatus(HttpStatus.NOT_FOUND, response);
		assertEquals(HttpStatus.NOT_FOUND.getReasonPhrase(), response.getBody().error());
		assertEquals(message, response.getBody().message());
	}

	@Test
	void mapsFieldValidationErrorsToBadRequest() {
		BeanPropertyBindingResult bindingResult = new BeanPropertyBindingResult(new Object(), "request");
		bindingResult.addError(new FieldError(
				"request", "brand", " ", false, null, null, "must not be blank"));

		ResponseEntity<ApiErrorResponse> response = handler.handleMethodArgumentNotValid(
				new MethodArgumentNotValidException(null, bindingResult));

		assertStatus(HttpStatus.BAD_REQUEST, response);
		assertEquals("brand must not be blank", response.getBody().message());
	}

	@Test
	void usesSafeFallbackWhenFieldValidationMessageIsUnavailable() {
		BeanPropertyBindingResult bindingResult = new BeanPropertyBindingResult(new Object(), "request");

		ResponseEntity<ApiErrorResponse> response = handler.handleMethodArgumentNotValid(
				new MethodArgumentNotValidException(null, bindingResult));

		assertStatus(HttpStatus.BAD_REQUEST, response);
		assertEquals("Request validation failed.", response.getBody().message());
	}

	@Test
	void mapsConstraintViolationsToBadRequest() {
		ResponseEntity<ApiErrorResponse> response = handler.handleConstraintViolation(
				new ConstraintViolationException("validation failed", Set.of()));

		assertStatus(HttpStatus.BAD_REQUEST, response);
		assertEquals("Request validation failed.", response.getBody().message());
	}

	@Test
	void mapsMalformedNumericQueryParameterToBadRequest() {
		MethodArgumentTypeMismatchException exception = new MethodArgumentTypeMismatchException(
				"abc", Integer.class, "page", null, new NumberFormatException("invalid integer"));

		ResponseEntity<ApiErrorResponse> response = handler.handleMethodArgumentTypeMismatch(exception);

		assertStatus(HttpStatus.BAD_REQUEST, response);
		assertEquals("Page must be a non-negative integer.", response.getBody().message());
	}

	@Test
	void mapsMissingImagePartToBadRequest() {
		ResponseEntity<ApiErrorResponse> response = handler.handleMissingPart();

		assertStatus(HttpStatus.BAD_REQUEST, response);
		assertEquals("The required image part is missing.", response.getBody().message());
	}

	private void assertStatus(HttpStatus expected, ResponseEntity<ApiErrorResponse> response) {
		assertEquals(expected, response.getStatusCode());
		assertEquals(expected.value(), response.getBody().status());
	}
}
