package com.yeji.domain.collection.dto;

import com.yeji.domain.collection.entity.Character;
import com.yeji.domain.collection.entity.CharacterGrade;
import com.yeji.domain.collection.entity.CharacterType;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@Schema(description = "캐릭터 정보 응답")
public class CharacterResponse {

    @Schema(description = "캐릭터 ID", example = "1")
    private Long id;

    @Schema(description = "캐릭터 이름", example = "산신령")
    private String name;

    @Schema(description = "캐릭터 타입 (EAST/WEST)", example = "EAST")
    private CharacterType type;

    @Schema(description = "캐릭터 등급", example = "RARE")
    private CharacterGrade grade;

    @Schema(description = "이미지 URL", example = "https://example.com/image.png")
    private String imageUrl;

    @Schema(description = "3D 모델 URL", example = "https://example.com/model.glb")
    private String modelUrl;

    @Schema(description = "설명", example = "동쪽 산을 지키는 신령님")
    private String description;

    public static CharacterResponse from(Character character) {
        return CharacterResponse.builder()
                .id(character.getId())
                .name(character.getName())
                .type(character.getType())
                .grade(character.getGrade())
                .imageUrl(character.getImageUrl())
                .modelUrl(character.getModelUrl())
                .description(character.getDescription())
                .build();
    }
}