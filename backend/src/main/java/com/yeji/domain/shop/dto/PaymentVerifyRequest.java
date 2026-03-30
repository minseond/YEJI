package com.yeji.domain.shop.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class PaymentVerifyRequest {
    @NotBlank
    @Schema(description = "PG사 결제 고유 번호 (imp_uid 등)", example = "imp_1234567890")
    private String paymentKey; // 포트원의 imp_uid 혹은 토스의 paymentKey
}