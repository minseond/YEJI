package com.yeji.domain.wallet.dto;

import com.yeji.domain.wallet.entity.TokenHistory;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
public class TokenHistoryResponse {
    private final Long id;
    private final String type;        // CHARGE, USE
    private final Integer amount;     // 변동량
    private final String description; // 설명
    private final LocalDateTime createdAt;

    public TokenHistoryResponse(TokenHistory history) {
        this.id = history.getId();
        this.type = history.getType();
        this.amount = history.getAmount();
        this.description = history.getDescription();
        this.createdAt = history.getCreatedAt();
    }
}