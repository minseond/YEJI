package com.yeji.domain.luck.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
public class LuckTransferRequest {
    private Long receiverId;
    private String transferType; // BLESS, CURSE
    private Long originResultId; // 공유할 결과 ID (옵션)
    private String originTableType; // SAJU, TARO 등 (옵션)
    private int characterType; // 보낼 캐릭터 아이콘 타입
    private String message;
}