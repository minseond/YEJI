package com.yeji.domain.wallet.repository;

import com.yeji.domain.wallet.entity.UserWallet;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

public interface UserWalletRepository extends JpaRepository<UserWallet, Long> {

    // 동시성 문제를 해결하기 위해 비관적 락(쓰기 잠금) 적용
    // 포인트 사용/충전 시에는 반드시 이 메서드로 조회해야 함
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT w FROM UserWallet w WHERE w.userId = :userId")
    Optional<UserWallet> findByUserIdWithLock(@Param("userId") Long userId);
}