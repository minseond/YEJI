package com.yeji.global.auth.oauth.info;

public interface OAuth2UserInfo {
    String getProvider(); // google, kakao, naver
    String getProviderId(); // 소셜 ID
    String getEmail();
    String getName();
    String getProfileImageUrl();
}