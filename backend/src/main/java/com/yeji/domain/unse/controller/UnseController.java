package com.yeji.domain.unse.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.yeji.domain.unse.dto.UnseResultDetailResponse;
import com.yeji.domain.unse.dto.UnseResultListItemResponse;
import com.yeji.domain.unse.service.UnseFlowService;
import com.yeji.domain.unse.service.UnseResultService;
import com.yeji.global.dto.ApiResponse;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Unse API", description = "운세 플로우(SSE) + 결과 조회 API")
@RestController
@RequestMapping("/unse")
@RequiredArgsConstructor
public class UnseController {

    private final UnseFlowService unseFlowService;
    private final UnseResultService unseResultService;

    /* ===================== 1. GREETING ===================== */

    /* ===================== 3. FINAL SUMMARY ===================== */

    @PostMapping("regist/{sessionId}")
    @Operation(summary = "운세 등록")
    public ResponseEntity<ApiResponse<Object>> getFinal(
            @AuthenticationPrincipal AuthUser authUser,
            @PathVariable String sessionId
    ) {
        return ResponseEntity.ok(
                ApiResponse.ok(
                        unseFlowService.getFinalSummaryBoth(sessionId, authUser.getUserId())
                )
        );
    }


    @GetMapping("/today/analysis/{sessionId}")
    @Operation(summary = "오늘의 운세 정적 분석 결과 조회 (동양/서양 개별 호출)")
    public ResponseEntity<ApiResponse<JsonNode>> getTodayAnalysis(
            @AuthenticationPrincipal AuthUser authUser,
            @PathVariable String sessionId,
            @RequestParam String type,
            @RequestParam(required = false) String category,
            @RequestParam(required = false, defaultValue = "false") boolean force
    ) {
        return ResponseEntity.ok(
                ApiResponse.ok(
                        unseFlowService.getTodayAnalysis(sessionId, authUser.getUserId(), type, category, force)
                )
        );
    }

    /* ===================== 4. HISTORY ===================== */

    @GetMapping("/history")
    public ResponseEntity<ApiResponse<List<UnseResultListItemResponse>>> history(
            @AuthenticationPrincipal AuthUser authUser
    ) {
        return ResponseEntity.ok(
                ApiResponse.ok(
                        unseResultService.getHistory(authUser.getUserId())
                )
        );
    }

    @GetMapping("/result/{resultId}")
    public ResponseEntity<ApiResponse<UnseResultDetailResponse>> detail(
            @AuthenticationPrincipal AuthUser authUser,
            @PathVariable Long resultId
    ) {
        return ResponseEntity.ok(
                ApiResponse.ok(
                        unseResultService.getDetail(authUser.getUserId(), resultId)
                )
        );
    }
}
