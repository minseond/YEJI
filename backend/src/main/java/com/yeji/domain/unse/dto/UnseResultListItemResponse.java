package com.yeji.domain.unse.dto;

import com.yeji.domain.unse.entity.UnsePair;

import java.time.LocalDateTime;

public record UnseResultListItemResponse(
        Long id,
        String category,
        LocalDateTime created_at
) {
    public static UnseResultListItemResponse from(UnsePair r) {
        return new UnseResultListItemResponse(
                r.getId(),
                r.getCategory(),
                r.getCreatedAt()
        );
    }
}
