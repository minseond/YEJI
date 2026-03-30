package com.yeji.domain.luck.service;

import com.yeji.domain.luck.dto.LuckTransferRequest;
import com.yeji.domain.luck.dto.LuckTransferResponse;
import com.yeji.domain.luck.entity.LuckTransfer;
import com.yeji.domain.luck.repository.LuckTransferRepository;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.global.jwt.AuthUser;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class LuckService {

    private final LuckTransferRepository luckTransferRepository;
    private final UserRepository userRepository;

    // LUCK-001 운세/저주 전송
    @Transactional
    public LuckTransferResponse sendLuck(AuthUser authUser, LuckTransferRequest request) {
        User sender = userRepository.findById(authUser.getUserId())
                .orElseThrow(() -> new IllegalArgumentException("발신자 정보를 찾을 수 없습니다."));

        User receiver = userRepository.findById(request.getReceiverId())
                .orElseThrow(() -> new IllegalArgumentException("수신자 정보를 찾을 수 없습니다."));

        LuckTransfer transfer = LuckTransfer.builder()
                .sender(sender)
                .receiver(receiver)
                .transferType(request.getTransferType())
                .message(request.getMessage())
                .characterType(request.getCharacterType())
                .originResultId(request.getOriginResultId())
                .originTableType(request.getOriginTableType())
                .build();

        LuckTransfer saved = luckTransferRepository.save(transfer);
        return LuckTransferResponse.from(saved);
    }

    // LUCK-002 수신함 조회
    public List<LuckTransferResponse> getInbox(AuthUser authUser) {
        return luckTransferRepository.findAllByReceiver_IdOrderByCreatedAtDesc(authUser.getUserId())
                .stream()
                .map(LuckTransferResponse::from)
                .collect(Collectors.toList());
    }

    // LUCK-003 읽음 처리
    @Transactional
    public void markAsRead(AuthUser authUser, Long transferId) {
        LuckTransfer transfer = luckTransferRepository.findById(transferId)
                .orElseThrow(() -> new IllegalArgumentException("메시지를 찾을 수 없습니다."));

        if (!transfer.getReceiver().getId().equals(authUser.getUserId())) {
            throw new IllegalArgumentException("본인의 메시지만 읽음 처리할 수 있습니다.");
        }

        transfer.markAsRead();
    }
}