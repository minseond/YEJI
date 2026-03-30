package com.yeji.domain.card.controller;

import com.yeji.domain.card.dto.CardCreateReadingRequest;
import com.yeji.domain.card.dto.CardResultDetailResponse;
import com.yeji.domain.card.dto.CardResultListItemResponse;
import com.yeji.domain.card.service.CardResultService;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@Tag(name = "Card API", description = "카드(타로/화투) 리딩 생성 및 결과 조회 API")
@RestController
@RequestMapping("/cards")
@RequiredArgsConstructor
public class CardController {

    private final CardResultService cardResultService;

    //카드 리딩 생성
    @PostMapping("/readings")
    @Operation(
        summary = "카드 리딩 생성",
        description = "카테고리에 따라(TARO=3장, HWATU=4장) 사용자가 선택한 카드로 리딩을 생성한다. CardCode=총 카드의 장 수 중에 선택한 카드의 코드, position=뽑은 카드의 순서, isReversed=뒤집었는지 여부"
    )
    public ResponseEntity<CardResultDetailResponse> createReading(
            @AuthenticationPrincipal AuthUser authUser,
            @Valid @RequestBody CardCreateReadingRequest request
            ) {
        return ResponseEntity.ok(
                cardResultService.createReading(authUser.getUserId(), request));
    }

    //카드 결과 상세 조회
    //resultId로 받아와서 그 결과 상세 조회 (카드를 뽑은 사용자만 접근할 수 있음)
    @GetMapping("/readings/{cardResultId}")
    @Operation(
            summary = "카드 결과 상세 조회",
            description = "특정 카드 리딩 결과의 상세 내용을 조회합니다."
    )
    public ResponseEntity<CardResultDetailResponse> getDetail(
            @AuthenticationPrincipal AuthUser authUser,
            @PathVariable Long cardResultId
    ) {
        return ResponseEntity.ok(
                cardResultService.getDetail(authUser.getUserId(), cardResultId));
    }

    //History (목록)
    @GetMapping("/history")
    @Operation(summary = "카드 히스토리 목록 조회", description = "히스토리 탭에 들어가면 현재까지 사용자가 선택한 카드들의 목록을 조회할 수 있다.")
    public ResponseEntity<List<CardResultListItemResponse>> getHistoryList(
            @AuthenticationPrincipal AuthUser authUser,
            @RequestParam(required = false) String category,
            @RequestParam(required = false)  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate from,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate to
    ) {
        return ResponseEntity.ok(cardResultService.getHistoryList(authUser.getUserId(), category, from, to));
    }

    //History (상세)
    @GetMapping("/history/{cardResultId}")
    @Operation(summary = "카드 히스토리 상세 조회", description = "히스토리 목록에서 원하는 결과를 선택하여 해당 결과를 상세 조회할 수 있다.")
    public ResponseEntity<CardResultDetailResponse> getHistoryDetail(
            @AuthenticationPrincipal AuthUser authUser,
            @PathVariable Long cardResultId
    ) {
        return ResponseEntity.ok(cardResultService.getHistoryDetail(authUser.getUserId(), cardResultId));
    }

}
