package com.yeji.domain.luck.controller;

import com.yeji.domain.luck.dto.LuckTransferRequest;
import com.yeji.domain.luck.dto.LuckTransferResponse;
import com.yeji.domain.luck.service.LuckService;
import com.yeji.global.dto.ApiResponse;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Luck", description = "운세/저주 전송 (소셜) API")
@RestController
@RequestMapping("/luck")
@RequiredArgsConstructor
public class LuckController {

    private final LuckService luckService;

    @Operation(summary = "운세/저주 메시지 전송 (LUCK-001)", description = "친구에게 축복(BLESS) 또는 저주(CURSE) 메시지를 전송합니다.")
    @PostMapping("/transfers")
    public ApiResponse<LuckTransferResponse> sendLuck(
            @Parameter(hidden = true) @AuthenticationPrincipal AuthUser authUser,
            @RequestBody LuckTransferRequest request) {
        return ApiResponse.success(luckService.sendLuck(authUser, request));
    }

    @Operation(summary = "수신함 조회 (LUCK-002)", description = "나에게 도착한 운세/저주 메시지 목록을 조회합니다.")
    @GetMapping("/inbox")
    public ApiResponse<List<LuckTransferResponse>> getInbox(
            @Parameter(hidden = true) @AuthenticationPrincipal AuthUser authUser) {
        return ApiResponse.success(luckService.getInbox(authUser));
    }

    @Operation(summary = "메시지 읽음 처리 (LUCK-003)", description = "특정 메시지를 읽음 상태로 변경합니다.")
    @PatchMapping("/transfers/{transferId}/read")
    public ApiResponse<Void> markAsRead(
            @Parameter(hidden = true) @AuthenticationPrincipal AuthUser authUser,
            @Parameter(description = "메시지 ID") @PathVariable Long transferId) {
        luckService.markAsRead(authUser, transferId);
        return ApiResponse.success(null);
    }
}