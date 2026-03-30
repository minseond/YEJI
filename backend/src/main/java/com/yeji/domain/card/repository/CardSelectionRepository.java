package com.yeji.domain.card.repository;


import com.yeji.domain.card.entity.CardSelection;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface CardSelectionRepository extends JpaRepository<CardSelection, Long> {

    // 결과 ID 기준 카드 3장 조회
    @Query("""
        SELECT c
        FROM CardSelection c
        WHERE c.cardResult.id = :resultId
        ORDER BY c.position ASC
""")
    List<CardSelection> findByResultId(@Param("resultId") Long resultId);
}
