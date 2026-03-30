package com.yeji.domain.saju.controller;

import com.yeji.domain.saju.dto.response.SajuAnalyzeResponse;
import com.yeji.domain.saju.service.SajuResultService;
import com.yeji.global.dto.ApiResponse;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;


@Tag(name = "Saju API", description = "사주 분석/결과 조회 API")
@RestController
@RequestMapping("/saju")
@RequiredArgsConstructor
public class SajuController {

    private final SajuResultService sajuResultService;

    // 분석 요청
    @PostMapping("/analyze")
    @Operation(
            summary = "사주 분석 요청(요청 바디 없음)",
            description = """
                    로그인 사용자(User)의 기본 정보(이름/생년월일시/성별/음양력)를 기반으로 사주 분석을 수행합니다.
                    - 요청 바디 없음
                    - 유저당 1개의 결과 유지(재분석 시 UPDATE 덮어쓰기)
                    """
    )
    public ApiResponse<SajuAnalyzeResponse> analyze(
            @AuthenticationPrincipal AuthUser authUser
    ) {
        Long userId = authUser.getUserId();
        return ApiResponse.success(sajuResultService.analyzeAndSave(userId));
    }

    // 결과 조회
    @GetMapping("/result")
    @Operation(
            summary = "사주 현재 결과 조회",
            description = "로그인 유저의 사주 결과(유저당 1개 고정)를 조회합니다."
    )
    public ApiResponse<SajuAnalyzeResponse> getCurrentResult(
            @AuthenticationPrincipal AuthUser authUser
    ) {
        return ApiResponse.success(sajuResultService.getCurrentResult(authUser.getUserId()));
    }

    // 히스토리 조회
    @GetMapping("/history")
    @Operation(
            summary = "사주 히스토리 조회",
            description = "히스토리 페이지(사주/운세/카드)에서 사주 결과를 다시 보여주기 위한 API입니다."
    )
    public ApiResponse<SajuAnalyzeResponse> getHistory(
            @AuthenticationPrincipal AuthUser authUser
    ) {
        return ApiResponse.success(sajuResultService.getCurrentResult(authUser.getUserId()));
    }
}
