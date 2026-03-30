package com.yeji.domain.wallet.controller;

import com.yeji.domain.wallet.dto.TokenHistoryResponse;
import com.yeji.domain.wallet.dto.WalletResponse;
import com.yeji.domain.wallet.service.WalletService;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@Tag(name = "Wallet API", description = "토큰(FP) 지갑 및 내역 조회")
@RestController
@RequestMapping("/wallet")
@RequiredArgsConstructor
public class WalletController {

    private final WalletService walletService;

    @Operation(summary = "지갑 조회 (WALLET-001)", description = "내 보유 토큰 잔액을 조회합니다.")
    @GetMapping({"", "/"})
    public ResponseEntity<WalletResponse> getMyWallet(@AuthenticationPrincipal AuthUser authUser) {
        return ResponseEntity.ok(walletService.getMyWallet(authUser.getUserId()));
    }

    @Operation(summary = "토큰 내역 조회 (TOKEN-001)", description = "토큰 사용/충전 내역을 페이징 조회합니다.")
    @GetMapping("/history")
    public ResponseEntity<Page<TokenHistoryResponse>> getHistory(
            @AuthenticationPrincipal AuthUser authUser,
            @PageableDefault(size = 20) Pageable pageable
    ) {
        return ResponseEntity.ok(walletService.getTokenHistory(authUser.getUserId(), pageable));
    }

    // 개발/테스트용 API (실제 서비스 시에는 ADMIN 권한 필요하거나 제거)
    @Operation(summary = "[TEST] 토큰 강제 충전", description = "개발 테스트용 API입니다.")
    @PostMapping("/charge/test")
    public ResponseEntity<Void> chargeTest(
            @AuthenticationPrincipal AuthUser authUser,
            @RequestParam int amount
    ) {
        walletService.chargePoint(authUser.getUserId(), amount, "테스트 무료 충전");
        return ResponseEntity.ok().build();
    }
}