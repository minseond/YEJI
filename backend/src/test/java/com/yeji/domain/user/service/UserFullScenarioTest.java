package com.yeji.domain.user.service;

import com.yeji.domain.user.dto.*;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.entity.UserSettings;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.domain.user.repository.UserSettingsRepository;
import com.yeji.domain.wallet.repository.UserWalletRepository;
import jakarta.mail.Session;
import jakarta.mail.internet.MimeMessage;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.transaction.annotation.Transactional;

import java.lang.reflect.Constructor;
import java.time.LocalDate;
import java.time.LocalTime;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class UserFullScenarioTest {

    @Autowired private UserService userService;
    @Autowired private UserRepository userRepository;
    @Autowired private UserSettingsRepository userSettingsRepository;
    @Autowired private UserWalletRepository userWalletRepository;
    @Autowired private RedisTemplate<String, String> redisTemplate;
    @Autowired private PasswordEncoder passwordEncoder;

    @MockitoBean
    private JavaMailSender javaMailSender;

    @BeforeEach
    void setUp() {
        MimeMessage mimeMessage = new MimeMessage((Session) null);
        given(javaMailSender.createMimeMessage()).willReturn(mimeMessage);
    }

    @Test
    @DisplayName("1. 회원가입: 최소 정보로 가입하며, 지갑/설정은 자동 생성되고 추가 정보는 비어있다")
    void signup_success_test() {
        // Given: 이메일, 비번, 닉네임만 입력
        UserSignupRequest request = createSignupRequest("test@yeji.com", "password123", "테스터");

        // When
        UserResponse response = userService.signup(request);

        // Then
        // 1. 기본 정보 확인
        assertThat(response.getEmail()).isEqualTo("test@yeji.com");
        assertThat(response.getNickname()).isEqualTo("테스터");

        // 2. 입력하지 않은 정보는 null 또는 기본값이어야 함
        User savedUser = userRepository.findById(response.getId()).orElseThrow();
        assertThat(savedUser.getNameKor()).isNull();
        assertThat(savedUser.getBirthDate()).isNull();
        assertThat(savedUser.isSolar()).isTrue(); // Entity의 기본값 true 확인

        // 3. 연관 데이터 생성 확인
        assertThat(userWalletRepository.findById(response.getId())).isPresent();
        assertThat(userSettingsRepository.findById(response.getId())).isPresent();
    }

    @Test
    @DisplayName("2. 비밀번호 검증: 정보 수정 전 비밀번호 확인 로직 검증")
    void verify_password_test() {
        // Given
        UserSignupRequest signupRequest = createSignupRequest("verify@yeji.com", "realPassword!", "검증유저");
        UserResponse user = userService.signup(signupRequest);

        // When & Then
        // 1. 올바른 비밀번호 입력 시 -> 예외 없음
        userService.verifyPassword(user.getId(), "realPassword!");

        // 2. 틀린 비밀번호 입력 시 -> 예외 발생
        assertThatThrownBy(() -> userService.verifyPassword(user.getId(), "wrongPassword"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("비밀번호가 일치하지 않습니다.");
    }

    @Test
    @DisplayName("3. 회원 정보 수정: 닉네임 변경 및 사주 정보(생년월일 등) 입력 검증")
    void update_user_info_test() {
        // Given
        UserSignupRequest signupRequest = createSignupRequest("update@yeji.com", "pass", "전닉네임");
        UserResponse user = userService.signup(signupRequest);

        // 변경할 데이터 준비
        LocalDate newBirthDate = LocalDate.of(1995, 12, 25);
        LocalTime newBirthTime = LocalTime.of(15, 30);

        UserUpdateRequest updateRequest = createUserUpdateRequest(
                "새닉네임",
                "http://img.url/new.png",
                "홍길동",
                "洪吉童",
                "M",
                newBirthDate,
                newBirthTime,
                false // 음력으로 변경 (isSolar)
        );

        // When
        UserResponse updatedResponse = userService.updateProfile(user.getId(), updateRequest);

        // Then
        User dbUser = userRepository.findById(user.getId()).orElseThrow();

        assertThat(updatedResponse.getNickname()).isEqualTo("새닉네임");
        assertThat(dbUser.getNickname()).isEqualTo("새닉네임");
        assertThat(dbUser.getProfileImg()).isEqualTo("http://img.url/new.png");
        assertThat(dbUser.getNameKor()).isEqualTo("홍길동");
        assertThat(dbUser.getBirthDate()).isEqualTo(newBirthDate);
        assertThat(dbUser.getBirthTime()).isEqualTo(newBirthTime);
        assertThat(dbUser.isSolar()).isFalse();
    }

    @Test
    @DisplayName("4. 비밀번호 재설정 시나리오")
    void reset_password_scenario() {
        // 1. 회원가입
        String email = "reset@yeji.com";
        userService.signup(createSignupRequest(email, "oldPass", "리셋유저"));

        // 2. 인증 코드 발송
        userService.sendEmailVerification(createEmailRequest(email));

        // 3. Redis 코드 조회
        String verificationCode = redisTemplate.opsForValue().get("EmailAuth:" + email);
        assertThat(verificationCode).isNotNull();

        // 4. 재설정 실행
        String newPassword = "newPassword123!";
        PasswordResetRequest resetRequest = createPasswordResetRequest(email, verificationCode, newPassword);
        userService.resetPassword(resetRequest);

        // 5. 검증
        User user = userRepository.findByEmail(email).orElseThrow();
        assertThat(passwordEncoder.matches(newPassword, user.getPassword())).isTrue();
    }

    @Test
    @DisplayName("5. 환경 설정 수정 테스트")
    void update_settings_test() {
        // Given
        UserResponse user = userService.signup(createSignupRequest("set@yeji.com", "pw", "설정유저"));

        // When
        UserSettingsUpdateRequest updateRequest = createUserSettingsUpdateRequest(false, true, null, null);
        userService.updateSettings(user.getId(), updateRequest);

        // Then
        UserSettings settings = userSettingsRepository.findById(user.getId()).orElseThrow();
        assertThat(settings.isPushEnabled()).isFalse();
        assertThat(settings.isMarketingAgreed()).isTrue();
    }

    @Test
    @DisplayName("6. 회원 탈퇴 시나리오: 인증 코드 검증 후 탈퇴 처리")
    void withdraw_scenario_test() {
        // 1. 회원가입
        String email = "bye@yeji.com";
        UserResponse user = userService.signup(createSignupRequest(email, "password", "탈퇴자"));

        // 로그인 상태 시뮬레이션 (Redis에 RT 저장)
        redisTemplate.opsForValue().set("RT:" + email, "dummy-refresh-token");

        // 2. 탈퇴용 인증 코드 발송 요청
        userService.sendWithdrawVerification(user.getId());

        // 3. Redis에서 발송된 코드 탈취 (테스트 환경이므로 직접 조회)
        // EmailService 로직 상 키는 "EmailAuth:{email}" 형태임
        String verificationCode = redisTemplate.opsForValue().get("EmailAuth:" + email);
        assertThat(verificationCode).isNotNull();

        // 4. 틀린 코드로 탈퇴 시도 -> 실패 검증
        assertThatThrownBy(() -> userService.withdraw(user.getId(), "WRONG_CODE_123"))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("인증 코드"); // 에러 메시지 검증

        // 5. 올바른 코드로 탈퇴 시도 -> 성공
        userService.withdraw(user.getId(), verificationCode);

        // 6. DB 조회 시 검색되지 않아야 함 (Soft Delete + @SQLRestriction 동작 확인)
        assertThat(userRepository.findById(user.getId())).isEmpty();

        // 7. Redis의 Refresh Token도 삭제되었는지 확인
        Boolean hasRefreshToken = redisTemplate.hasKey("RT:" + email);
        assertThat(hasRefreshToken).isFalse();
    }

    // --- DTO 생성 헬퍼 메서드 (Protected 생성자 접근을 위해 Reflection 사용) ---

    private <T> T createInstance(Class<T> clazz) {
        try {
            Constructor<T> constructor = clazz.getDeclaredConstructor();
            constructor.setAccessible(true);
            return constructor.newInstance();
        } catch (Exception e) {
            throw new RuntimeException("Failed to instantiate " + clazz.getName(), e);
        }
    }

    private UserSignupRequest createSignupRequest(String email, String password, String nickname) {
        UserSignupRequest req = createInstance(UserSignupRequest.class);
        ReflectionTestUtils.setField(req, "email", email);
        ReflectionTestUtils.setField(req, "password", password);
        ReflectionTestUtils.setField(req, "nickname", nickname);
        return req;
    }

    private UserUpdateRequest createUserUpdateRequest(String nickname, String profileImg, String nameKor,
                                                      String nameChn, String gender, LocalDate birthDate, LocalTime birthTime, Boolean isSolar) {
        UserUpdateRequest req = createInstance(UserUpdateRequest.class);
        ReflectionTestUtils.setField(req, "nickname", nickname);
        ReflectionTestUtils.setField(req, "profileImg", profileImg);
        ReflectionTestUtils.setField(req, "nameKor", nameKor);
        ReflectionTestUtils.setField(req, "nameChn", nameChn);
        ReflectionTestUtils.setField(req, "gender", nameChn);
        ReflectionTestUtils.setField(req, "birthDate", birthDate);
        ReflectionTestUtils.setField(req, "birthTime", birthTime);
        ReflectionTestUtils.setField(req, "isSolar", isSolar);
        return req;
    }

    private EmailRequest createEmailRequest(String email) {
        EmailRequest req = createInstance(EmailRequest.class);
        ReflectionTestUtils.setField(req, "email", email);
        return req;
    }

    private PasswordResetRequest createPasswordResetRequest(String email, String code, String newPassword) {
        PasswordResetRequest req = createInstance(PasswordResetRequest.class);
        ReflectionTestUtils.setField(req, "email", email);
        ReflectionTestUtils.setField(req, "code", code);
        ReflectionTestUtils.setField(req, "newPassword", newPassword);
        return req;
    }

    private UserSettingsUpdateRequest createUserSettingsUpdateRequest(Boolean push, Boolean marketing, Boolean sound, Boolean vib) {
        UserSettingsUpdateRequest req = createInstance(UserSettingsUpdateRequest.class);
        ReflectionTestUtils.setField(req, "pushEnabled", push);
        ReflectionTestUtils.setField(req, "marketingAgreed", marketing);
        ReflectionTestUtils.setField(req, "soundEnabled", sound);
        ReflectionTestUtils.setField(req, "vibEnabled", vib);
        return req;
    }
}