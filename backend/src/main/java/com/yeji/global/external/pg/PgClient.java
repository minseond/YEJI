package com.yeji.global.external.pg;

// PG사 결제 검증을 위한 인터페이스
public interface PgClient {
    // 결제 검증 메서드
    // paymentKey: PG사에서 발급한 결제 고유 번호 (imp_uid)
    // orderId: 우리가 생성한 주문 번호
    // amount: 결제되어야 하는 금액
    // return: 검증 성공 여부
    boolean validatePayment(String paymentKey, String orderId, int amount);
}