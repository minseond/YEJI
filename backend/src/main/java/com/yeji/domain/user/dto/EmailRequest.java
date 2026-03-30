package com.yeji.domain.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Schema(description = "이메일 인증번호 발송 요청")
public class EmailRequest {
    @Email
    @NotBlank
    @Schema(description = "인증할 이메일", example = "user@example.com")
    private String email;
}