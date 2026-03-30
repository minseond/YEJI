package com.yeji.domain.unse.repository;

import com.yeji.domain.unse.entity.UnsePair;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

public interface UnsePairRepository extends JpaRepository<UnsePair, Long> {

    // 특정 유저의 결과 전체 최신순 조회
    List<UnsePair> findAllByUser_IdOrderByCreatedAtDesc(Long userId);
    //업뎃
    Optional<UnsePair> findByUser_IdAndCategory(Long userId, String category);
    // 특정 유저의 특정 결과 1건 조회
    Optional<UnsePair> findByIdAndUser_Id(Long id, Long userId);

    // 특정 유저의 특정 카테고리 최신 1건 조회 (가장 자주 씀)
    Optional<UnsePair> findTopByUser_IdAndCategoryOrderByCreatedAtDesc(Long userId, String category);

    // 특정 유저의 전체 최신 1건 조회 (카테고리 상관 없이)
    Optional<UnsePair> findTopByUser_IdOrderByCreatedAtDesc(Long userId);

    // 최근 N시간 이내 생성한 적 있는지 체크 (카테고리 상관 없이)
    boolean existsByUser_IdAndCreatedAtAfter(Long userId, LocalDateTime after);

    // 최근 N시간 이내 생성한 적 있는지 체크 (카테고리별)
    boolean existsByUser_IdAndCategoryAndCreatedAtAfter(Long userId, String category, LocalDateTime after);

    // 날짜별 조회 (오늘 생성된 것이 있는지 확인용)
    Optional<UnsePair> findTopByUser_IdAndCategoryAndCreatedAtBetweenOrderByCreatedAtDesc(
            Long userId, String category, LocalDateTime start, LocalDateTime end
    );

}
