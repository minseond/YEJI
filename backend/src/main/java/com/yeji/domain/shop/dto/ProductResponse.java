package com.yeji.domain.shop.dto;

import com.yeji.domain.shop.entity.Product;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;

@Getter
public class ProductResponse {
    @Schema(description = "상품 ID")
    private final Integer productId;
    @Schema(description = "상품명")
    private final String name;
    @Schema(description = "가격(KRW)")
    private final Integer priceKrw;
    @Schema(description = "충전되는 포인트(FP)")
    private final Integer fpAmount;

    public ProductResponse(Product product) {
        this.productId = product.getId();
        this.name = product.getName();
        this.priceKrw = product.getPriceKrw();
        this.fpAmount = product.getFpAmount();
    }
}