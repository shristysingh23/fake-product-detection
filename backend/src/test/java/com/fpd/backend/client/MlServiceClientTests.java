package com.fpd.backend.client;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withException;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import java.io.IOException;
import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import com.fpd.backend.dto.response.AnalyzeResponseDto;
import com.fpd.backend.dto.response.MlHealthResponseDto;
import com.fpd.backend.exception.MlBadRequestException;
import com.fpd.backend.exception.MlGatewayTimeoutException;
import com.fpd.backend.exception.MlServiceUnavailableException;
import com.fpd.backend.exception.MlUpstreamException;

class MlServiceClientTests {

	private static final String BASE_URL = "http://127.0.0.1:8000";

	private MockRestServiceServer server;
	private MlServiceClient client;

	@BeforeEach
	void setUp() {
		RestClient.Builder builder = RestClient.builder().baseUrl(BASE_URL);
		server = MockRestServiceServer.bindTo(builder).build();
		client = new MlServiceClient(builder.build());
	}

	@AfterEach
	void verifyRequests() {
		server.verify();
	}

	@Test
	void analyzeUploadsImageAndDeserializesResponse() {
		server.expect(requestTo(BASE_URL + "/analyze"))
				.andExpect(method(HttpMethod.POST))
				.andExpect(content().contentTypeCompatibleWith(MediaType.MULTIPART_FORM_DATA))
				.andExpect(content().string(org.hamcrest.Matchers.allOf(
						org.hamcrest.Matchers.containsString("name=\"image\""),
						org.hamcrest.Matchers.containsString("filename=\"original.png\""),
						org.hamcrest.Matchers.containsString("Content-Type: image/png"))))
				.andRespond(withSuccess(
						"{\"brand\":\"MAGGI\",\"product\":\"2-Minute Noodles\",\"status\":\"ANALYSIS_PENDING\"}",
						MediaType.APPLICATION_JSON));

		AnalyzeResponseDto response = client.analyze(
				"png-data".getBytes(StandardCharsets.UTF_8), "original.png", "image/png");

		assertEquals("MAGGI", response.brand());
		assertEquals("2-Minute Noodles", response.product());
		assertEquals("ANALYSIS_PENDING", response.status());
	}

	@Test
	void mapsUnsupportedImageResponseToBadRequest() {
		server.expect(requestTo(BASE_URL + "/analyze"))
				.andRespond(withStatus(HttpStatus.BAD_REQUEST));

		assertThrows(MlBadRequestException.class,
				() -> client.analyze(new byte[] { 1 }, "unsupported.txt", "text/plain"));
	}

	@Test
	void mapsMissingImageResponseToBadRequest() {
		server.expect(requestTo(BASE_URL + "/analyze"))
				.andRespond(withStatus(HttpStatus.UNPROCESSABLE_ENTITY));

		assertThrows(MlBadRequestException.class,
				() -> client.analyze(new byte[] { 1 }, "image.png", "image/png"));
	}

	@Test
	void mapsConnectionRefusedToServiceUnavailable() throws IOException {
		server.expect(requestTo(BASE_URL + "/analyze"))
				.andRespond(withException(new ConnectException("Connection refused")));

		assertThrows(MlServiceUnavailableException.class,
				() -> client.analyze(new byte[] { 1 }, "image.png", "image/png"));
	}

	@Test
	void mapsConnectionTimeoutToGatewayTimeout() throws IOException {
		server.expect(requestTo(BASE_URL + "/analyze"))
				.andRespond(withException(new SocketTimeoutException("Read timed out")));

		assertThrows(MlGatewayTimeoutException.class,
				() -> client.analyze(new byte[] { 1 }, "image.png", "image/png"));
	}

	@Test
	void mapsOtherMlErrorsToBadGateway() {
		server.expect(requestTo(BASE_URL + "/analyze"))
				.andRespond(withStatus(HttpStatus.INTERNAL_SERVER_ERROR));

		assertThrows(MlUpstreamException.class,
				() -> client.analyze(new byte[] { 1 }, "image.png", "image/png"));
	}

	@Test
	void mapsMalformedMlResponseToBadGateway() {
		server.expect(requestTo(BASE_URL + "/analyze"))
				.andRespond(withSuccess("{invalid-json", MediaType.APPLICATION_JSON));

		assertThrows(MlUpstreamException.class,
				() -> client.analyze(new byte[] { 1 }, "image.png", "image/png"));
	}

	@Test
	void healthReturnsSuccessfulMlHealthResponse() {
		server.expect(requestTo(BASE_URL + "/health"))
				.andExpect(method(HttpMethod.GET))
				.andRespond(withSuccess("{\"status\":\"ok\"}", MediaType.APPLICATION_JSON));

		MlHealthResponseDto response = client.health();

		assertEquals("ok", response.status());
	}

	@Test
	void healthFailureMapsToBadGateway() {
		server.expect(requestTo(BASE_URL + "/health"))
				.andRespond(withStatus(HttpStatus.INTERNAL_SERVER_ERROR));

		assertThrows(MlUpstreamException.class, client::health);
	}
}
