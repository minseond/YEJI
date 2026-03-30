package com.yeji.global.external.pg;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Profile;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Component
@Primary
@Profile("!test") // test 프로필이 아닐 때만 빈 등록
@RequiredArgsConstructor
public class PortOnePgClient implements PgClient {

    @Value("${portone.api.key}")
    private String apiKey;

    @Value("${portone.api.secret}")
    private String apiSecret;

    private final RestTemplate restTemplate = new RestTemplate();
    private static final String PORTONE_URL = "https://api.iamport.kr";

    @Override
    public boolean validatePayment(String paymentKey, String orderId, int amount) {
        try {
            // 1. 아임포트 API 토큰 발급
            String accessToken = getAccessToken();

            // 2. 결제 정보 단건 조회
            PortOnePaymentResponse paymentInfo = getPaymentInfo(paymentKey, accessToken);

            // 3. 검증 로직
            if (paymentInfo != null && "paid".equals(paymentInfo.getStatus())) {
                if (paymentInfo.getAmount() == amount && orderId.equals(paymentInfo.getMerchantUid())) {
                    log.info("[PortOne] 검증 성공: orderId={}, amount={}", orderId, amount);
                    return true;
                } else {
                    log.warn("[PortOne] 금액 또는 주문번호 불일치: realAmount={}, expectedAmount={}", paymentInfo.getAmount(), amount);
                }
            } else {
                log.warn("[PortOne] 결제 상태가 paid가 아님: status={}", paymentInfo != null ? paymentInfo.getStatus() : "null");
            }

        } catch (HttpClientErrorException e) {
            log.error("[PortOne] API 호출 오류: status={}, response={}", e.getStatusCode(), e.getResponseBodyAsString());
        } catch (Exception e) {
            log.error("[PortOne] 결제 검증 중 알 수 없는 오류 발생", e);
        }
        return false;
    }

    private String getAccessToken() {
        // [디버깅 로그] 실제 전송되는 키 값 확인 (보안상 앞 4자리만 출력)
        String maskedKey = (apiKey != null && apiKey.length() > 4) ? apiKey.substring(0, 4) + "****" : "null";
        log.info("[PortOne] 토큰 발급 요청 시작 - Key: {}", maskedKey);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, String> body = new HashMap<>();
        body.put("imp_key", apiKey);
        body.put("imp_secret", apiSecret);

        HttpEntity<Map<String, String>> request = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<PortOneTokenResponse> response = restTemplate.postForEntity(
                    PORTONE_URL + "/users/getToken",
                    request,
                    PortOneTokenResponse.class
            );

            if (response.getBody() == null || response.getBody().getResponse() == null) {
                throw new RuntimeException("PortOne Access Token 발급 실패 (응답 없음)");
            }

            return response.getBody().getResponse().getAccessToken();

        } catch (HttpClientErrorException.Unauthorized e) {
            log.error("❌ [PortOne] 401 Unauthorized: API Key 또는 Secret이 잘못되었습니다.");
            throw e; // 상위에서 잡아서 처리
        }
    }

    private PortOnePaymentResponse getPaymentInfo(String impUid, String accessToken) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(accessToken);

        HttpEntity<Void> request = new HttpEntity<>(headers);

        // 260126부로 PortOne 측에서 "include_sandbox" 파라미터를 추가 요청함.
        ResponseEntity<PortOnePaymentResultResponse> response = restTemplate.exchange(
                PORTONE_URL + "/payments/" + impUid + "?include_sandbox=true",
                HttpMethod.GET,
                request,
                PortOnePaymentResultResponse.class
        );

        if (response.getBody() == null) {
            return null;
        }
        return response.getBody().getResponse();
    }

    @Getter @NoArgsConstructor
    static class PortOneTokenResponse {
        private TokenData response;
        @Getter @NoArgsConstructor
        static class TokenData {
            @JsonProperty("access_token")
            private String accessToken;
        }
    }

    @Getter @NoArgsConstructor
    static class PortOnePaymentResultResponse {
        private PortOnePaymentResponse response;
    }

    @Getter @NoArgsConstructor
    static class PortOnePaymentResponse {
        private String status;
        private Integer amount;
        @JsonProperty("merchant_uid")
        private String merchantUid;
    }
}