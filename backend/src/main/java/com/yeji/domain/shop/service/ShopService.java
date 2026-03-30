package com.yeji.domain.shop.service;

import com.yeji.domain.shop.dto.PaymentCreateRequest;
import com.yeji.domain.shop.dto.PaymentCreateResponse;
import com.yeji.domain.shop.dto.PaymentHistoryResponse;
import com.yeji.domain.shop.dto.ProductResponse;
import com.yeji.domain.shop.entity.Payment;
import com.yeji.domain.shop.entity.Product;
import com.yeji.domain.shop.exception.PaymentVerificationException;
import com.yeji.domain.shop.repository.PaymentRepository;
import com.yeji.domain.shop.repository.ProductRepository;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.domain.wallet.service.WalletService;
import com.yeji.global.external.pg.PgClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ShopService {

    private final ProductRepository productRepository;
    private final PaymentRepository paymentRepository;
    private final UserRepository userRepository;
    private final WalletService walletService;
    private final PgClient pgClient;

    // 상품 목록 조회
    public List<ProductResponse> getProducts() {
        return productRepository.findAllByIsActiveTrue().stream()
                .map(ProductResponse::new)
                .toList();
    }

    // 결제 생성 (주문서 발급)
    @Transactional
    public PaymentCreateResponse createPayment(Long userId, PaymentCreateRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        Product product = productRepository.findById(request.getProductId())
                .orElseThrow(() -> new RuntimeException("Product not found"));

        // 주문 번호 생성
        String orderId = "ORD-" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd")) + "-" + UUID.randomUUID().toString().substring(0, 8);

        log.info("[ShopService] 결제 생성 요청 - User: {}, OrderId: [{}]", userId, orderId);

        // 결제 정보 저장 (PENDING)
        Payment payment = Payment.builder()
                .orderId(orderId)
                .user(user)
                .product(product)
                .amount(product.getPriceKrw())
                .status("PENDING")
                .build();

        paymentRepository.save(payment);
        paymentRepository.flush(); // 즉시 DB 반영

        return PaymentCreateResponse.builder()
                .orderId(orderId)
                .amount(product.getPriceKrw())
                .orderName(product.getName())
                .build();
    }

    // 결제 검증 및 완료 처리
    @Transactional
    public void verifyPayment(Long userId, String orderId, String paymentKey) {
        log.info("[ShopService] 검증 요청 시작 - User: {}, 요청된 OrderId: [{}]", userId, orderId);

        Payment payment = paymentRepository.findById(orderId)
                .orElseThrow(() -> {
                    // [디버깅] 조회 실패 시, 현재 DB에 있는 데이터 목록을 출력하여 원인 파악
                    log.error("❌ 주문 정보를 찾을 수 없습니다! (요청 ID: [{}])", orderId);
                    log.error("📋 === 현재 DB에 저장된 주문 목록 (최대 10개) ===");
                    List<Payment> allPayments = paymentRepository.findAll();
                    if (allPayments.isEmpty()) {
                        log.error(">> DB가 비어있습니다. (트랜잭션 롤백, 혹은 데이터 초기화 의심)");
                    } else {
                        allPayments.stream().limit(10).forEach(p ->
                                log.error(">> 저장된 ID: [{}], 상태: [{}], 생성일: [{}]", p.getOrderId(), p.getStatus(), p.getCreatedAt())
                        );
                    }
                    return new RuntimeException("주문 정보를 찾을 수 없습니다.");
                });

        if (!payment.getUser().getId().equals(userId)) {
            throw new PaymentVerificationException("주문자와 요청자가 일치하지 않습니다.");
        }

        if (!"PENDING".equals(payment.getStatus())) {
            throw new PaymentVerificationException("이미 처리되었거나 취소된 주문입니다.");
        }

        // PG사 검증
        boolean isValid = pgClient.validatePayment(paymentKey, orderId, payment.getAmount());

        if (isValid) {
            payment.complete("PORTONE"); // PG사 이름
            walletService.chargePoint(userId, payment.getProduct().getFpAmount(), "상품 구매: " + payment.getProduct().getName());
            log.info("[ShopService] 결제 검증 및 포인트 지급 성공! OrderId: {}", orderId);
        } else {
            payment.fail();
            log.error("[ShopService] PG사 검증 실패");
            throw new PaymentVerificationException("결제 검증에 실패했습니다. (금액 불일치 또는 결제 미완료)");
        }
    }

    // 결제 내역 조회
    public List<PaymentHistoryResponse> getPaymentHistory(Long userId) {
        return paymentRepository.findAllByUserIdOrderByCreatedAtDesc(userId).stream()
                .map(PaymentHistoryResponse::new)
                .toList();
    }

    // 개발용 초기 데이터
    @Transactional
    public void initProducts() {
        if(productRepository.count() == 0) {
            productRepository.save(new Product("100 FP", 1000, 100, true));
            productRepository.save(new Product("550 FP", 5000, 550, true));
            productRepository.save(new Product("1200 FP", 10000, 1200, true));
        }
    }
}