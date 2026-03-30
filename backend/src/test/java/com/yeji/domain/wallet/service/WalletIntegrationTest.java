package com.yeji.domain.wallet.service;

import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.domain.wallet.entity.UserWallet;
import com.yeji.domain.wallet.repository.UserWalletRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

// 추후 동시성 체크 시 필요한 import
//import java.time.LocalDate;
//import java.time.LocalTime;
//import java.util.concurrent.CountDownLatch;
//import java.util.concurrent.ExecutorService;
//import java.util.concurrent.Executors;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class WalletIntegrationTest {

    @Autowired
    private WalletService walletService;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private UserWalletRepository userWalletRepository;

    @Test
    @DisplayName("지갑 생성 및 충전, 사용 테스트")
    void wallet_Basic_Flow() {
        // 1. 유저 생성 (회원가입 시뮬레이션)
        User user = userRepository.save(User.builder()
                .email("wallet_test@example.com")
                .nickname("richman")
                .provider("EMAIL")
                .isSolar(true)
                .build());

        // 2. 지갑 생성
        walletService.createWallet(user.getId());

        // 3. 초기 잔액 0 확인
        UserWallet wallet = userWalletRepository.findById(user.getId()).orElseThrow();
        assertThat(wallet.getBalance()).isEqualTo(0);

        // 4. 1000포인트 충전
        walletService.chargePoint(user.getId(), 1000, "Event");
        assertThat(userWalletRepository.findById(user.getId()).get().getBalance()).isEqualTo(1000);

        // 5. 500포인트 사용
        walletService.usePoint(user.getId(), 500, "TEST_SERVICE", "Service Use");
        assertThat(userWalletRepository.findById(user.getId()).get().getBalance()).isEqualTo(500);
    }

    // 동시성 테스트는 @Transactional 하에서 롤백 문제로 인해 별도 설정이 없으면 테스트가 까다롭지만
    // ExecutorService를 이용해 호출해볼 수 있음 (단, DB가 격리되어야 함)
}