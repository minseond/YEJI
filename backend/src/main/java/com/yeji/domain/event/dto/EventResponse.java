package com.yeji.domain.event.dto;

import com.yeji.domain.event.entity.Event;
import com.yeji.domain.event.entity.EventType;
import com.yeji.domain.event.entity.RewardType;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@Builder
@AllArgsConstructor
public class EventResponse {
    private Long eventId;
    private String title;
    private EventType type;
    private LocalDateTime startDate;
    private LocalDateTime endDate;
    private RewardType rewardType;
    private int rewardValue;
    private int dailyLimit;

    // 유저별 상태 (목록 조회 시 필요)
    private int myParticipationCountToday;
    private boolean isParticipatedToday;

    public static EventResponse of(Event event, int todayCount) {
        return EventResponse.builder()
                .eventId(event.getId())
                .title(event.getTitle())
                .type(event.getType())
                .startDate(event.getStartDate())
                .endDate(event.getEndDate())
                .rewardType(event.getRewardType())
                .rewardValue(event.getRewardValue())
                .dailyLimit(event.getDailyLimit())
                .myParticipationCountToday(todayCount)
                .isParticipatedToday(todayCount >= event.getDailyLimit())
                .build();
    }
}