package com.fpd.backend.client;

import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.net.http.HttpTimeoutException;
import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

import com.fpd.backend.dto.response.AnalyzeResponseDto;
import com.fpd.backend.dto.response.MlHealthResponseDto;
import com.fpd.backend.exception.MlBadRequestException;
import com.fpd.backend.exception.MlGatewayTimeoutException;
import com.fpd.backend.exception.MlServiceUnavailableException;
import com.fpd.backend.exception.MlUpstreamException;

@Component
public class MlServiceClient {

	private final RestClient restClient;

	public MlServiceClient(RestClient restClient) {
		this.restClient = restClient;
	}

	public AnalyzeResponseDto analyze(byte[] image, String filename, String contentType) {
		HttpHeaders partHeaders = new HttpHeaders();
		if (contentType != null && !contentType.isBlank()) {
			partHeaders.set(HttpHeaders.CONTENT_TYPE, contentType);
		}

		ByteArrayResource imageResource = new ByteArrayResource(image) {
			@Override
			public String getFilename() {
				return filename;
			}
		};

		MultiValueMap<String, Object> multipartBody = new LinkedMultiValueMap<>();
		multipartBody.add("image", new HttpEntity<>(imageResource, partHeaders));

		try {
			AnalyzeResponseDto response = restClient.post()
					.uri("/analyze")
					.contentType(MediaType.MULTIPART_FORM_DATA)
					.body(multipartBody)
					.retrieve()
					.body(AnalyzeResponseDto.class);
			if (response == null
					|| response.brand() == null
					|| response.product() == null
					|| response.status() == null) {
				throw new MlUpstreamException();
			}
			return response;
		}
		catch (RestClientResponseException exception) {
			throw mapHttpError(exception);
		}
		catch (ResourceAccessException exception) {
			throw mapConnectionError(exception);
		}
		catch (RestClientException exception) {
			throw new MlUpstreamException(exception);
		}
	}

	public MlHealthResponseDto health() {
		try {
			MlHealthResponseDto response = restClient.get()
					.uri("/health")
					.retrieve()
					.body(MlHealthResponseDto.class);
			if (response == null || !"ok".equals(response.status())) {
				throw new MlUpstreamException();
			}
			return response;
		}
		catch (RestClientResponseException exception) {
			throw mapHttpError(exception);
		}
		catch (ResourceAccessException exception) {
			throw mapConnectionError(exception);
		}
		catch (RestClientException exception) {
			throw new MlUpstreamException(exception);
		}
	}

	private RuntimeException mapHttpError(RestClientResponseException exception) {
		HttpStatusCode status = exception.getStatusCode();
		if (status.value() == 400 || status.value() == 422) {
			return new MlBadRequestException();
		}
		return new MlUpstreamException(exception);
	}

	private RuntimeException mapConnectionError(ResourceAccessException exception) {
		if (hasCause(exception, SocketTimeoutException.class)
				|| hasCause(exception, HttpTimeoutException.class)) {
			return new MlGatewayTimeoutException(exception);
		}
		if (hasCause(exception, ConnectException.class)) {
			return new MlServiceUnavailableException(exception);
		}
		return new MlUpstreamException(exception);
	}

	private boolean hasCause(Throwable exception, Class<? extends Throwable> causeType) {
		Map<Throwable, Boolean> visited = new LinkedHashMap<>();
		Throwable current = exception;
		while (current != null && !visited.containsKey(current)) {
			if (causeType.isInstance(current)) {
				return true;
			}
			visited.put(current, Boolean.TRUE);
			current = current.getCause();
		}
		return false;
	}
}
