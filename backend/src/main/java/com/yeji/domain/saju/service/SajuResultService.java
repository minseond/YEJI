package com.yeji.domain.saju.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yeji.domain.saju.dto.response.SajuAnalyzeResponse;
import com.yeji.domain.saju.entity.SajuResult;
import com.yeji.domain.saju.repository.SajuResultRepository;
import com.yeji.domain.saju.service.ai.SajuAiClient;
import com.yeji.domain.saju.service.ai.dto.SajuAiRequest;
import com.yeji.domain.saju.service.ai.validation.FortuneV2ResponseValidator;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class SajuResultService {

    private static final ZoneId KST = ZoneId.of("Asia/Seoul");
    private static final DateTimeFormatter REQ_TS = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");
    private static final SecureRandom RND = new SecureRandom();

    private final SajuResultRepository sajuResultRepository;
    private final UserRepository userRepository;
    private final SajuAiClient sajuAiClient;
    private final ObjectMapper objectMapper;

    //저장된 사주 결과 있으면 반환 (유저당 1개 유지)
    public SajuAnalyzeResponse getCurrentResult(Long userId) {
        SajuResult result = sajuResultRepository.findByUser_Id(userId)
                .orElseThrow(() -> new RuntimeException("사주 결과를 찾을 수 없습니다."));
        return SajuAnalyzeResponse.ok(
                result.getId(),
                OffsetDateTime.now(KST),
                "db",
                result.getAnalysisResult()
        );
    }

    //분석 요청 및 저장
    //request body 없이 호출 -> 어차피 user db에 있는 정보 그대로 가져오니까
    // AI 요청: {request_id, user_context, input_data}
    // AI 응답: dummyFortuneV2 JSON 통으로 저장/반환
    @Transactional
    public SajuAnalyzeResponse analyzeAndSave(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("유저를 찾을 수 없습니다."));

        //input_data (user db에서 받아온 정보)
        JsonNode inputData = buildInputDataSnap(user); //input_data를 유저 db 기반으로 구성

        //request_id (추후에 제거해도 됨)
        String requestId = buildRequestId(userId);

        //user_context
        String locale = "ko-KR";
        String timezone = "Asia/Seoul";

        //AI 요청 DTO
        SajuAiRequest aiRequest = SajuAiRequest.of(
                requestId,
                userId,
                locale,
                timezone,
                inputData
        );

        // AI 호출 (결과는 dummyFortuneV2 형식에 맞춰서)
        JsonNode analysisResult = sajuAiClient.analyze(aiRequest);
        System.out.println("[SAJU AI RAW] " + analysisResult.toString());

        //최소 스키마 검증 - 프론트 깨짐 방지
        FortuneV2ResponseValidator.validateOrThrow(analysisResult);

        //AI 분석 결과 받아와서 DB 저장 (유저당 1개 유지 - 추가하면 덮어쓰기)
        SajuResult result = sajuResultRepository.findByUser_Id(userId)
                .map(existing -> {
                    existing.overwrite(inputData, analysisResult);
                    return existing;
                })
                //없으면 일단 기본값으로 채우기
                .orElseGet(() -> SajuResult.builder()
                        .user(user)
                        .inputData(inputData)
                        .analysisResult(analysisResult)
                        .status("KEEP")
                        .score(0)
                        .build()
                );

        SajuResult saved = sajuResultRepository.save(result);

        return SajuAnalyzeResponse.ok(
                saved.getId(),
                OffsetDateTime.now(KST),
                "ai",
                saved.getAnalysisResult()
        );
    }

    //user db에서 받아올 값들 그대로 input_data 생성
    private JsonNode buildInputDataSnap(User user) {
        Map<String, Object> snap = new LinkedHashMap<>();
        snap.put("name_kor", user.getNameKor());
        snap.put("name_chn", user.getNameChn());
        snap.put("birth_date", user.getBirthDate() != null ? user.getBirthDate().toString() : null);
        snap.put("birth_time", user.getBirthTime() != null ? user.getBirthTime().toString() : null);
        snap.put("gender", user.getGender());
        snap.put("is_solar", user.isSolar());
        return objectMapper.valueToTree(snap);
    }

    private String buildRequestId(Long userId) {
        String ts = OffsetDateTime.now(KST).format(REQ_TS);
        String rand = Integer.toHexString(RND.nextInt()).replace("-", "");
        if (rand.length() > 6) rand = rand.substring(0, 6);
        return "req_" + ts + "_" + userId + "_" + rand;
    }

    //이렇게 보내면? AI로 실제로 나가는 JSON 형태
    /*
       {
       "request_id": "req_20260129_153012_7_ab12cd",
       "user_context": { "user_id": 7, "locale": "ko-KR", "timezone": "Asia/Seoul" },
       "input_data": {
       "name_kor": "홍길동",
       "name_chn": "洪吉童",
       "birth_date": "1999-03-15",
       "birth_time": "14:30",
       "gender": "M",
       "is_solar": true
         }
      }
     */

}
