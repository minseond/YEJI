package com.yeji.domain.shop.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class PaymentCreateRequest {
    @NotNull
    @Schema(description = "구매할 상품 ID", example = "1")
    private Integer productId;
}