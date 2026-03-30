package com.yeji.global.exception;

import com.yeji.domain.shop.exception.PaymentVerificationException;
import com.yeji.domain.wallet.exception.NotEnoughBalanceException;
import com.yeji.global.dto.ErrorResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {
    // @Valid 유효성 검사 실패 시(400 Bad Request)
    @ExceptionHandler(MethodArgumentNotValidException.class)
    protected ResponseEntity<ErrorResponse> handleValidationExceptions(MethodArgumentNotValidException ex) {
        StringBuilder message = new StringBuilder();
        // 첫 에러 메시지만 추출
        FieldError fieldError = ex.getBindingResult().getFieldError();
        if(fieldError != null) {
            message.append(fieldError.getDefaultMessage());
        } else {
            message.append("유효성 검사에 실패했습니다.");
        }
        log.warn("Validation Error : {}", message);
        return ErrorResponse.toResponseEntity(
                HttpStatus.BAD_REQUEST.value(),
                HttpStatus.BAD_REQUEST.name(),
                message.toString()
        );
    }

    // 잔액 부족 예외 처리 -> 400 Bad Request 반환
    @ExceptionHandler(NotEnoughBalanceException.class)
    public ResponseEntity<ErrorResponse> handleNotEnoughBalanceException(NotEnoughBalanceException e) {
        // 생성자(new) 대신 static 메서드 toResponseEntity 사용
        return ErrorResponse.toResponseEntity(
                HttpStatus.BAD_REQUEST.value(),
                "BAD_REQUEST",
                e.getMessage()
        );
    }

    // 결제 검증 실패 예외 처리 -> 400 Bad Request 반환
    @ExceptionHandler(PaymentVerificationException.class)
    public ResponseEntity<ErrorResponse> handlePaymentVerificationException(PaymentVerificationException e) {
        // 생성자(new) 대신 static 메서드 toResponseEntity 사용
        return ErrorResponse.toResponseEntity(
                HttpStatus.BAD_REQUEST.value(),
                "PAYMENT_VERIFICATION_FAILED",
                e.getMessage()
        );
    }

    // 일반적인 비즈니스 로직 예외(RuntimeException)
    // 이메일 중복 검사, 비밀번호 불일치 등
    @ExceptionHandler(RuntimeException.class)
    protected ResponseEntity<ErrorResponse> handleRuntimeException(RuntimeException ex) {
        log.warn("Business Logic Error", ex);

        String msg = ex.getMessage();
        if (msg == null || msg.isBlank()) {
            msg = "요청 처리 중 오류가 발생했습니다. (RuntimeException message is null)";
        }
        //상황에 따라 추후 401, 403 분기 가능
        return ErrorResponse.toResponseEntity(
                HttpStatus.BAD_REQUEST.value(),
                HttpStatus.BAD_REQUEST.name(),
                ex.getMessage()
        );
    }

    // 그 외 보든 에러(500 Internal Server Error)
    @ExceptionHandler(Exception.class)
    protected ResponseEntity<ErrorResponse> handleException(Exception ex) {
        log.error("Unexpected error : ", ex);
        return ErrorResponse.toResponseEntity(
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                HttpStatus.INTERNAL_SERVER_ERROR.name(),
                "서버 내부 오류가 발생했습니다. 관리자에게 문의하세요"
        );
    }
}
