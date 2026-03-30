package com.yeji.domain.user.service;

import com.yeji.domain.user.dto.*;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.entity.UserSettings;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.domain.user.repository.UserSettingsRepository;
import com.yeji.domain.wallet.service.WalletService;
import com.yeji.global.jwt.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.NoSuchElementException;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;
    private final UserSettingsRepository userSettingsRepository;
    private final PasswordEncoder passwordEncoder;
    private final RedisTemplate<String, String> redisTemplate;
    private final JwtTokenProvider jwtTokenProvider;
    private final EmailService emailService;
    private final WalletService walletService;

    // 회원가입
    @Transactional
    public UserResponse signup(UserSignupRequest request) {
        if (userRepository.findByEmail(request.getEmail()).isPresent()) {
            throw new RuntimeException("이미 존재하는 이메일입니다.");
        }
        if (userRepository.existsByNickname(request.getNickname())) {
            throw new RuntimeException("이미 존재하는 닉네임입니다.");
        }

        // [수정] 이메일, 패스워드, 닉네임만 저장 (나머지는 null 또는 기본값)
        User user = User.builder()
                .email(request.getEmail())
                .password(passwordEncoder.encode(request.getPassword())) // 암호화 저장
                .nickname(request.getNickname())
                .provider("EMAIL")
                .isSolar(true) // 기본값 설정 (필요 시)
                .build();

        User savedUser = userRepository.save(user);

        // 지갑 생성
        walletService.createWallet(savedUser.getId());

        // 기본 설정 생성
        userSettingsRepository.save(UserSettings.createDefault(savedUser));

        return UserResponse.from(savedUser);
    }

    // 로그인
    @Transactional
    public TokenResponse login(UserLoginRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("가입되지 않은 이메일입니다."));

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new RuntimeException("비밀번호가 일치하지 않습니다.");
        }

        // JWT 생성 (Role 파라미터 없음)
        String accessToken = jwtTokenProvider.createAccessToken(user.getEmail(), user.getId());
        String refreshToken = jwtTokenProvider.createRefreshToken(user.getEmail());

        // Redis 저장 (Refresh Token)
        redisTemplate.opsForValue().set(
                "RT:" + user.getEmail(),
                refreshToken,
                7,
                TimeUnit.DAYS
        );

        return TokenResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .build();
    }

    // 로그아웃
    @Transactional
    public void logout(String refreshToken) {
        // 토큰 유효성 검증
        if (!jwtTokenProvider.validateToken(refreshToken)) {
            throw new RuntimeException("유효하지 않은 토큰입니다.");
        }

        String email = jwtTokenProvider.getSubject(refreshToken);

        if (redisTemplate.hasKey("RT:" + email)) {
            redisTemplate.delete("RT:" + email);
        }
    }

    // 토큰 재발급
    @Transactional
    public TokenResponse reissue(TokenRefreshRequest request) {
        if (!jwtTokenProvider.validateToken(request.getRefreshToken())) {
            throw new RuntimeException("Refresh Token이 유효하지 않습니다.");
        }

        String email = jwtTokenProvider.getSubject(request.getRefreshToken());
        String savedToken = redisTemplate.opsForValue().get("RT:" + email);

        if (savedToken == null || !savedToken.equals(request.getRefreshToken())) {
            throw new RuntimeException("Refresh Token이 일치하지 않습니다.");
        }

        // 유저 정보 조회 (ID 필요)
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found"));

        // 토큰 재발급
        String newAccessToken = jwtTokenProvider.createAccessToken(email, user.getId());
        String newRefreshToken = jwtTokenProvider.createRefreshToken(email);

        redisTemplate.opsForValue().set("RT:" + email, newRefreshToken, 7, TimeUnit.DAYS);

        return TokenResponse.builder()
                .accessToken(newAccessToken)
                .refreshToken(newRefreshToken)
                .build();
    }

    // 상세 조회
    public UserResponse getUserInfo(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        return UserResponse.from(user);
    }

    // [추가] 비밀번호 검증 (정보 수정 진입 전 단계)
    public void verifyPassword(Long userId, String rawPassword) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new NoSuchElementException("존재하지 않는 사용자입니다."));

        if (!passwordEncoder.matches(rawPassword, user.getPassword())) {
            throw new IllegalArgumentException("비밀번호가 일치하지 않습니다.");
        }
    }

    // USER-006 회원 정보 수정 (PATCH) -> 닉네임, 사주정보 등 업데이트
    @Transactional
    public UserResponse updateProfile(Long userId, UserUpdateRequest request) { // email 대신 userId 사용 권장 (Controller에서 넘어온 ID)
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        // 닉네임 변경 시 중복 체크
        if (request.getNickname() != null &&
                !request.getNickname().equals(user.getNickname()) &&
                userRepository.existsByNickname(request.getNickname())) {
            throw new RuntimeException("이미 존재하는 닉네임입니다.");
        }

        // 엔티티의 업데이트 메서드 호출 (생년월일, isSolar 등 포함)
        user.updateUserInfo(request);

        return UserResponse.from(user);
    }

    // USER-007 회원 탈퇴 (DELETE)
    @Transactional
    public void withdraw(Long userId, String code) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        // [보안] 이메일 가입자는 인증 코드 필수 검증
        if ("EMAIL".equals(user.getProvider())) {
            if (!emailService.verifyCode(user.getEmail(), code)) {
                throw new RuntimeException("인증 코드가 올바르지 않거나 만료되었습니다.");
            }
            // 검증 성공 후 코드 삭제 (재사용 방지)
            emailService.deleteCode(user.getEmail());
        }

        // 1. Refresh Token 삭제 (로그아웃 처리)
        if (redisTemplate.hasKey("RT:" + user.getEmail())) {
            redisTemplate.delete("RT:" + user.getEmail());
        }

        // 2. Soft Delete 실행 (엔티티의 @SQLDelete 작동)
        userRepository.delete(user);
    }

    // 탈퇴 인증 코드 발송
    public void sendWithdrawVerification(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        // EmailService 재활용 (이메일로 코드 전송)
        emailService.sendVerificationCode(user.getEmail());
    }

    // USER-009 이메일 인증번호 전송(회원가입용)
    public void sendEmailVerification(EmailRequest request) {
        emailService.sendVerificationCode(request.getEmail());
    }

    // USER-009 이메일 인증번호 검증 (단순 확인용)
    public boolean verifyEmail(EmailVerificationRequest request) {
        return emailService.verifyCode(request.getEmail(), request.getCode());
    }

    // USER-008 비밀번호 재설정
    @Transactional
    public void resetPassword(PasswordResetRequest request) {
        // 1. 인증 코드 검증
        if (!emailService.verifyCode(request.getEmail(), request.getCode())) {
            throw new RuntimeException("인증 코드가 올바르지 않거나 만료되었습니다.");
        }

        // 2. 유저 조회
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("가입되지 않은 이메일입니다."));

        // 3. 비밀번호 변경 (자체 회원가입 유저만 가능)
        if (!"EMAIL".equals(user.getProvider())) {
            throw new RuntimeException("소셜 로그인 사용자는 해당 소셜 서비스에서 비밀번호를 변경해야 합니다.");
        }

        // 비밀번호 업데이트 실행
        user.updatePassword(passwordEncoder.encode(request.getNewPassword()));

        // 인증 코드 사용 완료 처리
        emailService.deleteCode(request.getEmail());
    }

    // SET-001 설정 조회
    public UserSettingsResponse getSettings(Long userId) {
        UserSettings settings = userSettingsRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("해당 회원의 정보를 찾을 수 없습니다."));
        return new UserSettingsResponse(settings);
    }

    // SET-002 설정 수정
    @Transactional
    public UserSettingsResponse updateSettings(Long userId, UserSettingsUpdateRequest request) {
        UserSettings settings = userSettingsRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("해당 회원의 설정 정보를 찾을 수 없습니다."));

        settings.update(
                request.getPushEnabled(),
                request.getMarketingAgreed(),
                request.getSoundEnabled(),
                request.getVibEnabled()
        );

        return new UserSettingsResponse(settings);
    }
    // 회원가입용 중복 체크 메서드
    public boolean checkEmailDuplication(String email) {
        return userRepository.findByEmail(email).isPresent();
    }
    public boolean checkNicknameDuplication(String nickname) {
        return userRepository.existsByNickname(nickname);
    }
}