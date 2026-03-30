package com.yeji.domain.card.entity;

public enum CardStatus {
    KEEP,
    SOLD,
    SHARED;

    public static CardStatus from(String raw) {
        if (raw == null || raw.isBlank()) return KEEP;
        return CardStatus.valueOf(raw.trim().toUpperCase());
    }
}
