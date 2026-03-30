package com.yeji.domain.shop.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class PaymentCreateResponse {
    @Schema(description = "생성된 주문 번호 (PG사에 전달)", example = "ORDER-20240101-XXXX")
    private String orderId;
    @Schema(description = "결제해야 할 금액", example = "1000")
    private Integer amount;
    @Schema(description = "구매 상품명", example = "100 FP")
    private String orderName;
}