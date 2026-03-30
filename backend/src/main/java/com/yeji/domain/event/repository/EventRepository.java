package com.yeji.domain.event.repository;

import com.yeji.domain.event.entity.Event;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface EventRepository extends JpaRepository<Event, Long> {

    // 현재 진행 중인 이벤트 목록 조회
    @Query("SELECT e FROM Event e WHERE e.isActive = true AND e.startDate <= :now AND e.endDate >= :now")
    List<Event> findAllActiveEvents(@Param("now") LocalDateTime now);
}