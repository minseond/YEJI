package com.yeji.domain.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Schema(description = "비밀번호 검증 요청")
public class PasswordCheckRequest {

    @Schema(description = "확인할 비밀번호")
    @NotBlank(message = "비밀번호를 입력해주세요.")
    private String password;
}