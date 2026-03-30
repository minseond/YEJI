package com.yeji.domain.card.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@Schema(description = "카드 선택 요청 DTO")
//선택된 카드 1장에 대한 요청 정보
public class CardSelectedCardRequest {
    @NotNull
    @Schema(description = "카드 코드 (TARO: 0~77, HWATU: 0~47", example = "12")
    private Integer cardCode;

    @NotNull
    @Schema(description = "배치 순서(TARO=1~3, HWATU=1~4)", example = "1")
    private Integer position;

    @NotNull
    @Schema(description = "역방향 여부(타로만 사용). HWATU는 의미가 없으므로 무조건 false로 처리합니다.", example = "false")
    private Boolean isReversed;
}
