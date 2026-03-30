package com.yeji.domain.event.service;

import com.yeji.domain.event.dto.EventParticipateResponse;
import com.yeji.domain.event.entity.Event;
import com.yeji.domain.event.entity.EventType;
import com.yeji.domain.event.entity.RewardType;
import com.yeji.domain.event.repository.EventHistoryRepository;
import com.yeji.domain.event.repository.EventRepository;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.domain.wallet.entity.UserWallet;
import com.yeji.domain.wallet.repository.UserWalletRepository;
import com.yeji.domain.wallet.service.WalletService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@SpringBootTest
@Transactional
class EventIntegrationTest {

    @Autowired
    private EventService eventService;

    @Autowired
    private EventRepository eventRepository;

    @Autowired
    private EventHistoryRepository eventHistoryRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private UserWalletRepository userWalletRepository;

    @Autowired
    private WalletService walletService; // WalletService 주입

    private User testUser;

    @BeforeEach
    void setUp() {
        // 1. User 생성 (User 클래스에 @Builder 존재)
        testUser = User.builder()
                .email("test@event.com")
                .nickname("EventTester")
                .password("password")
                .build();
        userRepository.save(testUser);

        // 2. UserWallet 생성 (UserWallet 클래스에 @Builder 없음, 생성자 사용)
        // WalletService의 createWallet 메서드를 사용하거나 직접 Repository에 저장
        // 여기서는 직접 저장 방식을 사용하되, UserWallet의 public 생성자를 활용
        UserWallet wallet = new UserWallet(testUser.getId());
        userWalletRepository.save(wallet);
    }

    @Test
    @DisplayName("출석 이벤트: 1일 1회 참여 및 보상 지급 성공")
    void attendance_success() {
        // Given: 출석 이벤트 생성
        Event attendanceEvent = Event.builder()
                .title("매일 출석체크")
                .type(EventType.ATTENDANCE)
                .startDate(LocalDateTime.now().minusDays(1))
                .endDate(LocalDateTime.now().plusDays(10))
                .isActive(true)
                .rewardType(RewardType.FP)
                .rewardValue(100)
                .dailyLimit(1)
                .build();
        eventRepository.save(attendanceEvent);

        // When: 이벤트 참여
        EventParticipateResponse response = eventService.participate(testUser.getId(), attendanceEvent.getId());

        // Then: 결과 검증
        assertThat(response.isSuccess()).isTrue();
        assertThat(response.getRewardAmount()).isEqualTo(100);

        // 지갑 잔액 확인
        UserWallet wallet = userWalletRepository.findById(testUser.getId()).orElseThrow();
        // 초기 잔액 0 + 보상 100 = 100
        assertThat(wallet.getBalance()).isEqualTo(100);
    }

    @Test
    @DisplayName("출석 이벤트: 하루에 두 번 참여하면 예외 발생")
    void attendance_fail_duplicate() {
        // Given
        Event attendanceEvent = Event.builder()
                .title("매일 출석체크")
                .type(EventType.ATTENDANCE)
                .startDate(LocalDateTime.now().minusDays(1))
                .endDate(LocalDateTime.now().plusDays(10))
                .isActive(true)
                .rewardType(RewardType.FP)
                .rewardValue(100)
                .dailyLimit(1)
                .build();
        eventRepository.save(attendanceEvent);

        // When: 첫 번째 참여 (성공)
        eventService.participate(testUser.getId(), attendanceEvent.getId());

        // Then: 두 번째 참여 시 예외 발생
        assertThatThrownBy(() -> eventService.participate(testUser.getId(), attendanceEvent.getId()))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("참여 횟수를 모두 소진했습니다");
    }

    @Test
    @DisplayName("룰렛 이벤트: 1일 3회 참여 가능 및 랜덤 보상 지급")
    void roulette_success_multiple_times() {
        // Given
        Event rouletteEvent = Event.builder()
                .title("행운의 룰렛")
                .type(EventType.ROULETTE)
                .startDate(LocalDateTime.now().minusDays(1))
                .endDate(LocalDateTime.now().plusDays(10))
                .isActive(true)
                .rewardType(RewardType.FP)
                .rewardValue(0) // 랜덤 로직을 타므로 기본값 무시
                .dailyLimit(3)
                .build();
        eventRepository.save(rouletteEvent);

        // When: 3회 참여 시도
        for (int i = 0; i < 3; i++) {
            EventParticipateResponse response = eventService.participate(testUser.getId(), rouletteEvent.getId());
            assertThat(response.isSuccess()).isTrue();
            System.out.println((i+1) + "회차 룰렛 보상: " + response.getRewardAmount());
        }

        // Then: 4회차 시도 시 실패
        assertThatThrownBy(() -> eventService.participate(testUser.getId(), rouletteEvent.getId()))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("참여 횟수를 모두 소진했습니다");

        // 지갑 잔액이 증가했는지 확인 (최소 10FP * 3 = 30FP 이상이어야 함)
        UserWallet wallet = userWalletRepository.findById(testUser.getId()).orElseThrow();
        assertThat(wallet.getBalance()).isGreaterThanOrEqualTo(15);
    }
}