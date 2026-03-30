package com.yeji.domain.card.entity;

import com.yeji.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Getter
@Table(name = "card_selections")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class CardSelection {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "card_result_id", nullable = false)
    private CardResult cardResult;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "card_code")
    private Integer cardCode;

    @Column(name = "position")
    private Integer position;

    @Column(name = "is_reversed", nullable = false)
    private Boolean isReversed;

    @PrePersist
    public void prePersist() {
        if (this.isReversed == null) this.isReversed = false;
    }

    @Builder
    public CardSelection(CardResult cardResult,
                         User user,
                         Integer cardCode,
                         Integer position,
                         Boolean isReversed) {
        this.cardResult = cardResult;
        this.user = user;
        this.cardCode = cardCode;
        this.position = position;
        this.isReversed = isReversed;
    }
}
