package com.fpd.backend.dto.response;

public record ApiErrorResponse(int status, String error, String message) {
}
