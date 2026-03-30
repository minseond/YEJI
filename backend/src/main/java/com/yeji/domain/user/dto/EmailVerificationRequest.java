package com.yeji.domain.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@Schema(description = "이메일 인증번호 검증 요청")
public class EmailVerificationRequest {
    @Email
    @NotBlank
    @Schema(description = "이메일", example = "user@example.com")
    private String email;

    @NotBlank
    @Schema(description = "인증 코드", example = "123456")
    private String code;
}