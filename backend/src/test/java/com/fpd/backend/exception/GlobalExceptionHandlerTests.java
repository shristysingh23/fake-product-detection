package com.fpd.backend.exception;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.fpd.backend.dto.response.ApiErrorResponse;

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
