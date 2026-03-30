package com.yeji.global.external.pg;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@Profile("test") // 로컬 및 테스트 환경에서만 동작
// 지금은 프로필 설정 없이 기본 빈으로 등록하여 항상 동작하게 함 (추후 PortOnePgClient 구현 시 교체)
public class StubPgClient implements PgClient {

    @Override
    public boolean validatePayment(String paymentKey, String orderId, int amount) {
        log.info("[Stub PG] 검증 요청 - paymentKey: {}, orderId: {}, amount: {}", paymentKey, orderId, amount);

        // 테스트 시나리오: paymentKey가 "FAIL_"로 시작하면 검증 실패 처리
        if (paymentKey.startsWith("FAIL_")) {
            log.warn("[Stub PG] 검증 실패 시뮬레이션");
            return false;
        }

        // 그 외에는 무조건 성공 (금액 위변조 없다고 가정)
        log.info("[Stub PG] 검증 성공");
        return true;
    }
}