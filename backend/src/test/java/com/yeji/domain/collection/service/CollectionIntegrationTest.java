package com.yeji.domain.collection.service;

import com.yeji.domain.collection.entity.Character;
import com.yeji.domain.collection.entity.CharacterGrade;
import com.yeji.domain.collection.entity.CharacterType;
import com.yeji.domain.collection.entity.UserCollection;
import com.yeji.domain.collection.repository.CharacterRepository;
import com.yeji.domain.collection.repository.UserCollectionRepository;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.global.jwt.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.print;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Transactional
class CollectionIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private CharacterRepository characterRepository;

    @Autowired
    private UserCollectionRepository userCollectionRepository;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    private User testUser;
    private Character eastCharacter;
    private Character westCharacter;
    private String accessToken; // 테스트용 액세스 토큰

    @BeforeEach
    void setUp() {
        // 1. 테스트 유저 생성
        testUser = User.builder()
                .email("test@example.com")
                .nickname("tester")
                .password("password")
                .provider("local")
                .build();
        testUser = userRepository.save(testUser);

        // 2. 테스트용 토큰 발급 (로그인 시뮬레이션)
        // JwtTokenProvider의 createAccessToken 메서드 시그니처에 맞춰 호출
        accessToken = jwtTokenProvider.createAccessToken(testUser.getEmail(), testUser.getId());

        // 3. 테스트 캐릭터 생성
        eastCharacter = Character.builder()
                .name("산신령")
                .type(CharacterType.EAST)
                .grade(CharacterGrade.RARE)
                .description("동양의 신")
                .isActive(true)
                .build();
        characterRepository.save(eastCharacter);

        westCharacter = Character.builder()
                .name("멀린")
                .type(CharacterType.WEST)
                .grade(CharacterGrade.LEGENDARY)
                .description("서양의 마법사")
                .isActive(true)
                .build();
        characterRepository.save(westCharacter);
    }

    @Test
    @DisplayName("전체 캐릭터 도감 조회 - 인증 불필요")
    void getAllCharacters() throws Exception {
        mockMvc.perform(get("/collection/characters")
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken))
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(jsonPath("$.data[0].name").exists());
    }

    @Test
    @DisplayName("보유 캐릭터 조회 - 토큰 인증 사용")
    void getMyCollections() throws Exception {
        // Given: 유저에게 캐릭터 지급
        UserCollection collection = UserCollection.builder()
                .user(testUser)
                .character(eastCharacter)
                .build();
        userCollectionRepository.save(collection);

        // When & Then
        mockMvc.perform(get("/collection/my-characters")
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)) // 헤더에 토큰 추가
                .andDo(print())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data").isArray())
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("캐릭터 장착 테스트 - 토큰 인증 사용")
    void equipCharacterTest() throws Exception {
        // 1. 유저가 캐릭터 보유 처리
        userCollectionRepository.save(UserCollection.builder().user(testUser).character(eastCharacter).build());

        // 2. 요청 DTO 생성 (JSON 문자열)
        String requestBody = String.format("{\"type\":\"EAST\", \"characterId\":%d}", eastCharacter.getId());

        // 3. API 호출
        mockMvc.perform(patch("/collection/equip")
                        .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken) // 헤더에 토큰 추가
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(requestBody))
                .andDo(print())
                .andExpect(status().isOk());
    }
}