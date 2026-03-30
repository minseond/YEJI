package com.yeji.domain.compatibility.controller;

import com.yeji.domain.compatibility.dto.CompatibilityListItemResponse;
import com.yeji.domain.compatibility.dto.CompatibilityRequest;
import com.yeji.domain.compatibility.dto.CompatibilityResponse;
import com.yeji.domain.compatibility.service.CompatibilityService;
import com.yeji.global.dto.ApiResponse;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Compatibility", description = "궁합 분석 API")
@RestController
@RequestMapping("/compatibility")
@RequiredArgsConstructor
public class CompatibilityController {

    private final CompatibilityService compatibilityService;

    @Operation(summary = "궁합 분석 생성 (COMPAT-001)", description = "친구 또는 직접 입력한 대상과의 궁합을 분석합니다. 저장된 사주 결과가 있다면 AI 분석에 활용됩니다.")
    @PostMapping("/results")
    public ApiResponse<CompatibilityResponse> createResult(
            @Parameter(hidden = true) @AuthenticationPrincipal AuthUser authUser,
            @RequestBody CompatibilityRequest request) {
        return ApiResponse.success(compatibilityService.createCompatibility(authUser, request));
    }

    @Operation(summary = "궁합 결과 목록 조회 (COMPAT-002)", description = "내가 요청했던 궁합 분석 결과 목록을 조회합니다.")
    @GetMapping("/results")
    public ApiResponse<List<CompatibilityListItemResponse>> getResults(
            @Parameter(hidden = true) @AuthenticationPrincipal AuthUser authUser) {
        return ApiResponse.success(compatibilityService.getCompatibilityList(authUser));
    }

    @Operation(summary = "궁합 결과 상세 조회 (COMPAT-003)", description = "특정 궁합 분석 결과의 상세 내용을 조회합니다.")
    @GetMapping("/results/{resultId}")
    public ApiResponse<CompatibilityResponse> getResultDetail(
            @Parameter(hidden = true) @AuthenticationPrincipal AuthUser authUser,
            @Parameter(description = "궁합 결과 ID") @PathVariable Long resultId) {
        return ApiResponse.success(compatibilityService.getCompatibilityDetail(authUser, resultId));
    }
}