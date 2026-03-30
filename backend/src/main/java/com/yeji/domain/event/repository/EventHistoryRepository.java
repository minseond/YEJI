package com.yeji.domain.event.repository;

import com.yeji.domain.event.entity.EventHistory;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;

public interface EventHistoryRepository extends JpaRepository<EventHistory, Long> {

    // 특정 유저가 특정 기간(오늘) 동안 특정 이벤트에 참여한 횟수 조회
    int countByUserIdAndEventIdAndCreatedAtBetween(Long userId, Long eventId, LocalDateTime start, LocalDateTime end);
}