package com.yeji.global.auth.oauth.handler;

import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.global.jwt.JwtTokenProvider;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.util.UriComponentsBuilder;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Slf4j
@Component
@RequiredArgsConstructor
public class OAuth2LoginSuccessHandler extends SimpleUrlAuthenticationSuccessHandler {
    private final JwtTokenProvider jwtTokenProvider;
    private final RedisTemplate<String, String> redisTemplate;
    private final UserRepository userRepository;

    @Value("${frontend.url:http://localhost:3000}")
    private String frontendUrl;

    @Override
    @SuppressWarnings("unchecked")
    public void onAuthenticationSuccess(HttpServletRequest request, HttpServletResponse response, Authentication authentication) throws IOException, ServletException {
        OAuth2AuthenticationToken authToken = (OAuth2AuthenticationToken) authentication;
        OAuth2User oAuth2User = authToken.getPrincipal();
        Map<String, Object> attributes = oAuth2User.getAttributes();
        String registrationId = authToken.getAuthorizedClientRegistrationId();

        // 이메일 추출
        String email = null;
        if ("google".equals(registrationId)) {
            email = (String) attributes.get("email");
        } else if ("kakao".equals(registrationId)) {
            Map<String, Object> kakaoAccount = (Map<String, Object>) attributes.get("kakao_account");
            email = (String) kakaoAccount.get("email");
        } else if ("naver".equals(registrationId)) {
            Map<String, Object> responseData = (Map<String, Object>) attributes.get("response");
            email = (String) responseData.get("email");
        }

        // DB에서 유저 조회
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found. But OAuth2 was successful."));

        // JWT Token 생성
        String accessToken = jwtTokenProvider.createAccessToken(user.getEmail(), user.getId());
        String refreshToken = jwtTokenProvider.createRefreshToken(user.getEmail());

        // Refresh Token Redis 저장
        redisTemplate.opsForValue().set(
                "RT:" + user.getEmail(),
                refreshToken,
                7,
                TimeUnit.DAYS
        );

        // 토큰과 함께 frontend로 redirect
        String targetUrl = UriComponentsBuilder.fromUriString(frontendUrl + "/oauth/callback")
                .queryParam("accessToken", accessToken)
                .queryParam("refreshToken", refreshToken)
                .build().toUriString();

        getRedirectStrategy().sendRedirect(request, response, targetUrl);
    }
}
