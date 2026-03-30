package com.yeji.domain.user.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.yeji.domain.collection.dto.CharacterResponse;
import com.yeji.domain.user.entity.User;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDate;
import java.time.LocalTime;

@Getter
@Builder
@Schema(description = "유저 정보 응답 DTO")
public class UserResponse {

    @Schema(description = "유저 ID", example = "1")
    private final Long id;

    @Schema(description = "이메일", example = "user@example.com")
    private final String email;

    @Schema(description = "닉네임", example = "행운의주인공")
    private final String nickname;

    @Schema(description = "프로필 이미지 URL", example = "https://k.kakaocdn.net/...")
    private final String profileImg;

    @Schema(description = "이름 (한글)", example = "홍길동")
    private final String nameKor;

    @Schema(description = "성별", example = "M")
    private final String gender;

    @Schema(description = "생년월일", example = "1995-05-05")
    private final LocalDate birthDate;

    @Schema(description = "태어난 시간", example = "14:30:00")
    private final LocalTime birthTime;

    @Schema(description = "양력 여부", example = "true")
    @JsonProperty("isSolar")
    private final boolean isSolar;

    @Schema(description = "동양 장착 캐릭터")
    private final CharacterResponse equipEast;

    @Schema(description = "서양 장착 캐릭터")
    private final CharacterResponse equipWest;


    public static UserResponse from(User user) {
        return UserResponse.builder()
                .id(user.getId())
                .email(user.getEmail())
                .nickname(user.getNickname())
                .profileImg(user.getProfileImg())
                .nameKor(user.getNameKor())
                .gender(user.getGender())
                .birthDate(user.getBirthDate())
                .birthTime(user.getBirthTime())
                .isSolar(user.isSolar())
                .equipEast(user.getEquipEast() != null ? CharacterResponse.from(user.getEquipEast()) : null)
                .equipWest(user.getEquipWest() != null ? CharacterResponse.from(user.getEquipWest()) : null)
                .build();
    }
}