package com.fpd.backend;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class BackendApplicationTests {

	@LocalServerPort
	private int port;

	@Test
	void contextLoads() {
	}

	@Test
	void swaggerUiAndOpenApiDocumentsAreAvailable() throws Exception {
		HttpClient client = HttpClient.newHttpClient();
		HttpResponse<String> swagger = client.send(
				HttpRequest.newBuilder(URI.create(
						"http://localhost:" + port + "/swagger-ui/index.html")).GET().build(),
				HttpResponse.BodyHandlers.ofString());
		HttpResponse<String> apiDocs = client.send(
				HttpRequest.newBuilder(URI.create(
						"http://localhost:" + port + "/v3/api-docs")).GET().build(),
				HttpResponse.BodyHandlers.ofString());

		org.junit.jupiter.api.Assertions.assertEquals(200, swagger.statusCode());
		org.junit.jupiter.api.Assertions.assertEquals(200, apiDocs.statusCode());
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("/api/products"));
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("/api/products/{id}"));
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("/api/ml/analyze"));
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("/api/ml/health"));
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("/api/brands"));
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("/api/brands/{id}"));
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("/api/products/{productId}/versions"));
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("/api/versions/{versionId}"));
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("/api/images/{imageId}"));
		org.junit.jupiter.api.Assertions.assertTrue(
				apiDocs.body().contains("/api/versions/{versionId}/images"));
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("multipart/form-data"));
		org.junit.jupiter.api.Assertions.assertTrue(apiDocs.body().contains("Adidas"));
	}

}
