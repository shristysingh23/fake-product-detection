package com.fpd.backend.controller;

import java.io.IOException;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.fpd.backend.client.MlServiceClient;
import com.fpd.backend.dto.response.AnalyzeResponseDto;
import com.fpd.backend.dto.response.MlHealthResponseDto;

@RestController
@RequestMapping("/api/ml")
public class MlController {

	private final MlServiceClient mlServiceClient;

	public MlController(MlServiceClient mlServiceClient) {
		this.mlServiceClient = mlServiceClient;
	}

	@PostMapping(value = "/analyze", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
	public AnalyzeResponseDto analyze(@RequestPart("image") MultipartFile image) throws IOException {
		return mlServiceClient.analyze(image.getBytes(), image.getOriginalFilename(), image.getContentType());
	}

	@GetMapping("/health")
	public MlHealthResponseDto health() {
		return mlServiceClient.health();
	}
}
