package com.yeji.domain.unse.service;

import com.yeji.domain.unse.dto.UnseResultDetailResponse;
import com.yeji.domain.unse.dto.UnseResultListItemResponse;
import com.yeji.domain.unse.entity.UnsePair;
import com.yeji.domain.unse.repository.UnsePairRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

// 조회 전용 Service -> History, ResultDetail
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UnseResultService {

    private final UnsePairRepository unsePairRepository;

    public List<UnseResultListItemResponse> getHistory(Long userId) {
        return unsePairRepository.findAllByUser_IdOrderByCreatedAtDesc(userId)
                .stream()
                .map(UnseResultListItemResponse::from) // from(UnsePair)로 바뀌어야 함
                .toList();
    }

    public UnseResultDetailResponse getDetail(Long userId, Long resultId) {
        UnsePair r = unsePairRepository.findByIdAndUser_Id(resultId, userId)
                .orElseThrow(() -> new RuntimeException("운세 결과를 찾을 수 없습니다."));
        return UnseResultDetailResponse.from(r); // from(UnsePair)로 바뀌어야 함
    }
}
