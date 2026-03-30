package com.yeji.domain.compatibility.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yeji.domain.compatibility.dto.CompatibilityListItemResponse;
import com.yeji.domain.compatibility.dto.CompatibilityRequest;
import com.yeji.domain.compatibility.dto.CompatibilityResponse;
import com.yeji.domain.compatibility.entity.CompatibilityResult;
import com.yeji.domain.compatibility.repository.CompatibilityResultRepository;
import com.yeji.domain.compatibility.service.ai.CompatibilityAiClient;
import com.yeji.domain.saju.entity.SajuResult;
import com.yeji.domain.saju.repository.SajuResultRepository;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.global.jwt.AuthUser;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CompatibilityService {

    private final CompatibilityResultRepository resultRepository;
    private final UserRepository userRepository;
    private final SajuResultRepository sajuResultRepository;
    private final CompatibilityAiClient aiClient;
    private final ObjectMapper objectMapper;

    /**
     * AI Swagger (/v1/fortune/compatibility) 계약에 맞춰 호출:
     * {
     *   "person1": {"birth_date":"YYYY-MM-DD","gender":"M|F","name":"..."},
     *   "person2": {"birth_date":"YYYY-MM-DD","gender":"M|F","name":"..."}
     * }
     */
    @Transactional
    public CompatibilityResponse createCompatibility(AuthUser authUser, CompatibilityRequest request) {
        // 1) 요청자(User) 조회
        User requester = userRepository.findById(authUser.getUserId())
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));

        // 2) 내 사주 결과 조회 (saju_results.input_data에서 person1 구성)
        SajuResult mySaju = sajuResultRepository.findByUser_Id(requester.getId())
                .orElseThrow(() -> new IllegalArgumentException("내 사주 정보가 없습니다. (saju_results 없음)"));

        // 3) 상대 정보 검증
        if (request.getTargetName() == null || request.getTargetName().isBlank()) {
            throw new IllegalArgumentException("상대 이름(targetName)은 필수입니다.");
        }
        if (request.getBirthData() == null || request.getBirthData().isEmpty()) {
            throw new IllegalArgumentException("상대 생년월일 정보(birthData)는 필수입니다.");
        }
        requireKey(request.getBirthData(), "gender", "birthData.gender");
        requireKey(request.getBirthData(), "birth_date", "birthData.birth_date");

        // 4) AI Request Body 구성 (Swagger 계약 준수)
        Map<String, Object> aiReq = new LinkedHashMap<>();
        aiReq.put("person1", toAiPerson1FromSaju(mySaju));
        aiReq.put("person2", toAiPerson2FromRequest(request.getTargetName(), request.getBirthData()));

        // 5) AI 호출 (응답 JSON을 그대로 저장)
        JsonNode aiJson = aiClient.analyze(aiReq).block();
        if (aiJson == null) {
            throw new IllegalArgumentException("AI 응답이 비어있습니다.");
        }

        Map<String, Object> resultData = objectMapper.convertValue(aiJson, new TypeReference<Map<String, Object>>() {});

        // 6) DB 저장 (AI response JSON 그대로 JSONB 저장)
        CompatibilityResult result = CompatibilityResult.builder()
                .requester(requester)
                .targetId(request.getTargetUserId())       // 친구면 저장용(선택)
                .targetName(request.getTargetName())
                .targetBirthData(request.getBirthData())   // 원본 입력 저장(선택)
                .relationType(request.getRelationType())   // 필요 없으면 제거 가능
                .resultData(resultData)
                .build();

        CompatibilityResult saved = resultRepository.save(result);
        return CompatibilityResponse.from(saved);
    }

    // COMPAT-002 궁합 결과 목록
    public List<CompatibilityListItemResponse> getCompatibilityList(AuthUser authUser) {
        return resultRepository.findAllByRequester_IdOrderByCreatedAtDesc(authUser.getUserId())
                .stream()
                .map(CompatibilityListItemResponse::from)
                .collect(Collectors.toList());
    }

    // COMPAT-003 궁합 결과 상세
    public CompatibilityResponse getCompatibilityDetail(AuthUser authUser, Long resultId) {
        CompatibilityResult result = resultRepository.findById(resultId)
                .orElseThrow(() -> new IllegalArgumentException("결과를 찾을 수 없습니다."));

        if (!result.getRequester().getId().equals(authUser.getUserId())) {
            throw new IllegalArgumentException("본인의 결과만 조회할 수 있습니다.");
        }

        return CompatibilityResponse.from(result);
    }

    /**
     * saju_results.input_data 예시:
     * {"gender":"M","is_solar":true,"name_kor":"홍길동","birth_date":"1995-05-05","birth_time":"14:30"}
     *
     * AI로는 "name/gender/birth_date"만 전달합니다.
     */
    private Map<String, Object> toAiPerson1FromSaju(SajuResult mySaju) {
        Map<String, Object> input = castToMap(mySaju.getInputData());

        requireKey(input, "name_kor", "saju_results.input_data.name_kor");
        requireKey(input, "gender", "saju_results.input_data.gender");
        requireKey(input, "birth_date", "saju_results.input_data.birth_date");

        Map<String, Object> person1 = new LinkedHashMap<>();
        person1.put("name", input.get("name_kor"));
        person1.put("gender", input.get("gender"));
        person1.put("birth_date", input.get("birth_date"));
        return person1;
    }

    /**
     * request.birthData 예시:
     * {"gender":"M","is_solar":true,"birth_date":"1995-05-05","birth_time":"14:30"}
     *
     * AI로는 "name/gender/birth_date"만 전달합니다.
     */
    private Map<String, Object> toAiPerson2FromRequest(String targetName, Map<String, Object> birthData) {
        Map<String, Object> person2 = new LinkedHashMap<>();
        person2.put("name", targetName);
        person2.put("gender", birthData.get("gender"));
        person2.put("birth_date", birthData.get("birth_date"));
        return person2;
    }

    private void requireKey(Map<String, Object> map, String key, String label) {
        Object v = map.get(key);
        if (v == null || v.toString().isBlank()) {
            throw new IllegalArgumentException(label + " 값이 필요합니다.");
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> castToMap(Object obj) {
        if (obj == null) return new LinkedHashMap<>();
        if (obj instanceof Map<?, ?> m) return (Map<String, Object>) m;
        return objectMapper.convertValue(obj, new TypeReference<Map<String, Object>>() {});
    }
}
