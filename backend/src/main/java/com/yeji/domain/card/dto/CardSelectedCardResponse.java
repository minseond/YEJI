package com.yeji.domain.card.dto;

import com.yeji.domain.card.entity.CardSelection;
import lombok.Getter;

@Getter
public class CardSelectedCardResponse {

    private final Integer cardCode;
    private final Integer position;
    private final Boolean isReversed;

    public CardSelectedCardResponse(CardSelection selection) {
        this.cardCode = selection.getCardCode();
        this.position = selection.getPosition();
        this.isReversed = selection.getIsReversed();
    }
}
