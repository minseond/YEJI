package com.yeji.domain.compatibility.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.Map;

@Getter
@NoArgsConstructor
@Schema(description = "궁합 분석 요청")
public class CompatibilityRequest {

    @Schema(description = "친구인 경우 식별용 ID(선택, AI로는 안 보냄)", example = "123")
    private Long targetUserId;

    @Schema(description = "상대 이름(필수)", example = "김민수")
    private String targetName;

    @Schema(description = "관계 타입(선택)", example = "LOVE", nullable = true)
    private String relationType;

    @Schema(description = "점수", example = "90", nullable = true)
    private Long score;

    @Schema(
            description = """
                    상대 생년 정보 (필수)
                    - gender: M/F
                    - is_solar: true(양력) / false(음력)
                    - birth_date: YYYY-MM-DD
                    - birth_time: HH:mm (모르면 생략 가능)
                    """,
            example = """
                    {
                      "gender": "M",
                      "is_solar": true,
                      "birth_date": "1995-05-05",
                      "birth_time": "14:30"
                    }
                    """
    )
    private Map<String, Object> birthData;
}
