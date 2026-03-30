package com.yeji.domain.shop.service;

import com.yeji.domain.shop.dto.PaymentCreateRequest;
import com.yeji.domain.shop.dto.PaymentCreateResponse;
import com.yeji.domain.shop.entity.Payment;
import com.yeji.domain.shop.entity.Product;
import com.yeji.domain.shop.exception.PaymentVerificationException; // [수정] 커스텀 예외 Import
import com.yeji.domain.shop.repository.PaymentRepository;
import com.yeji.domain.shop.repository.ProductRepository;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.domain.wallet.repository.UserWalletRepository;
import com.yeji.domain.wallet.service.WalletService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.transaction.annotation.Transactional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@SpringBootTest
@ActiveProfiles("test") // StubPgClient가 동작하도록 test 프로필 활성화
@Transactional
class ShopIntegrationTest {

    @Autowired private ShopService shopService;
    @Autowired private WalletService walletService;
    @Autowired private UserRepository userRepository;
    @Autowired private ProductRepository productRepository;
    @Autowired private PaymentRepository paymentRepository;
    @Autowired private UserWalletRepository userWalletRepository;

    private User user;
    private Product product;

    @BeforeEach
    void setUp() {
        // 1. 테스트 유저 생성
        user = userRepository.save(User.builder()
                .email("shopper@example.com")
                .nickname("shopper")
                .provider("EMAIL")
                .isSolar(true)
                .build());

        // 2. 지갑 생성 (필수)
        walletService.createWallet(user.getId());

        // 3. 테스트 상품 생성
        product = productRepository.save(new Product("Test 100 FP", 1000, 100, true));
    }

    @Test
    @DisplayName("결제 프로세스 정상 작동 (생성 -> 검증 -> 포인트 지급)")
    void payment_Process_Success() {
        // Given
        PaymentCreateRequest request = new PaymentCreateRequest();
        ReflectionTestUtils.setField(request, "productId", product.getId());

        // When 1: 결제(주문) 생성
        PaymentCreateResponse response = shopService.createPayment(user.getId(), request);
        String orderId = response.getOrderId();

        // Then 1: 주문 생성 확인 (PENDING)
        Payment payment = paymentRepository.findById(orderId).orElseThrow();
        assertThat(payment.getStatus()).isEqualTo("PENDING");
        assertThat(payment.getAmount()).isEqualTo(1000);

        // When 2: 결제 검증 요청 (StubPgClient는 FAIL_ 로 시작하지 않으면 성공 처리)
        shopService.verifyPayment(user.getId(), orderId, "imp_success_123");

        // Then 2: 검증 후 상태 확인 (PAID)
        Payment paidPayment = paymentRepository.findById(orderId).orElseThrow();
        assertThat(paidPayment.getStatus()).isEqualTo("PAID");

        // Then 3: 포인트 지급 확인 (100FP)
        int balance = userWalletRepository.findById(user.getId()).get().getBalance();
        assertThat(balance).isEqualTo(100);
    }

    @Test
    @DisplayName("결제 검증 실패 시 상태 FAILED 변경 및 에러 발생")
    void payment_Process_Fail() {
        // Given
        PaymentCreateRequest request = new PaymentCreateRequest();
        ReflectionTestUtils.setField(request, "productId", product.getId());
        String orderId = shopService.createPayment(user.getId(), request).getOrderId();

        // When & Then: 검증 요청 (StubPgClient 로직상 FAIL_ 접두사 사용 시 실패)
        assertThatThrownBy(() ->
                shopService.verifyPayment(user.getId(), orderId, "FAIL_KEY_123")
        ).isInstanceOf(PaymentVerificationException.class) // [수정] 구체적인 예외 클래스 확인
                .hasMessageContaining("결제 검증에 실패");

        // Then: 상태 FAILED 확인
        Payment failedPayment = paymentRepository.findById(orderId).orElseThrow();
        assertThat(failedPayment.getStatus()).isEqualTo("FAILED");

        // Then: 포인트 미지급 확인 (0원)
        int balance = userWalletRepository.findById(user.getId()).get().getBalance();
        assertThat(balance).isEqualTo(0);
    }
}