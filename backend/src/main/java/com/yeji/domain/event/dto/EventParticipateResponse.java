package com.yeji.domain.event.dto;

import com.yeji.domain.event.entity.RewardType;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class EventParticipateResponse {
    private boolean success;
    private String message;
    private RewardType rewardType;
    private int rewardAmount;
    private int currentBalance; // 보상 수령 후 잔액 (선택)
}