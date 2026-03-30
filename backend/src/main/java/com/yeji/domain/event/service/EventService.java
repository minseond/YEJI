package com.yeji.domain.event.service;

import com.yeji.domain.event.dto.EventParticipateResponse;
import com.yeji.domain.event.dto.EventResponse;
import com.yeji.domain.event.entity.Event;
import com.yeji.domain.event.entity.EventHistory;
import com.yeji.domain.event.entity.EventType;
import com.yeji.domain.event.entity.RewardType;
import com.yeji.domain.event.repository.EventHistoryRepository;
import com.yeji.domain.event.repository.EventRepository;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.domain.wallet.service.WalletService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class EventService {

    private final EventRepository eventRepository;
    private final EventHistoryRepository eventHistoryRepository;
    private final WalletService walletService;
    private final UserRepository userRepository;

    // 랜덤 생성을 위한 객체
    private final Random random = new Random();

    // 진행 중인 이벤트 목록 조회
    public List<EventResponse> getActiveEvents(Long userId) {
        LocalDateTime now = LocalDateTime.now();
        List<Event> events = eventRepository.findAllActiveEvents(now);

        return events.stream().map(event -> {
            int todayCount = getTodayParticipationCount(userId, event.getId());
            return EventResponse.of(event, todayCount);
        }).collect(Collectors.toList());
    }

    // 이벤트 참여하기 (출석, 뽑기 등)
    @Transactional
    public EventParticipateResponse participate(Long userId, Long eventId) {
        Event event = eventRepository.findById(eventId)
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 이벤트입니다."));

        if (!event.isAvailable()) {
            throw new IllegalStateException("종료되었거나 유효하지 않은 이벤트입니다.");
        }

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 유저입니다."));

        // 1. 일일 참여 횟수 제한 체크
        int todayCount = getTodayParticipationCount(userId, eventId);
        if (todayCount >= event.getDailyLimit()) {
            throw new IllegalStateException("오늘 참여 횟수를 모두 소진했습니다.");
        }

        // 2. 보상 계산 (랜덤 로직 적용)
        int rewardAmount = event.getRewardValue();

        // 이벤트 타입이 룰렛(ROULETTE)이라면 랜덤 보상 로직 실행
        if (event.getType() == EventType.ROULETTE) {
            rewardAmount = drawRandomReward();
        }

        // 3. 보상 지급 (WalletService 연동 수정: description 추가)
        if (event.getRewardType() == RewardType.FP && rewardAmount > 0) {
            String description = event.getTitle() + " 참여 보상"; // 예: "매일 행운 뽑기 참여 보상"
            walletService.chargePoint(userId, rewardAmount, description);
        }

        // 4. 참여 기록 저장
        EventHistory history = EventHistory.builder()
                .user(user)
                .event(event)
                .rewardAmount(rewardAmount)
                .build();
        eventHistoryRepository.save(history);

        return EventParticipateResponse.builder()
                .success(true)
                .message(event.getTitle() + " 참여 완료!")
                .rewardType(event.getRewardType())
                .rewardAmount(rewardAmount)
                .build();
    }

    private int getTodayParticipationCount(Long userId, Long eventId) {
        LocalDateTime startOfDay = LocalDate.now().atStartOfDay();
        LocalDateTime endOfDay = LocalDate.now().atTime(23, 59, 59);
        return eventHistoryRepository.countByUserIdAndEventIdAndCreatedAtBetween(userId, eventId, startOfDay, endOfDay);
    }

    /**
     * 랜덤 보상 추첨 로직
     * 추후 DB(events 테이블의 json 필드 등)에서 확률표를 가져오도록 고도화 가능
     */
    private int drawRandomReward() {
        // [보상금액, 확률(%)] 설정
        // 확률의 합계는 100
        Map<Integer, Integer> probabilityTable = new LinkedHashMap<>();
        probabilityTable.put(5, 50);   // 5FP: 50%
        probabilityTable.put(10, 30);   // 10FP: 30%
        probabilityTable.put(20, 10);   // 20FP: 10%
        probabilityTable.put(30, 5);  // 30FP: 5%
        probabilityTable.put(50, 3);  // 50FP: 3%
        probabilityTable.put(100, 1);  // 100FP: 1% (대박)
        probabilityTable.put(500, 1);  // 500FP: 1% (대박)

        int randomValue = random.nextInt(100) + 1; // 1 ~ 100 사이 랜덤 숫자
        int currentSum = 0;

        for (Map.Entry<Integer, Integer> entry : probabilityTable.entrySet()) {
            currentSum += entry.getValue();
            if (randomValue <= currentSum) {
                return entry.getKey();
            }
        }

        return 5; // 기본값 (혹시 모를 오류 대비)
    }
}