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
@Schema(description = "비밀번호 재설정 요청")
public class PasswordResetRequest {
    @Email
    @NotBlank
    @Schema(description = "이메일", example = "user@example.com")
    private String email;

    @NotBlank
    @Schema(description = "인증 코드 (이메일로 받은 코드)", example = "123456")
    private String code;

    @NotBlank
    @Schema(description = "새로운 비밀번호", example = "newPassword1234!")
    private String newPassword;
}