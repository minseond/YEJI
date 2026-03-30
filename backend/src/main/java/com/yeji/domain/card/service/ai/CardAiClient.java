package com.yeji.domain.card.service.ai;

import com.yeji.domain.card.entity.CardCategory;
import com.yeji.domain.card.entity.CardSelection;
import com.yeji.domain.user.entity.User;

import java.util.List;


public interface CardAiClient {
    /**
     * 타로 리딩 생성
     * - 명세 나오기 전까지는 Stub 구현체가 동작
     * - 명세 확정 후 Real 구현체로 교체 예정
     */

    // 카드 리딩 분석 시작
    CardAiResult reading(User user, CardCategory category, String question, List<CardSelection> selections);
}
