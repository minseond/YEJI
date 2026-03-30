package com.yeji.domain.luck;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yeji.domain.luck.dto.LuckTransferRequest;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.global.jwt.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.lang.reflect.Field;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class LuckIntegrationTest {

    @Autowired MockMvc mockMvc;
    @Autowired UserRepository userRepository;
    @Autowired JwtTokenProvider jwtTokenProvider;
    @Autowired ObjectMapper objectMapper;

    User sender;
    User receiver;
    String accessToken;

    @BeforeEach
    void setUp() {
        // 테스트용 유저 생성
        sender = User.builder()
                .email("sender@test.com")
                .nickname("sender")
                .provider("TEST")
                .build();
        userRepository.save(sender);

        receiver = User.builder()
                .email("receiver@test.com")
                .nickname("receiver")
                .provider("TEST")
                .build();
        userRepository.save(receiver);

        accessToken = jwtTokenProvider.createAccessToken(sender.getEmail(), sender.getId());
    }

    @Test
    @DisplayName("LUCK-001: 운세 전송 테스트")
    void sendLuckTest() throws Exception {
        // Given
        // Reflection을 사용하여 DTO 생성 (NoArgsConstructor만 있는 경우)
        LuckTransferRequest request = new LuckTransferRequest();
        setField(request, "receiverId", receiver.getId());
        setField(request, "transferType", "BLESS");
        setField(request, "message", "행운을 빕니다!");
        setField(request, "characterType", 1);

        // When & Then
        mockMvc.perform(post("/luck/transfers")
                        .header("Authorization", "Bearer " + accessToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.senderId").value(sender.getId()))
                .andExpect(jsonPath("$.data.message").value("행운을 빕니다!"));
    }

    // Helper for setting private fields
    private void setField(Object object, String fieldName, Object value) throws Exception {
        Field field = object.getClass().getDeclaredField(fieldName);
        field.setAccessible(true);
        field.set(object, value);
    }
}