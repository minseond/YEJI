package com.yeji.global.auth.oauth.service;

import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.global.auth.oauth.info.OAuth2UserInfo;
import com.yeji.global.auth.oauth.info.impl.GoogleOAuth2UserInfo;
import com.yeji.global.auth.oauth.info.impl.KakaoOAuth2UserInfo;
import com.yeji.global.auth.oauth.info.impl.NaverOAuth2UserInfo;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.DefaultOAuth2User;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.Map;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService {
    private final UserRepository userRepository;

    @Override
    @Transactional
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        // 소셜 로그인 API를 통해 유저 정보 가져오기
        OAuth2User oAuth2User = super.loadUser(userRequest);

        // 어떤 서비스인지 확인(구글, 카카오, 네이버)
        String registrationId = userRequest.getClientRegistration().getRegistrationId();

        // 유저 정보 객체 생성
        OAuth2UserInfo userInfo = null;
        if (registrationId.equals("google")) {
            userInfo = new GoogleOAuth2UserInfo((oAuth2User.getAttributes()));
        } else if (registrationId.equals("naver")) {
            userInfo = new NaverOAuth2UserInfo((oAuth2User.getAttributes()));
        } else if (registrationId.equals("kakao")) {
            userInfo = new KakaoOAuth2UserInfo((oAuth2User.getAttributes()));
        } else {
            throw new OAuth2AuthenticationException("지원하지 않는 소셜 로그인 서비스입니다");
        }

        // 이메일 없는 경우 예외 처리
        String email = userInfo.getEmail();
        if (email == null) {
            throw new OAuth2AuthenticationException("이메일 정보가 필요합니다.");
        }

        // 회원가입 또는 업데이트
        User user = saveOrUpdate(userInfo);

        // SecurityContext에 저장할 User 객체 반환
        Map<String, Object> attributes = oAuth2User.getAttributes();

        return new DefaultOAuth2User(
                Collections.singleton(() -> "ROLE_USER"),
                attributes,
                userRequest.getClientRegistration().getProviderDetails().getUserInfoEndpoint().getUserNameAttributeName()
        );
    }

    private User saveOrUpdate(OAuth2UserInfo userInfo) {
        Optional<User> userOptional = userRepository.findByEmail(userInfo.getEmail());

        if (userOptional.isPresent()) {
            // 이미 존재하는 회원이면 정보 업데이트(프사, 닉네임)
            return userOptional.get().updateSocialInfo(userInfo.getName(), userInfo.getProfileImageUrl());
        } else {
            // 신규 회원이면 저장
            User user = User.builder()
                    .email(userInfo.getEmail())
                    .nickname(userInfo.getName())
                    .provider(userInfo.getProvider())
                    .profileImg(userInfo.getProfileImageUrl())
                    .isSolar(true) // 일단 기본값은 양력으로
                    .build();
            return userRepository.save(user);
        }
    }
}
