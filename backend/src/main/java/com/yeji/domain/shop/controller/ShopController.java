package com.yeji.domain.shop.controller;

import com.yeji.domain.shop.dto.*;
import com.yeji.domain.shop.service.ShopService;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.PostConstruct;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Shop API", description = "상점 상품 조회 및 결제")
@RestController
@RequestMapping("/shop")
@RequiredArgsConstructor
public class ShopController {

    private final ShopService shopService;

    // 편의상 앱 실행 시 상품 데이터가 없으면 넣음
    @PostConstruct
    public void init() {
        shopService.initProducts();
    }

    @Operation(summary = "상품 목록 조회 (SHOP-001)", description = "구매 가능한 토큰 상품 목록을 조회합니다.")
    @GetMapping("/products")
    public ResponseEntity<List<ProductResponse>> getProducts() {
        return ResponseEntity.ok(shopService.getProducts());
    }

    @Operation(summary = "결제 생성 (SHOP-002)", description = "상품 구매를 위한 주문 번호를 생성합니다. (PENDING 상태)")
    @PostMapping("/payments")
    public ResponseEntity<PaymentCreateResponse> createPayment(
            @AuthenticationPrincipal AuthUser authUser,
            @RequestBody @Valid PaymentCreateRequest request
    ) {
        return ResponseEntity.ok(shopService.createPayment(authUser.getUserId(), request));
    }

    @Operation(summary = "결제 검증 (SHOP-003)", description = "PG 결제 후 검증을 요청하여 포인트를 지급받습니다.")
    @PostMapping("/payments/{orderId}/verify")
    public ResponseEntity<Void> verifyPayment(
            @AuthenticationPrincipal AuthUser authUser,
            @PathVariable String orderId,
            @RequestBody @Valid PaymentVerifyRequest request
    ) {
        shopService.verifyPayment(authUser.getUserId(), orderId, request.getPaymentKey());
        return ResponseEntity.ok().build();
    }

    @Operation(summary = "결제 내역 조회 (SHOP-004)", description = "내 결제 내역을 조회합니다.")
    @GetMapping("/payments")
    public ResponseEntity<List<PaymentHistoryResponse>> getPaymentHistory(
            @AuthenticationPrincipal AuthUser authUser
    ) {
        return ResponseEntity.ok(shopService.getPaymentHistory(authUser.getUserId()));
    }
}