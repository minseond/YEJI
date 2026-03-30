package com.yeji.domain.event.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Table(name = "events")
public class Event {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "event_id")
    private Long id;

    @Column(nullable = false)
    private String title;

    @Column(nullable = false)
    @Enumerated(EnumType.STRING)
    private EventType type; // ATTENDANCE, ROULETTE, MISSION

    @Column(name = "start_date", nullable = false)
    private LocalDateTime startDate;

    @Column(name = "end_date", nullable = false)
    private LocalDateTime endDate;

    @Column(name = "is_active")
    private boolean isActive;

    @Column(name = "reward_type")
    @Enumerated(EnumType.STRING)
    private RewardType rewardType; // FP, ITEM, COUPON

    @Column(name = "reward_value")
    private int rewardValue;

    @Column(name = "daily_limit")
    private int dailyLimit;

    @Builder
    public Event(String title, EventType type, LocalDateTime startDate, LocalDateTime endDate, boolean isActive, RewardType rewardType, int rewardValue, int dailyLimit) {
        this.title = title;
        this.type = type;
        this.startDate = startDate;
        this.endDate = endDate;
        this.isActive = isActive;
        this.rewardType = rewardType;
        this.rewardValue = rewardValue;
        this.dailyLimit = dailyLimit;
    }

    public boolean isAvailable() {
        LocalDateTime now = LocalDateTime.now();
        return this.isActive && now.isAfter(this.startDate) && now.isBefore(this.endDate);
    }
}