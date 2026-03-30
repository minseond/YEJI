package com.yeji.domain.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
@Schema(description = "JWT 토큰 응답 DTO")
public class TokenResponse {
    @Schema(description = "액세스 토큰 (API 요청용)", example = "eyJhbGciOiJIUzI1NiJ9...")
    private String accessToken;

    @Schema(description = "리프레시 토큰 (토큰 재발급용)", example = "eyJhbGciOiJIUzI1NiJ9...")
    private String refreshToken;
}