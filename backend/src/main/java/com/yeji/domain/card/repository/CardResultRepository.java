package com.yeji.domain.card.repository;

import com.yeji.domain.card.entity.CardCategory;
import com.yeji.domain.card.entity.CardResult;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface CardResultRepository extends JpaRepository<CardResult, Long> {

    //특정 결과 조회
    Optional<CardResult> findByIdAndUser_Id(Long id, Long userId);

    @Query("""
        SELECT r
        FROM CardResult r
        WHERE r.user.id = :userId
            AND r.category = coalesce(:category, r.category)
            AND r.createdAt >= coalesce(:from, r.createdAt)
            AND r.createdAt <= coalesce(:to, r.createdAt)
        ORDER BY r.createdAt DESC
""")
    List<CardResult> findAllByUserIdWithFilters(
            @Param("userId") Long userId,
            @Param("category") CardCategory category,
            @Param("from") LocalDateTime from,
            @Param("to") LocalDateTime to
    );
}
