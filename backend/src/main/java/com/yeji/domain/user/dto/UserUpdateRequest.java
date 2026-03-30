package com.yeji.domain.user.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalTime;

@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Schema(description = "유저 정보 수정 요청 DTO")
public class UserUpdateRequest {

    @Schema(description = "변경할 닉네임", example = "새로운 닉네임")
    private String nickname;

    @Schema(description = "변경할 프로필 이미지 URL", example = "https://new-image.url/...")
    private String profileImg;

    @Schema(description = "변경할 이름(한글)", example = "김철수")
    private String nameKor;

    @Schema(description = "변경할 이름(한자)", example = "金哲秀")
    private String nameChn;

    @Schema(description = "성별", example = "M")
    private String gender;

    @Schema(description = "생년월일", example = "1995-10-07")
    private LocalDate birthDate;

    @Schema(description = "태어난 시간", example = "14:30:00")
    private LocalTime birthTime;

    @Schema(description = "양력 여부 (true: 양력, false: 음력)", example = "true")
    @JsonProperty("isSolar")
    private Boolean isSolar;
}