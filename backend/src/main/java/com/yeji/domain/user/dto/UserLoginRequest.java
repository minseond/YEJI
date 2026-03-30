package com.yeji.domain.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@Schema(description = "로그인 요청 DTO")
public class UserLoginRequest {
    @Schema(description = "이메일", example = "a@a.com")
    private String email;

    @Schema(description = "비밀번호", example = "123")
    private String password;
}