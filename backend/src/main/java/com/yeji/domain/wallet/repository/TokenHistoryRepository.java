package com.yeji.domain.wallet.repository;

import com.yeji.domain.wallet.entity.TokenHistory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TokenHistoryRepository extends JpaRepository<TokenHistory, Long> {
    // 최신순 조회
    Page<TokenHistory> findAllByUserIdOrderByCreatedAtDesc(Long userId, Pageable pageable);
}