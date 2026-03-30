package com.yeji.domain.wallet.dto;

import com.yeji.domain.wallet.entity.UserWallet;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@Schema(description = "지갑 정보 응답")
public class WalletResponse {
    @Schema(description = "유저 ID")
    private final Long userId;
    @Schema(description = "현재 보유 토큰(FP)")
    private final Integer balance;
    @Schema(description = "마지막 변동 일시")
    private final LocalDateTime updatedAt;

    public WalletResponse(UserWallet wallet) {
        this.userId = wallet.getUserId();
        this.balance = wallet.getBalance();
        this.updatedAt = wallet.getUpdatedAt();
    }
}