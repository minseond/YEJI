package com.yeji.domain.card.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

@Getter
@NoArgsConstructor
@Schema(description = "카드 리딩 생성 요청 DTO (프롬프트/질문 없이 topic만 받음)")
public class CardCreateReadingRequest {

    @NotBlank
    @Schema(description = "카드 종류", example = "TARO", allowableValues = {"TARO", "HWATU"})
    private String category;

    @NotBlank
    @Schema(
            description = "리딩 주제 코드(필수). 프롬프트/질문은 받지 않음",
            example = "LOVE",
            allowableValues = {"MONEY", "LOVE", "CAREER", "HEALTH", "STUDY"}
    )
    private String topic;

    @Valid
    @NotNull
    @Schema(description = "선택 카드 목록 (TARO=3장, HWATU=4장")
    private List<CardSelectedCardRequest> cards;
}
