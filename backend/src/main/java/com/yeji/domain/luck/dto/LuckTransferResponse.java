package com.yeji.domain.luck.dto;

import com.yeji.domain.luck.entity.LuckTransfer;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@Builder
public class LuckTransferResponse {
    private Long id;
    private Long senderId;
    private String senderName;
    private String transferType;
    private String message;
    private int characterType;
    private boolean isRead;
    private LocalDateTime createdAt;

    public static LuckTransferResponse from(LuckTransfer entity) {
        return LuckTransferResponse.builder()
                .id(entity.getId())
                .senderId(entity.getSender().getId())
                .senderName(entity.getSender().getNickname())
                .transferType(entity.getTransferType())
                .message(entity.getMessage())
                .characterType(entity.getCharacterType())
                .isRead(entity.isRead())
                .createdAt(entity.getCreatedAt())
                .build();
    }
}