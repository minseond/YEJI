package com.yeji.domain.collection.dto;

import com.yeji.domain.collection.entity.CharacterType;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@Schema(description = "캐릭터 장착 요청")
public class CharacterEquipRequest {

    @Schema(description = "장착할 슬롯 타입 (EAST/WEST)", example = "EAST")
    @NotNull(message = "장착할 타입(위치)은 필수입니다.")
    private CharacterType type;

    @Schema(description = "장착할 캐릭터 ID (null일 경우 해제)", example = "1")
    private Long characterId;
}