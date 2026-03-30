package com.yeji.domain.compatibility.dto;

import com.yeji.domain.compatibility.entity.CompatibilityResult;
import lombok.Builder;
import lombok.Getter;
// Map 임포트 필수
import java.util.Map;

@Getter
@Builder
public class CompatibilityResponse {
    private Long id;
    private Long targetId;
    private String targetName;
    private String relationType;

    // 점수 필드
    private ScoreInfo score;

    // 필요 시 원본 유지
    private Map<String, Object> resultData;

    private java.time.LocalDateTime createdAt;

    public static CompatibilityResponse from(CompatibilityResult result) {
        return CompatibilityResponse.builder()
                .id(result.getId())
                .targetId(result.getTargetId())
                .targetName(result.getTargetName())
                .relationType(result.getRelationType())
                .resultData(result.getResultData())
                // 여기서 변환 수행
                .score(parseScore(result.getResultData()))
                .createdAt(result.getCreatedAt())
                .build();
    }

    @SuppressWarnings("unchecked")
    private static ScoreInfo parseScore(Map<String, Object> resultData) {
        if (resultData == null || !resultData.containsKey("score")) {
            System.out.println("비었다 이새끼야");
            return null;
        }
        try {
            Map<String, Object> scoreMap = (Map<String, Object>) resultData.get("score");

            // 안전하게 숫자 변환하는 메서드 사용
            return ScoreInfo.builder()
                    .total(parseInt(scoreMap.get("total")))
                    .east(parseInt(scoreMap.get("east")))
                    .west(parseInt(scoreMap.get("west")))
                    .build();
        } catch (Exception e) {
            // 에러 발생 시 로그 출력 (운영 환경에서는 log.error 권장)
            System.err.println("Score parsing failed: " + e.getMessage());
            return null;
        }
    }

    // 어떤 타입이 들어와도 int로 변환해주는 헬퍼 메서드
    private static int parseInt(Object value) {
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        if (value instanceof String) {
            try {
                return Integer.parseInt((String) value);
            } catch (NumberFormatException e) {
                return 0;
            }
        }
        return 0; // null이거나 변환 불가 시 0 리턴
    }

    // [중요] @Getter가 없으면 JSON 변환 시 값이 안 보일 수 있음
    @Getter
    @Builder
    public static class ScoreInfo {
        private int total;
        private int east;
        private int west;
    }
}