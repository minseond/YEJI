package com.yeji.domain.user.service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class EmailService {

    private final JavaMailSender javaMailSender;
    private final RedisTemplate<String, String> redisTemplate;

    private static final String AUTH_CODE_PREFIX = "EmailAuth:";
    private static final long AUTH_CODE_EXPIRE_TIME = 300; // 5분

    // 이메일 인증 코드 발송
    public void sendVerificationCode(String email) {
        String code = createRandomCode();

        try {
            MimeMessage message = javaMailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setTo(email);
            helper.setSubject("[Yeji] 이메일 인증 코드입니다.");
            helper.setText(buildEmailContent(code), true);

            javaMailSender.send(message);

            // Redis에 인증 코드 저장 (유효기간 5분)
            redisTemplate.opsForValue().set(
                    AUTH_CODE_PREFIX + email,
                    code,
                    AUTH_CODE_EXPIRE_TIME,
                    TimeUnit.SECONDS
            );

            log.info("Sent verification code to: {}", email);

        } catch (MessagingException e) {
            log.error("Failed to send email", e);
            throw new RuntimeException("이메일 발송에 실패했습니다.");
        }
    }

    // 인증 코드 검증
    public boolean verifyCode(String email, String code) {
        String savedCode = redisTemplate.opsForValue().get(AUTH_CODE_PREFIX + email);
        return savedCode != null && savedCode.equals(code);
    }

    // 검증 후 코드 삭제 (재사용 방지)
    public void deleteCode(String email) {
        redisTemplate.delete(AUTH_CODE_PREFIX + email);
    }

    private String createRandomCode() {
        SecureRandom random = new SecureRandom();
        StringBuilder key = new StringBuilder();
        for (int i = 0; i < 6; i++) {
            key.append(random.nextInt(10));
        }
        return key.toString();
    }

    private String buildEmailContent(String code) {
        return "<div style='margin:10px;'>" +
                "<h1>Yeji 이메일 인증</h1>" +
                "<br>" +
                "<p>아래 코드를 입력하여 본인 인증을 완료해주세요.</p>" +
                "<br>" +
                "<div style='border:1px solid black; font-family:verdana; padding:10px;'>" +
                "<h3 style='color:blue;'>회원가입/비밀번호 변경 인증 코드</h3>" +
                "<div style='font-size:130%'>" + code + "</div>" +
                "</div>" +
                "<br/>" +
                "</div>";
    }
}