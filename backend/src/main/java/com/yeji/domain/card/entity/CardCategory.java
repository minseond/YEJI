package com.yeji.domain.card.entity;

public enum CardCategory {
    TARO,
    HWATU;

    //사용자의 입력이 taro면 -> taro 로직으로
    //hwatu면 hwatu 로직으로
    public static CardCategory from(String raw) {
        if (raw == null || raw.isBlank()) return TARO;
        return CardCategory.valueOf(raw.trim().toUpperCase());
    }
}
