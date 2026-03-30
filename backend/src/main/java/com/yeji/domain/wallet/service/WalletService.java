package com.yeji.domain.wallet.service;

import com.yeji.domain.wallet.dto.TokenHistoryResponse;
import com.yeji.domain.wallet.dto.WalletResponse;
import com.yeji.domain.wallet.entity.TokenHistory;
import com.yeji.domain.wallet.entity.UserWallet;
import com.yeji.domain.wallet.exception.NotEnoughBalanceException;
import com.yeji.domain.wallet.repository.TokenHistoryRepository;
import com.yeji.domain.wallet.repository.UserWalletRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class WalletService {
    private final UserWalletRepository userWalletRepository;
    private final TokenHistoryRepository tokenHistoryRepository;

    // 지갑 생성(회원가입 시)
    @Transactional
    public void createWallet(Long userId) {
        if(!userWalletRepository.existsById(userId)) {
            userWalletRepository.save(new UserWallet(userId));
        }
    }

    // 내 지갑 조회
    public WalletResponse getMyWallet(Long userId) {
        UserWallet wallet = userWalletRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("해당 회원의 지갑을 찾을 수 없습니다."));
        return new WalletResponse(wallet);
    }

    // 토큰 내역 조회
    public Page<TokenHistoryResponse> getTokenHistory(Long userId, Pageable pageable) {
        return tokenHistoryRepository.findAllByUserIdOrderByCreatedAtDesc(userId, pageable)
                .map(TokenHistoryResponse::new);
    }

    // 포인트 충전 (결제 완료 후, 혹은 관리자가 지급)
    @Transactional
    public void chargePoint(Long userId, int amount, String description) {
        // 일단 Lock을 걸고 조회
        UserWallet wallet = userWalletRepository.findByUserIdWithLock(userId)
                .orElseThrow(() -> new RuntimeException("해당 회원의 지갑이 존재하지 않습니다."));

        wallet.addBalance(amount);

        tokenHistoryRepository.save(TokenHistory.builder()
                .userId(userId)
                .amount(amount)
                .type("CHARGE")
                .description(description)
                .build());
    }

    // 포인트 사용(서비스 이용 시 호출)
    @Transactional
    public void usePoint(Long userId, int amount, String serviceCode, String description) {
        UserWallet wallet = userWalletRepository.findByUserIdWithLock(userId)
                .orElseThrow(() -> new RuntimeException("해당 회원의 지갑이 존재하지 않습니다."));

        // 잔액 부족시 Exception
        if (wallet.getBalance() < amount) {
            throw new NotEnoughBalanceException("잔액이 부족합니다.");
        }

        wallet.subtractBalance(amount);

        tokenHistoryRepository.save(TokenHistory.builder()
                .userId(userId)
                .amount(-amount) // 사용은 음수로 표기할 수도 있고 양수로 하고 타입을 USE로 할 수도 있음. 여기선 양수+USE타입
                .serviceCode(serviceCode)
                .type("USE")
                .description(description)
                .build());
    }
}
