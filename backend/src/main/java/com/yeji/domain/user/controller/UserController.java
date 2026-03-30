package com.yeji.domain.user.controller;

import com.yeji.domain.user.dto.*;
import com.yeji.domain.user.service.UserService;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@Tag(name = "User API", description = "유저 정보 조회 및 수정 API")
@RestController
@RequestMapping("/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    // USER-004 회원가입
    @Operation(summary = "회원가입", description = "이메일 기반 자체 회원가입을 진행합니다.")
    @PostMapping("/signup")
    public ResponseEntity<UserResponse> signup(@RequestBody @Valid UserSignupRequest request) {
        return ResponseEntity.ok(userService.signup(request));
    }

    // USER-009 (회원가입 전용) 이메일 인증코드 발송
    @Operation(summary = "이메일 인증코드 발송", description = "회원가입/비밀번호 찾기를 위한 인증코드를 이메일로 전송합니다.")
    @PostMapping("/email/send")
    public ResponseEntity<Void> sendEmailVerification(@RequestBody @Valid EmailRequest request) {
        userService.sendEmailVerification(request);
        return ResponseEntity.ok().build();
    }

    // USER-001 로그인
    @Operation(summary = "로그인", description = "이메일과 비밀번호로 로그인하여 JWT 토큰을 발급받습니다.")
    @PostMapping("/login")
    public ResponseEntity<TokenResponse> login(@RequestBody @Valid UserLoginRequest request) {
        return ResponseEntity.ok(userService.login(request));
    }

    // USER-002 로그아웃
    @Operation(summary = "로그아웃", description = "Redis에서 리프레시 토큰을 삭제하여 로그아웃 처리합니다.")
    @PostMapping("/logout")
    public ResponseEntity<Void> logout(@RequestBody TokenRefreshRequest request) {
        userService.logout(request.getRefreshToken());
        return ResponseEntity.ok().build();
    }

    // USER-005 토큰 재발급
    @Operation(summary = "토큰 재발급", description = "RefreshToken을 이용하여 AccessToken을 재발급합니다.")
    @PostMapping("/token/refresh")
    public ResponseEntity<TokenResponse> refreshToken(@RequestBody TokenRefreshRequest request) {
        return ResponseEntity.ok(userService.reissue(request));
    }

    // USER-003 상세조회
    @Operation(summary = "유저 상세 조회", description = "유저 ID(PK)를 통해 상세 정보를 조회합니다.")
    @GetMapping("/{userId}")
    public ResponseEntity<UserResponse> getUserInfo(@PathVariable Long userId) {
        return ResponseEntity.ok(userService.getUserInfo(userId));
    }

    // USER-006 회원 정보 수정
    @Operation(summary = "회원 정보 수정", description = "로그인한 사용자의 정보를 수정합니다.")
    @PatchMapping("/me")
    public ResponseEntity<UserResponse> updateProfile(
            @AuthenticationPrincipal AuthUser authUser, // UserDetails -> AuthUser 변경 (ID 확보용)
            @RequestBody UserUpdateRequest request) {
        // userId를 Service로 전달하도록 변경
        return ResponseEntity.ok(userService.updateProfile(authUser.getUserId(), request));
    }

    // USER-007 회원 탈퇴
    @Operation(summary = "회원 탈퇴", description = "인증 코드를 확인한 후 탈퇴 처리합니다.")
    @DeleteMapping("/me")
    public ResponseEntity<Void> withdraw(
            @AuthenticationPrincipal AuthUser authUser,
            @RequestBody UserWithdrawRequest request
    ) {
        userService.withdraw(authUser.getUserId(), request.getCode());
        return ResponseEntity.ok().build();
    }

    // 회원 탈퇴를 위한 인증 코드 발송
    @Operation(summary = "탈퇴 인증 코드 발송", description = "회원 탈퇴를 위해 이메일로 인증 코드를 발송합니다.")
    @PostMapping("/me/withdraw/send")
    public ResponseEntity<Void> sendWithdrawVerification(@AuthenticationPrincipal AuthUser authUser) {
        userService.sendWithdrawVerification(authUser.getUserId());
        return ResponseEntity.ok().build();
    }



    // USER-009 이메일 인증코드 검증
    @Operation(summary = "이메일 인증코드 검증", description = "입력한 코드가 맞는지 확인합니다.")
    @PostMapping("/email/verify")
    public ResponseEntity<Boolean> verifyEmail(@RequestBody @Valid EmailVerificationRequest request) {
        return ResponseEntity.ok(userService.verifyEmail(request));
    }

    // USER-008 비밀번호 재설정
    @Operation(summary = "비밀번호 재설정", description = "이메일 인증코드가 일치하면 새로운 비밀번호로 변경합니다.")
    @PostMapping("/password/reset")
    public ResponseEntity<Void> resetPassword(@RequestBody @Valid PasswordResetRequest request) {
        userService.resetPassword(request);
        return ResponseEntity.ok().build();
    }

    // SET-001 설정 조회
    @Operation(summary = "설정 조회", description = "유저의 환경설정(알림, 사운드 등)을 조회합니다.")
    @GetMapping("/{userId}/settings")
    public ResponseEntity<UserSettingsResponse> getSettings(@PathVariable Long userId) {
        return ResponseEntity.ok(userService.getSettings(userId));
    }

    // SET-002 설정 수정
    @Operation(summary = "설정 수정", description = "유저의 환경설정을 수정합니다.")
    @PatchMapping("/{userId}/settings")
    public ResponseEntity<UserSettingsResponse> updateSettings(
            @PathVariable Long userId,
            @RequestBody UserSettingsUpdateRequest request) {
        return ResponseEntity.ok(userService.updateSettings(userId, request));
    }

    // 비밀번호 검증 (회원 정보 수정 전 단계)
    @Operation(summary = "비밀번호 검증", description = "회원 정보 수정 전 비밀번호가 일치하는지 확인합니다.")
    @PostMapping("/verify-password")
    public ResponseEntity<Boolean> verifyPassword(
            @AuthenticationPrincipal AuthUser authUser,
            @Valid @RequestBody PasswordCheckRequest request
    ) {
        userService.verifyPassword(authUser.getUserId(), request.getPassword());
        return ResponseEntity.ok(true);
    }

    // 이메일 중복 확인(회원가입 시)
    @GetMapping("/check-email")
    public ResponseEntity<Boolean> checkEmail(@RequestParam String email) {
        return ResponseEntity.ok(userService.checkEmailDuplication(email));
    }
    // 닉네임 중복 확인(회원가입 시)
    @GetMapping("/check-nickname")
    public ResponseEntity<Boolean> checkNickname(@RequestParam String nickname) {
        return ResponseEntity.ok(userService.checkNicknameDuplication(nickname));
    }
}