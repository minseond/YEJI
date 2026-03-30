package com.yeji.domain.card.entity;

public enum CardTopic {
    MONEY,
    LOVE,
    CAREER,
    HEALTH,
    STUDY;

    public static CardTopic from(String v) {
        if (v == null || v.isBlank()) throw new IllegalArgumentException("topic은 필수입니다.");
        try {
            return CardTopic.valueOf(v.trim().toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException("지원하지 않는 topic 입니다: " + v);
        }
    }
}
