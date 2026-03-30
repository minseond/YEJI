package com.yeji.domain.luck.repository;

import com.yeji.domain.luck.entity.LuckTransfer;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface LuckTransferRepository extends JpaRepository<LuckTransfer, Long> {
    // 수신함 조회 (최신순)
    List<LuckTransfer> findAllByReceiver_IdOrderByCreatedAtDesc(Long receiverId);
}