"""후처리 모듈 테스트 케이스

후처리기(WesternPostprocessor, EasternPostprocessor)의 테스트 케이스입니다.

테스트 시나리오:
- Western (서양 점성술): keywords 처리, element 분포, 코드 정규화
- Eastern (동양 사주): 천간지지, 오행, 십신 처리
- 엣지 케이스: 빈 값, 특수문자, 중복 처리
"""

import pytest

from yeji_ai.services.postprocessor.base import (
    PostprocessError,
    PostprocessErrorType,
    PostprocessResult,
)
from yeji_ai.services.postprocessor.eastern import EasternPostprocessor
from yeji_ai.services.postprocessor.extractors import (
    DefaultKeywordExtractor,
    extract_first_json,
    get_nested_value,
    set_nested_value,
)
from yeji_ai.services.postprocessor.noise_filter import (
    KNOWN_MIXED_SCRIPT_ERRORS,
    filter_noise,
    fix_mixed_script_tokens,
)
from yeji_ai.services.postprocessor.western import (
    WesternPostprocessor,
    normalize_zodiac_sign,
)

# ============================================================
# Western 후처리기 테스트
# ============================================================


class TestWesternPostprocessor:
    """서양 점성술 후처리기 테스트"""

    # ------------------------------------------------------------
    # FR-001: keywords 추출 테스트
    # ------------------------------------------------------------

    def test_keywords_누락시_keywords_summary에서_추출(self) -> None:
        """keywords 필드가 누락된 경우 keywords_summary에서 추출"""
        # Arrange
        raw = {
            "stats": {
                "keywords_summary": "리더십과 열정이 핵심 키워드입니다.",
                # keywords 필드 없음
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert "keywords" in result["stats"]
        keywords = result["stats"]["keywords"]
        assert len(keywords) >= 1
        # 리더십 또는 열정이 추출되어야 함
        codes = [kw["code"] for kw in keywords]
        assert "LEADERSHIP" in codes or "PASSION" in codes

    def test_keywords_빈배열시_keywords_summary에서_추출(self) -> None:
        """keywords가 빈 배열인 경우 keywords_summary에서 추출"""
        # Arrange
        raw = {
            "stats": {
                "keywords_summary": "리더십과 열정이 핵심 키워드입니다.",
                "keywords": [],  # 빈 배열
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        keywords = result["stats"]["keywords"]
        assert len(keywords) >= 1

    def test_keywords_3개이상시_그대로_유지(self) -> None:
        """keywords가 3개 이상인 경우 그대로 유지"""
        # Arrange
        original_keywords = [
            {"code": "LEADERSHIP", "label": "리더십", "weight": 0.9},
            {"code": "PASSION", "label": "열정", "weight": 0.85},
            {"code": "EMPATHY", "label": "공감", "weight": 0.8},
        ]
        raw = {
            "stats": {
                "keywords_summary": "다른 내용의 요약...",
                "keywords": original_keywords.copy(),
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["keywords"] == original_keywords

    def test_keywords_3개미만시_기본값_보충(self) -> None:
        """keywords가 3개 미만인 경우 기본값으로 보충"""
        # Arrange
        original_keywords = [
            {"code": "LEADERSHIP", "label": "리더십", "weight": 0.9},
            {"code": "PASSION", "label": "열정", "weight": 0.85},
        ]
        raw = {
            "stats": {
                "keywords_summary": "다른 내용의 요약...",
                "keywords": original_keywords.copy(),
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert: 최소 3개가 보장됨
        keywords = result["stats"]["keywords"]
        assert len(keywords) >= 3
        # 원본 키워드가 유지됨
        assert keywords[0]["code"] == "LEADERSHIP"
        assert keywords[1]["code"] == "PASSION"

    # ------------------------------------------------------------
    # FR-002: 기본값 채우기 테스트
    # ------------------------------------------------------------

    def test_필수필드_누락시_기본값_채우기(self) -> None:
        """필수 필드가 누락된 경우 기본값 채우기"""
        # Arrange
        raw = {
            "stats": {},
            "fortune_content": {},
            "lucky": {},
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["element_summary"] == "원소 분석 결과입니다."
        assert result["fortune_content"]["overview"] == "오늘의 운세입니다."
        assert result["lucky"]["color"] == "보라색"
        assert result["lucky"]["number"] == "3"

    def test_빈문자열_필드에_기본값_채우기(self) -> None:
        """빈 문자열 필드에 기본값 채우기"""
        # Arrange
        raw = {
            "stats": {
                "element_summary": "",  # 빈 문자열
            },
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["element_summary"] == "원소 분석 결과입니다."

    # ------------------------------------------------------------
    # FR-003: 구조 변환 테스트
    # ------------------------------------------------------------

    def test_element_4_distribution_객체를_배열로_변환(self) -> None:
        """4원소 분포 객체 형태를 배열로 변환"""
        # Arrange
        raw = {
            "stats": {
                "element_4_distribution": {
                    "FIRE": 30,
                    "EARTH": 25,
                    "AIR": 25,
                    "WATER": 20,
                },
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        dist = result["stats"]["element_4_distribution"]
        assert isinstance(dist, list)
        assert len(dist) == 4
        # 코드와 퍼센트 확인
        fire = next((d for d in dist if d["code"] == "FIRE"), None)
        assert fire is not None
        assert fire["percent"] == 30.0

    def test_modality_3_distribution_객체를_배열로_변환(self) -> None:
        """3양태 분포 객체 형태를 배열로 변환"""
        # Arrange
        raw = {
            "stats": {
                "modality_3_distribution": {
                    "CARDINAL": 40,
                    "FIXED": 30,
                    "MUTABLE": 30,
                },
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        dist = result["stats"]["modality_3_distribution"]
        assert isinstance(dist, list)
        assert len(dist) == 3

    def test_detailed_analysis_문자열배열을_객체배열로_변환(self) -> None:
        """상세 분석 문자열 배열을 객체 배열로 변환"""
        # Arrange
        raw = {
            "fortune_content": {
                "detailed_analysis": [
                    "첫 번째 분석 내용...",
                    "두 번째 분석 내용...",
                ],
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        analysis = result["fortune_content"]["detailed_analysis"]
        assert isinstance(analysis, list)
        assert len(analysis) == 2
        assert analysis[0]["title"] == "분석 1"
        assert analysis[0]["content"] == "첫 번째 분석 내용..."

    # ------------------------------------------------------------
    # FR-005: summary 필드 영문 코드 제거 테스트
    # ------------------------------------------------------------

    def test_summary_필드에서_영문코드_제거_AIR(self) -> None:
        """summary 필드에서 '공기(AIR)의' → '공기의' 변환"""
        # Arrange
        raw = {
            "stats": {
                "element_summary": "공기(AIR)의 에너지가 강합니다.",
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["element_summary"] == "공기의 에너지가 강합니다."
        assert "(AIR)" not in result["stats"]["element_summary"]

    def test_summary_필드에서_영문코드_제거_FIXED(self) -> None:
        """summary 필드에서 '고정(FIXED) 성향' → '고정 성향' 변환"""
        # Arrange
        raw = {
            "stats": {
                "modality_summary": "고정(FIXED) 성향이 두드러집니다.",
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["modality_summary"] == "고정 성향이 두드러집니다."
        assert "(FIXED)" not in result["stats"]["modality_summary"]

    def test_summary_필드에서_여러_영문코드_제거(self) -> None:
        """summary 필드에서 여러 영문 코드 동시 제거"""
        # Arrange
        raw = {
            "stats": {
                "element_summary": "공기(AIR)와 불(FIRE)의 에너지가 조화롭습니다.",
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["element_summary"] == "공기와 불의 에너지가 조화롭습니다."
        assert "(AIR)" not in result["stats"]["element_summary"]
        assert "(FIRE)" not in result["stats"]["element_summary"]

    def test_summary_필드_언더스코어_코드_제거(self) -> None:
        """summary 필드에서 언더스코어 포함 영문 코드 제거 (예: DAY_MASTER)"""
        # Arrange
        raw = {
            "stats": {
                "keywords_summary": "일간(DAY_MASTER)의 특성이 강합니다.",
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["keywords_summary"] == "일간의 특성이 강합니다."

    def test_summary_필드_코드없으면_그대로_유지(self) -> None:
        """영문 코드가 없는 summary 필드는 그대로 유지"""
        # Arrange
        raw = {
            "stats": {
                "element_summary": "공기의 에너지가 강합니다.",
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["element_summary"] == "공기의 에너지가 강합니다."

    # ------------------------------------------------------------
    # FR-004: 코드 정규화 테스트
    # ------------------------------------------------------------

    def test_element_code_소문자를_대문자로_정규화(self) -> None:
        """원소 코드 소문자를 대문자로 정규화"""
        # Arrange
        raw = {
            "element": "fire",  # 소문자
            "stats": {
                "element_4_distribution": [
                    {"code": "fire", "label": "불", "percent": 30.0},
                ],
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["element"] == "FIRE"
        assert result["stats"]["element_4_distribution"][0]["code"] == "FIRE"

    def test_modality_code_소문자를_대문자로_정규화(self) -> None:
        """양태 코드 소문자를 대문자로 정규화"""
        # Arrange
        raw = {
            "stats": {
                "modality_3_distribution": [
                    {"code": "fixed", "label": "고정", "percent": 40.0},
                    {"code": "cardinal", "label": "활동", "percent": 30.0},
                    {"code": "mutable", "label": "변동", "percent": 30.0},
                ],
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        codes = [d["code"] for d in result["stats"]["modality_3_distribution"]]
        assert "FIXED" in codes
        assert "CARDINAL" in codes
        assert "MUTABLE" in codes

    def test_유사어_매핑_flexible을_MUTABLE로(self) -> None:
        """유사어 매핑 테스트 - flexible -> MUTABLE"""
        # Arrange
        raw = {
            "stats": {
                "modality_3_distribution": [
                    {"code": "flexible", "label": "", "percent": 30.0},
                ],
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["modality_3_distribution"][0]["code"] == "MUTABLE"

    def test_한글코드를_영문코드로_정규화(self) -> None:
        """한글 코드를 영문 코드로 정규화"""
        # Arrange
        raw = {
            "stats": {
                "element_4_distribution": [
                    {"code": "불", "label": "불", "percent": 30.0},
                ],
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["element_4_distribution"][0]["code"] == "FIRE"

    # ------------------------------------------------------------
    # FR-005: 별자리 정규화 테스트
    # ------------------------------------------------------------

    def test_main_sign_영문소문자를_대문자로_정규화(self) -> None:
        """main_sign 영문 소문자를 대문자로 정규화"""
        # Arrange
        raw = {
            "main_sign": "aquarius",  # 소문자
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["main_sign"] == "AQUARIUS"
        assert result["main_sign_label"] == "물병자리"

    def test_main_sign_한글을_영문코드로_정규화(self) -> None:
        """main_sign 한글을 영문 코드로 정규화"""
        # Arrange
        raw = {
            "main_sign": "물병자리",  # 한글
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["main_sign"] == "AQUARIUS"
        assert result["main_sign_label"] == "물병자리"

    def test_main_sign_한글축약형_정규화(self) -> None:
        """main_sign 한글 축약형 (자리 없이) 정규화"""
        # Arrange
        raw = {
            "main_sign": "물병",  # 한글 축약형
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["main_sign"] == "AQUARIUS"
        assert result["main_sign_label"] == "물병자리"

    def test_main_sign_영문첫글자대문자_정규화(self) -> None:
        """main_sign 영문 첫글자 대문자 형식 정규화"""
        # Arrange
        raw = {
            "main_sign": "Aquarius",  # 첫글자 대문자
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["main_sign"] == "AQUARIUS"

    def test_main_sign_이미대문자면_그대로_유지(self) -> None:
        """main_sign이 이미 대문자면 그대로 유지"""
        # Arrange
        raw = {
            "main_sign": "AQUARIUS",  # 이미 대문자
            "main_sign_label": "물병자리",  # 이미 존재
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["main_sign"] == "AQUARIUS"
        assert result["main_sign_label"] == "물병자리"

    def test_main_sign_label_누락시_자동채우기(self) -> None:
        """main_sign_label이 없으면 자동으로 채우기"""
        # Arrange
        raw = {
            "main_sign": "LEO",
            # main_sign_label 없음
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["main_sign"] == "LEO"
        assert result["main_sign_label"] == "사자자리"

    def test_12별자리_전체_한글_정규화(self) -> None:
        """12별자리 모든 한글 입력 정규화 테스트"""
        # Arrange
        pp = WesternPostprocessor()
        zodiac_korean = [
            ("양자리", "ARIES"),
            ("황소자리", "TAURUS"),
            ("쌍둥이자리", "GEMINI"),
            ("게자리", "CANCER"),
            ("사자자리", "LEO"),
            ("처녀자리", "VIRGO"),
            ("천칭자리", "LIBRA"),
            ("전갈자리", "SCORPIO"),
            ("사수자리", "SAGITTARIUS"),
            ("염소자리", "CAPRICORN"),
            ("물병자리", "AQUARIUS"),
            ("물고기자리", "PISCES"),
        ]

        for korean, expected_code in zodiac_korean:
            # Act
            raw = {"main_sign": korean}
            result = pp.process(raw)

            # Assert
            assert result["main_sign"] == expected_code, f"{korean} -> {expected_code}"

    def test_12별자리_전체_영문소문자_정규화(self) -> None:
        """12별자리 모든 영문 소문자 입력 정규화 테스트"""
        # Arrange
        pp = WesternPostprocessor()
        zodiac_lowercase = [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ]

        for lowercase in zodiac_lowercase:
            # Act
            raw = {"main_sign": lowercase}
            result = pp.process(raw)

            # Assert
            assert result["main_sign"] == lowercase.upper(), f"{lowercase} -> {lowercase.upper()}"

    # ------------------------------------------------------------
    # FR-006: 서버 계산값 덮어쓰기 테스트
    # ------------------------------------------------------------

    def test_calculated_zodiac으로_main_sign_덮어쓰기(self) -> None:
        """서버 계산값으로 main_sign을 강제 덮어쓰기"""
        # Arrange: LLM이 잘못된 별자리(쌍둥이자리)를 생성한 경우
        raw = {
            "stats": {
                "main_sign": {"code": "GEMINI", "name": "쌍둥이자리"},
                "element": {"code": "AIR", "name": "공기"},
            },
            "element": "AIR",
        }
        pp = WesternPostprocessor()

        # Act: 서버 계산값(양자리)으로 덮어쓰기
        result = pp.process(raw, calculated_zodiac="ARIES")

        # Assert
        assert result["stats"]["main_sign"]["code"] == "ARIES"
        assert result["stats"]["main_sign"]["name"] == "양자리"
        # 원소도 별자리에 맞게 덮어쓰기 (양자리 = FIRE)
        assert result["stats"]["element"]["code"] == "FIRE"
        assert result["stats"]["element"]["name"] == "불"
        # 최상위 element 필드도 덮어쓰기
        assert result["element"] == "FIRE"

    def test_calculated_zodiac_1992_04_05_양자리(self) -> None:
        """1992-04-05 생년월일은 양자리(ARIES)로 덮어쓰기"""
        # Arrange: LLM이 쌍둥이자리로 잘못 생성
        raw = {
            "stats": {
                "main_sign": {"code": "GEMINI", "name": "쌍둥이자리"},
                "element": {"code": "AIR", "name": "공기"},
            },
        }
        pp = WesternPostprocessor()

        # Act: 4월 5일 = 양자리 (3/21 ~ 4/19)
        result = pp.process(raw, calculated_zodiac="ARIES")

        # Assert
        assert result["stats"]["main_sign"]["code"] == "ARIES"
        assert result["stats"]["main_sign"]["name"] == "양자리"
        assert result["stats"]["element"]["code"] == "FIRE"

    def test_calculated_zodiac_없으면_덮어쓰기_안함(self) -> None:
        """calculated_zodiac이 None이면 덮어쓰기 하지 않음"""
        # Arrange
        raw = {
            "stats": {
                "main_sign": {"code": "GEMINI", "name": "쌍둥이자리"},
                "element": {"code": "AIR", "name": "공기"},
            },
        }
        pp = WesternPostprocessor()

        # Act: calculated_zodiac 없이 호출
        result = pp.process(raw, calculated_zodiac=None)

        # Assert: 원래 값 유지 (main_sign이 dict이므로 code로 접근)
        assert result["stats"]["main_sign"]["code"] == "GEMINI"
        assert result["stats"]["element"]["code"] == "AIR"

    def test_calculated_zodiac_유효하지_않으면_무시(self) -> None:
        """calculated_zodiac이 유효하지 않은 코드면 무시"""
        # Arrange
        raw = {
            "stats": {
                "main_sign": {"code": "GEMINI", "name": "쌍둥이자리"},
            },
        }
        pp = WesternPostprocessor()

        # Act: 유효하지 않은 별자리 코드
        result = pp.process(raw, calculated_zodiac="INVALID_ZODIAC")

        # Assert: 원래 값 유지
        assert result["stats"]["main_sign"]["code"] == "GEMINI"

    def test_calculated_zodiac_12별자리_전체(self) -> None:
        """12별자리 전체에 대해 덮어쓰기 검증"""
        # Arrange
        zodiac_element_pairs = [
            ("ARIES", "FIRE"),
            ("TAURUS", "EARTH"),
            ("GEMINI", "AIR"),
            ("CANCER", "WATER"),
            ("LEO", "FIRE"),
            ("VIRGO", "EARTH"),
            ("LIBRA", "AIR"),
            ("SCORPIO", "WATER"),
            ("SAGITTARIUS", "FIRE"),
            ("CAPRICORN", "EARTH"),
            ("AQUARIUS", "AIR"),
            ("PISCES", "WATER"),
        ]
        pp = WesternPostprocessor()

        for zodiac, expected_element in zodiac_element_pairs:
            # Arrange: 빈 main_sign 객체
            raw = {"stats": {}}

            # Act
            result = pp.process(raw, calculated_zodiac=zodiac)

            # Assert
            assert result["stats"]["main_sign"]["code"] == zodiac
            assert result["stats"]["element"]["code"] == expected_element

    def test_calculated_zodiac_기존_main_sign_객체형식_아닐때(self) -> None:
        """기존 main_sign이 객체 형식이 아닐 때도 정상 덮어쓰기"""
        # Arrange: main_sign이 문자열인 경우
        raw = {
            "main_sign": "GEMINI",  # 문자열 형식 (비정상)
            "stats": {},
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw, calculated_zodiac="ARIES")

        # Assert
        assert result["stats"]["main_sign"]["code"] == "ARIES"
        assert result["stats"]["main_sign"]["name"] == "양자리"

    # ------------------------------------------------------------
    # 후처리 결과 테스트
    # ------------------------------------------------------------

    def test_process_with_result_상세결과_반환(self) -> None:
        """process_with_result 메서드가 상세 결과 반환"""
        # Arrange
        raw = {
            "stats": {
                "keywords_summary": "리더십과 열정",
                "keywords": [],
            }
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process_with_result(raw)

        # Assert
        assert isinstance(result, PostprocessResult)
        assert len(result.steps_applied) > 0
        assert result.latency_ms >= 0


# ============================================================
# Eastern 후처리기 테스트
# ============================================================


class TestEasternPostprocessor:
    """동양 사주 후처리기 테스트"""

    # ------------------------------------------------------------
    # FR-002: 기본값 채우기 테스트
    # ------------------------------------------------------------

    def test_오행분포_summary_누락시_기본값_채우기(self) -> None:
        """오행 분포 summary 필드 누락 시 기본값 채우기"""
        # Arrange
        raw = {
            "stats": {
                "five_elements": {
                    # summary 없음
                },
            },
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["stats"]["five_elements"]["summary"] == "오행 분포 분석입니다."

    def test_final_verdict_누락시_기본값_채우기(self) -> None:
        """종합 평가 필드 누락 시 기본값 채우기"""
        # Arrange
        raw = {
            "final_verdict": {
                # summary, strength, weakness, advice 모두 없음
            },
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["final_verdict"]["summary"] == "종합 분석 결과입니다."
        assert result["final_verdict"]["strength"] == "강점을 분석 중입니다."
        assert result["final_verdict"]["weakness"] == "보완점을 분석 중입니다."
        assert result["final_verdict"]["advice"] == "조언을 준비 중입니다."

    def test_lucky_누락시_기본값_채우기(self) -> None:
        """행운 정보 필드 누락 시 기본값 채우기"""
        # Arrange
        raw = {
            "lucky": {
                # color, number, item 없음
            },
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["lucky"]["color"] == "파란색"
        assert result["lucky"]["number"] == "7"
        assert result["lucky"]["item"] == "행운의 물건"

    # ------------------------------------------------------------
    # FR-003: 구조 변환 테스트
    # ------------------------------------------------------------

    def test_오행분포_객체를_배열로_변환(self) -> None:
        """오행 분포 객체 형태를 배열로 변환"""
        # Arrange
        raw = {
            "stats": {
                "five_elements": {
                    "WOOD": 20,
                    "FIRE": 30,
                    "EARTH": 20,
                    "METAL": 20,
                    "WATER": 10,
                },
            }
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        elements = result["stats"]["five_elements"]
        assert "list" in elements
        assert isinstance(elements["list"], list)
        assert len(elements["list"]) == 5

    def test_십신분포_객체를_배열로_변환(self) -> None:
        """십신 분포 객체 형태를 배열로 변환"""
        # Arrange
        raw = {
            "stats": {
                "ten_gods": {
                    "BI_GYEON": 15,
                    "SIK_SIN": 25,
                    "PYEON_JAE": 20,
                },
            }
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        gods = result["stats"]["ten_gods"]
        assert "list" in gods
        assert isinstance(gods["list"], list)
        assert len(gods["list"]) == 3

    # ------------------------------------------------------------
    # FR-004: 코드 정규화 테스트
    # ------------------------------------------------------------

    def test_오행코드_소문자를_대문자로_정규화(self) -> None:
        """오행 코드 소문자를 대문자로 정규화"""
        # Arrange
        raw = {
            "element": "fire",  # 소문자
            "stats": {
                "five_elements": {
                    "list": [
                        {"code": "wood", "label": "목", "percent": 20.0},
                        {"code": "fire", "label": "화", "percent": 30.0},
                    ],
                },
            }
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["element"] == "FIRE"
        codes = [e["code"] for e in result["stats"]["five_elements"]["list"]]
        assert "WOOD" in codes
        assert "FIRE" in codes

    def test_오행_한글코드를_영문코드로_정규화(self) -> None:
        """오행 한글 코드를 영문 코드로 정규화"""
        # Arrange
        raw = {
            "stats": {
                "five_elements": {
                    "list": [
                        {"code": "목", "label": "", "percent": 20.0},
                        {"code": "화", "label": "", "percent": 30.0},
                    ],
                },
            }
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        codes = [e["code"] for e in result["stats"]["five_elements"]["list"]]
        assert "WOOD" in codes
        assert "FIRE" in codes

    def test_십신코드_소문자를_대문자로_정규화(self) -> None:
        """십신 코드 소문자를 대문자로 정규화"""
        # Arrange
        raw = {
            "stats": {
                "ten_gods": {
                    "list": [
                        {"code": "bi_gyeon", "label": "비견", "percent": 15.0},
                        {"code": "sik_sin", "label": "식신", "percent": 25.0},
                    ],
                },
            }
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        codes = [g["code"] for g in result["stats"]["ten_gods"]["list"]]
        assert "BI_GYEON" in codes
        assert "SIK_SIN" in codes

    def test_십신_한글코드를_영문코드로_정규화(self) -> None:
        """십신 한글 코드를 영문 코드로 정규화"""
        # Arrange
        raw = {
            "stats": {
                "ten_gods": {
                    "list": [
                        {"code": "비견", "label": "", "percent": 15.0},
                        {"code": "식신", "label": "", "percent": 25.0},
                    ],
                },
            }
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        codes = [g["code"] for g in result["stats"]["ten_gods"]["list"]]
        assert "BI_GYEON" in codes
        assert "SIK_SIN" in codes

    # ------------------------------------------------------------
    # 십신 한자 혼용 수정 테스트
    # ------------------------------------------------------------

    def test_십신_한자코드를_영문코드로_정규화(self) -> None:
        """십신 한자 코드를 영문 코드로 정규화"""
        # Arrange
        raw = {
            "stats": {
                "ten_gods": {
                    "list": [
                        {"code": "比肩", "label": "비견", "percent": 15.0},
                        {"code": "食神", "label": "식신", "percent": 25.0},
                    ],
                },
            }
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        codes = [g["code"] for g in result["stats"]["ten_gods"]["list"]]
        assert "BI_GYEON" in codes
        assert "SIK_SIN" in codes

    def test_십신_한자레이블을_한글로_변환(self) -> None:
        """십신 한자 레이블을 한글로 변환"""
        # Arrange
        raw = {
            "stats": {
                "ten_gods": {
                    "list": [
                        {"code": "BI_GYEON", "label": "比肩", "percent": 15.0},
                        {"code": "SIK_SIN", "label": "食神", "percent": 25.0},
                        {"code": "PYEON_JAE", "label": "偏財", "percent": 20.0},
                    ],
                },
            }
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        labels = [g["label"] for g in result["stats"]["ten_gods"]["list"]]
        assert "비견" in labels
        assert "식신" in labels
        assert "편재" in labels
        # 한자가 남아있지 않아야 함
        assert "比肩" not in labels
        assert "食神" not in labels
        assert "偏財" not in labels

    def test_십신_한자혼용레이블을_한글로_변환(self) -> None:
        """십신 한자+한글 혼용 레이블을 한글로 변환 (예: 식神 -> 식신)"""
        # Arrange
        raw = {
            "stats": {
                "ten_gods": {
                    "list": [
                        {"code": "BI_GYEON", "label": "비肩", "percent": 15.0},
                        {"code": "SIK_SIN", "label": "식神", "percent": 25.0},
                    ],
                },
            }
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        labels = [g["label"] for g in result["stats"]["ten_gods"]["list"]]
        assert "비견" in labels
        assert "식신" in labels
        # 혼용 패턴이 남아있지 않아야 함
        assert "비肩" not in labels
        assert "식神" not in labels

    def test_전체_10십신_한자_매핑(self) -> None:
        """10개 십신 전체 한자 매핑 검증"""
        from yeji_ai.services.postprocessor.eastern import TEN_GOD_CODE_NORMALIZE

        # 한자 -> 코드 매핑 확인
        expected_hanja = {
            "比肩": "BI_GYEON",
            "劫財": "GANG_JAE",
            "食神": "SIK_SIN",
            "傷官": "SANG_GWAN",
            "偏財": "PYEON_JAE",
            "正財": "JEONG_JAE",
            "偏官": "PYEON_GWAN",
            "正官": "JEONG_GWAN",
            "偏印": "PYEON_IN",
            "正印": "JEONG_IN",
        }
        for hanja, code in expected_hanja.items():
            assert hanja in TEN_GOD_CODE_NORMALIZE
            assert TEN_GOD_CODE_NORMALIZE[hanja] == code

    def test_전체_10십신_한자레이블_한글변환(self) -> None:
        """10개 십신 전체 한자 레이블 → 한글 변환 검증"""
        from yeji_ai.services.postprocessor.eastern import TEN_GOD_HANJA_TO_KR

        # 한자 -> 한글 매핑 확인
        expected = {
            "比肩": "비견",
            "劫財": "겁재",
            "食神": "식신",
            "傷官": "상관",
            "偏財": "편재",
            "正財": "정재",
            "偏官": "편관",
            "正官": "정관",
            "偏印": "편인",
            "正印": "정인",
        }
        for hanja, korean in expected.items():
            assert hanja in TEN_GOD_HANJA_TO_KR
            assert TEN_GOD_HANJA_TO_KR[hanja] == korean

    # ------------------------------------------------------------
    # 천간지지 동기화 테스트
    # ------------------------------------------------------------

    def test_chart에서_cheongan_jiji_자동생성(self) -> None:
        """chart 데이터에서 cheongan_jiji 필드 자동 생성"""
        # Arrange
        raw = {
            "chart": {
                "year": {"gan": "甲", "ji": "子"},
                "month": {"gan": "乙", "ji": "丑"},
                "day": {"gan": "丙", "ji": "寅"},
                "hour": {"gan": "丁", "ji": "卯"},
            },
            "stats": {},
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        cj = result["stats"]["cheongan_jiji"]
        assert cj["year"]["cheon_gan"] == "甲"
        assert cj["year"]["ji_ji"] == "子"
        assert cj["month"]["cheon_gan"] == "乙"
        assert cj["day"]["cheon_gan"] == "丙"
        assert cj["hour"]["cheon_gan"] == "丁"

    # ------------------------------------------------------------
    # FR-005: 천간/지지/십신 코드 자동 생성 테스트
    # ------------------------------------------------------------

    def test_gan_code_자동생성(self) -> None:
        """천간 한자에서 gan_code 자동 생성"""
        # Arrange
        raw = {
            "chart": {
                "year": {"gan": "甲", "ji": "子", "element_code": "WOOD"},
                "month": {"gan": "乙", "ji": "丑", "element_code": "WOOD"},
                "day": {"gan": "丙", "ji": "寅", "element_code": "FIRE"},
                "hour": {"gan": "丁", "ji": "卯", "element_code": "FIRE"},
            },
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["chart"]["year"]["gan_code"] == "GAP"
        assert result["chart"]["month"]["gan_code"] == "EUL"
        assert result["chart"]["day"]["gan_code"] == "BYEONG"
        assert result["chart"]["hour"]["gan_code"] == "JEONG"

    def test_ji_code_자동생성(self) -> None:
        """지지 한자에서 ji_code 자동 생성"""
        # Arrange
        raw = {
            "chart": {
                "year": {"gan": "甲", "ji": "子", "element_code": "WOOD"},
                "month": {"gan": "乙", "ji": "丑", "element_code": "WOOD"},
                "day": {"gan": "丙", "ji": "寅", "element_code": "FIRE"},
                "hour": {"gan": "丁", "ji": "卯", "element_code": "FIRE"},
            },
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["chart"]["year"]["ji_code"] == "JA"
        assert result["chart"]["month"]["ji_code"] == "CHUK"
        assert result["chart"]["day"]["ji_code"] == "IN"
        assert result["chart"]["hour"]["ji_code"] == "MYO"

    def test_ten_god_code_자동생성_day_master(self) -> None:
        """일주(day)는 DAY_MASTER로 자동 생성"""
        # Arrange
        raw = {
            "chart": {
                "day": {"gan": "丙", "ji": "寅", "element_code": "FIRE"},
            },
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["chart"]["day"]["ten_god_code"] == "DAY_MASTER"

    def test_ten_god_code_자동계산_비견(self) -> None:
        """같은 오행, 같은 음양이면 비견(BI_GYEON)"""
        # Arrange: 일간 丙(FIRE, YANG), 년간 丙(FIRE, YANG) = 비견
        raw = {
            "chart": {
                "year": {"gan": "丙", "ji": "子", "element_code": "FIRE"},
                "day": {"gan": "丙", "ji": "寅", "element_code": "FIRE"},
            },
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["chart"]["year"]["ten_god_code"] == "BI_GYEON"

    def test_ten_god_code_자동계산_겁재(self) -> None:
        """같은 오행, 다른 음양이면 겁재(GANG_JAE)"""
        # Arrange: 일간 丙(FIRE, YANG), 년간 丁(FIRE, YIN) = 겁재
        raw = {
            "chart": {
                "year": {"gan": "丁", "ji": "子", "element_code": "FIRE"},
                "day": {"gan": "丙", "ji": "寅", "element_code": "FIRE"},
            },
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["chart"]["year"]["ten_god_code"] == "GANG_JAE"

    def test_ten_god_code_자동계산_정인(self) -> None:
        """생받는 오행, 다른 음양이면 정인(JEONG_IN)"""
        # Arrange: 일간 丙(FIRE, YANG), 년간 乙(WOOD, YIN) = 정인 (목생화, 음양다름)
        raw = {
            "chart": {
                "year": {"gan": "乙", "ji": "子", "element_code": "WOOD"},
                "day": {"gan": "丙", "ji": "寅", "element_code": "FIRE"},
            },
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert result["chart"]["year"]["ten_god_code"] == "JEONG_IN"

    def test_기존_코드_필드_유지(self) -> None:
        """LLM이 이미 생성한 코드 필드는 덮어쓰지 않음"""
        # Arrange
        raw = {
            "chart": {
                "year": {
                    "gan": "甲",
                    "gan_code": "GAP",  # 이미 존재
                    "ji": "子",
                    "ji_code": "JA",  # 이미 존재
                    "element_code": "WOOD",
                    "ten_god_code": "PYEON_IN",  # 이미 존재
                },
                "day": {"gan": "丙", "ji": "寅", "element_code": "FIRE"},
            },
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert: 기존 값 유지
        assert result["chart"]["year"]["gan_code"] == "GAP"
        assert result["chart"]["year"]["ji_code"] == "JA"
        assert result["chart"]["year"]["ten_god_code"] == "PYEON_IN"

    def test_전체_10천간_매핑(self) -> None:
        """10개 천간 전체 매핑 검증"""
        from yeji_ai.services.postprocessor.eastern import GAN_TO_CODE

        expected = {
            "甲": "GAP", "乙": "EUL", "丙": "BYEONG", "丁": "JEONG", "戊": "MU",
            "己": "GI", "庚": "GYEONG", "辛": "SIN", "壬": "IM", "癸": "GYE",
        }
        assert GAN_TO_CODE == expected

    def test_전체_12지지_매핑(self) -> None:
        """12개 지지 전체 매핑 검증"""
        from yeji_ai.services.postprocessor.eastern import JI_TO_CODE

        expected = {
            "子": "JA", "丑": "CHUK", "寅": "IN", "卯": "MYO", "辰": "JIN", "巳": "SA",
            "午": "O", "未": "MI", "申": "SHIN", "酉": "YU", "戌": "SUL", "亥": "HAE",
        }
        assert JI_TO_CODE == expected

    # ------------------------------------------------------------
    # FR-006: 서버 계산값 강제 덮어쓰기 테스트
    # ------------------------------------------------------------

    def test_서버_계산값으로_일간_덮어쓰기(self) -> None:
        """LLM이 잘못 생성한 일간을 서버 계산값으로 덮어쓰기 (辛→甲 문제 해결)"""
        # Arrange: LLM이 일간을 甲으로 잘못 생성한 경우
        raw = {
            "chart": {
                "year": {"gan": "壬", "ji": "申", "element_code": "WATER"},
                "month": {"gan": "甲", "ji": "辰", "element_code": "WOOD"},
                "day": {"gan": "甲", "ji": "未", "element_code": "WOOD"},  # LLM 오류: 甲 (정답: 辛)
                "hour": {"gan": "庚", "ji": "午", "element_code": "METAL"},
            },
        }
        # 서버에서 계산된 정확한 사주 정보 (1992-04-05 기준)
        calculated_saju = {
            "year_pillar_hanja": "壬申",
            "month_pillar_hanja": "甲辰",
            "day_pillar_hanja": "辛未",  # 정확한 일주: 辛未
            "hour_pillar_hanja": "庚午",
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw, calculated_saju=calculated_saju)

        # Assert: 일간이 辛으로 덮어쓰기됨
        assert result["chart"]["day"]["gan"] == "辛"
        assert result["chart"]["day"]["ji"] == "未"
        assert result["chart"]["day"]["gan_code"] == "SIN"
        assert result["chart"]["day"]["ji_code"] == "MI"
        assert result["chart"]["day"]["element_code"] == "METAL"  # 辛은 금(METAL)

    def test_서버_계산값으로_4기둥_전체_덮어쓰기(self) -> None:
        """4기둥 전체를 서버 계산값으로 덮어쓰기"""
        # Arrange: LLM 응답에 사주 정보가 아예 없는 경우
        raw = {
            "chart": {},
        }
        calculated_saju = {
            "year_pillar_hanja": "壬申",
            "month_pillar_hanja": "甲辰",
            "day_pillar_hanja": "辛未",
            "hour_pillar_hanja": "庚午",
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw, calculated_saju=calculated_saju)

        # Assert: 4기둥 전체가 생성됨
        assert result["chart"]["year"]["gan"] == "壬"
        assert result["chart"]["year"]["ji"] == "申"
        assert result["chart"]["month"]["gan"] == "甲"
        assert result["chart"]["month"]["ji"] == "辰"
        assert result["chart"]["day"]["gan"] == "辛"
        assert result["chart"]["day"]["ji"] == "未"
        assert result["chart"]["hour"]["gan"] == "庚"
        assert result["chart"]["hour"]["ji"] == "午"

    def test_서버_계산값_덮어쓰기_후_십신_재계산(self) -> None:
        """서버 계산값 덮어쓰기 후 십신이 올바르게 재계산됨"""
        # Arrange
        raw = {
            "chart": {
                "year": {"gan": "壬", "ji": "申", "element_code": "WATER"},
                "month": {"gan": "甲", "ji": "辰", "element_code": "WOOD"},
                "day": {"gan": "甲", "ji": "未", "element_code": "WOOD"},  # 잘못된 일간
                "hour": {"gan": "庚", "ji": "午", "element_code": "METAL"},
            },
        }
        calculated_saju = {
            "year_pillar_hanja": "壬申",
            "month_pillar_hanja": "甲辰",
            "day_pillar_hanja": "辛未",  # 정확한 일간: 辛 (금, 음)
            "hour_pillar_hanja": "庚午",
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw, calculated_saju=calculated_saju)

        # Assert: 일주는 DAY_MASTER
        assert result["chart"]["day"]["ten_god_code"] == "DAY_MASTER"

        # 辛(금, 음) 기준 십신 계산:
        # 壬(수, 양) - 금생수(SIK), 음양 다름 -> 상관(SANG_GWAN)
        assert result["chart"]["year"]["ten_god_code"] == "SANG_GWAN"
        # 甲(목, 양) - 금극목(JAE), 음양 다름 -> 정재(JEONG_JAE)
        assert result["chart"]["month"]["ten_god_code"] == "JEONG_JAE"
        # 庚(금, 양) - 같은 오행(BI), 음양 다름 -> 겁재(GANG_JAE)
        assert result["chart"]["hour"]["ten_god_code"] == "GANG_JAE"

    def test_서버_계산값_없으면_덮어쓰기_스킵(self) -> None:
        """calculated_saju가 None이면 덮어쓰기 단계 스킵"""
        # Arrange
        raw = {
            "chart": {
                "day": {"gan": "甲", "ji": "子", "element_code": "WOOD"},
            },
        }
        pp = EasternPostprocessor()

        # Act: calculated_saju=None (기본값)
        result = pp.process(raw)

        # Assert: 원본 유지
        assert result["chart"]["day"]["gan"] == "甲"

    def test_서버_계산값_시주_없으면_시주_스킵(self) -> None:
        """서버 계산값에 시주가 없으면 시주 덮어쓰기 스킵"""
        # Arrange
        raw = {
            "chart": {
                "day": {"gan": "甲", "ji": "子", "element_code": "WOOD"},
                "hour": {"gan": "丁", "ji": "巳", "element_code": "FIRE"},
            },
        }
        calculated_saju = {
            "year_pillar_hanja": "壬申",
            "month_pillar_hanja": "甲辰",
            "day_pillar_hanja": "辛未",
            "hour_pillar_hanja": None,  # 시주 없음
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw, calculated_saju=calculated_saju)

        # Assert: 일주는 덮어쓰기됨, 시주는 원본 유지
        assert result["chart"]["day"]["gan"] == "辛"
        assert result["chart"]["hour"]["gan"] == "丁"  # 원본 유지

    def test_서버_계산값_cheongan_jiji_동기화(self) -> None:
        """서버 계산값 덮어쓰기 후 cheongan_jiji도 동기화됨"""
        # Arrange
        raw = {
            "chart": {
                "day": {"gan": "甲", "ji": "子", "element_code": "WOOD"},
            },
            "stats": {
                "cheongan_jiji": {
                    "summary": "천간지지 요약",
                    "day": {"cheon_gan": "甲", "ji_ji": "子"},
                },
            },
        }
        calculated_saju = {
            "day_pillar_hanja": "辛未",
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw, calculated_saju=calculated_saju)

        # Assert: cheongan_jiji도 동기화됨
        assert result["stats"]["cheongan_jiji"]["day"]["cheon_gan"] == "辛"
        assert result["stats"]["cheongan_jiji"]["day"]["ji_ji"] == "未"

    def test_process_with_result에도_calculated_saju_전달(self) -> None:
        """process_with_result 메서드에서도 calculated_saju 정상 처리"""
        # Arrange
        raw = {
            "chart": {
                "day": {"gan": "甲", "ji": "子", "element_code": "WOOD"},
            },
        }
        calculated_saju = {
            "day_pillar_hanja": "辛未",
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process_with_result(raw, calculated_saju=calculated_saju)

        # Assert
        assert result.data["chart"]["day"]["gan"] == "辛"
        assert "override_with_calculated" in result.steps_applied


# ============================================================
# 별자리 정규화 함수 테스트
# ============================================================


class TestNormalizeZodiacSign:
    """normalize_zodiac_sign 함수 단위 테스트"""

    def test_영문대문자_입력_그대로_반환(self) -> None:
        """영문 대문자 입력은 그대로 반환"""
        # Act & Assert
        assert normalize_zodiac_sign("AQUARIUS") == "AQUARIUS"
        assert normalize_zodiac_sign("LEO") == "LEO"
        assert normalize_zodiac_sign("ARIES") == "ARIES"

    def test_영문소문자_입력_대문자로_변환(self) -> None:
        """영문 소문자 입력은 대문자로 변환"""
        # Act & Assert
        assert normalize_zodiac_sign("aquarius") == "AQUARIUS"
        assert normalize_zodiac_sign("leo") == "LEO"
        assert normalize_zodiac_sign("aries") == "ARIES"

    def test_영문첫글자대문자_입력_대문자로_변환(self) -> None:
        """영문 첫글자 대문자 입력은 대문자로 변환"""
        # Act & Assert
        assert normalize_zodiac_sign("Aquarius") == "AQUARIUS"
        assert normalize_zodiac_sign("Leo") == "LEO"
        assert normalize_zodiac_sign("Sagittarius") == "SAGITTARIUS"

    def test_한글전체_입력_영문코드로_변환(self) -> None:
        """한글 전체 입력은 영문 코드로 변환"""
        # Act & Assert
        assert normalize_zodiac_sign("물병자리") == "AQUARIUS"
        assert normalize_zodiac_sign("사자자리") == "LEO"
        assert normalize_zodiac_sign("양자리") == "ARIES"
        assert normalize_zodiac_sign("쌍둥이자리") == "GEMINI"

    def test_한글축약형_입력_영문코드로_변환(self) -> None:
        """한글 축약형 (자리 없이) 입력은 영문 코드로 변환"""
        # Act & Assert
        assert normalize_zodiac_sign("물병") == "AQUARIUS"
        assert normalize_zodiac_sign("사자") == "LEO"
        assert normalize_zodiac_sign("양") == "ARIES"
        assert normalize_zodiac_sign("쌍둥이") == "GEMINI"

    def test_None_입력_None_반환(self) -> None:
        """None 입력은 None 반환"""
        # Act & Assert
        assert normalize_zodiac_sign(None) is None

    def test_공백포함_입력_정상처리(self) -> None:
        """공백이 포함된 입력도 정상 처리"""
        # Act & Assert
        assert normalize_zodiac_sign(" aquarius ") == "AQUARIUS"
        assert normalize_zodiac_sign(" 물병자리 ") == "AQUARIUS"

    def test_매핑에없는_값_대문자변환(self) -> None:
        """매핑에 없는 값은 대문자로 변환하여 반환"""
        # Act & Assert
        assert normalize_zodiac_sign("unknown") == "UNKNOWN"
        assert normalize_zodiac_sign("xyz") == "XYZ"

    def test_12별자리_모두_정상매핑(self) -> None:
        """12별자리 모두 정상적으로 매핑되는지 확인"""
        # Arrange
        expected_codes = [
            "ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
            "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
        ]

        # Act & Assert - 영문 소문자
        for code in expected_codes:
            assert normalize_zodiac_sign(code.lower()) == code

        # Act & Assert - 영문 대문자
        for code in expected_codes:
            assert normalize_zodiac_sign(code) == code


# ============================================================
# 키워드 추출기 테스트
# ============================================================


class TestDefaultKeywordExtractor:
    """기본 키워드 추출기 테스트"""

    def test_단일_키워드_추출(self) -> None:
        """단일 키워드 추출"""
        # Arrange
        extractor = DefaultKeywordExtractor()
        text = "리더십이 중요합니다."

        # Act
        keywords = extractor.extract(text)

        # Assert
        assert len(keywords) == 1
        assert keywords[0]["code"] == "LEADERSHIP"
        assert keywords[0]["label"] == "리더십"
        assert keywords[0]["weight"] == 0.9

    def test_복수_키워드_추출(self) -> None:
        """복수 키워드 추출"""
        # Arrange
        extractor = DefaultKeywordExtractor()
        text = "리더십과 열정, 그리고 소통이 핵심입니다."

        # Act
        keywords = extractor.extract(text)

        # Assert
        assert len(keywords) >= 2
        codes = [kw["code"] for kw in keywords]
        assert "LEADERSHIP" in codes
        assert "PASSION" in codes

    def test_최대_5개_키워드_제한(self) -> None:
        """최대 5개 키워드만 추출"""
        # Arrange
        extractor = DefaultKeywordExtractor()
        text = "리더십, 열정, 소통, 혁신, 분석, 안정, 공감 등 다양한 특성이 있습니다."

        # Act
        keywords = extractor.extract(text)

        # Assert
        assert len(keywords) <= 5

    def test_가중치_순서대로_감소(self) -> None:
        """가중치가 발견 순서에 따라 감소"""
        # Arrange
        extractor = DefaultKeywordExtractor()
        text = "리더십과 열정이 핵심입니다."

        # Act
        keywords = extractor.extract(text)

        # Assert
        if len(keywords) >= 2:
            assert keywords[0]["weight"] == 0.9
            assert keywords[1]["weight"] == 0.85

    def test_중복_키워드_처리(self) -> None:
        """동일 코드로 매핑되는 키워드 중복 방지"""
        # Arrange
        extractor = DefaultKeywordExtractor()
        text = "의사소통과 커뮤니케이션이 중요합니다."  # 둘 다 COMMUNICATION

        # Act
        keywords = extractor.extract(text)

        # Assert
        codes = [kw["code"] for kw in keywords]
        # COMMUNICATION은 한 번만 나와야 함
        assert codes.count("COMMUNICATION") == 1

    def test_빈_텍스트_처리(self) -> None:
        """빈 텍스트 입력 시 빈 배열 반환"""
        # Arrange
        extractor = DefaultKeywordExtractor()

        # Act
        keywords = extractor.extract("")

        # Assert
        assert keywords == []


# ============================================================
# 유틸리티 함수 테스트
# ============================================================


class TestUtilityFunctions:
    """유틸리티 함수 테스트"""

    def test_extract_first_json_정상_추출(self) -> None:
        """첫 번째 JSON 객체 정상 추출"""
        # Arrange
        text = '{"key": "value"}'

        # Act
        result = extract_first_json(text)

        # Assert
        assert result == {"key": "value"}

    def test_extract_first_json_앞뒤_텍스트_무시(self) -> None:
        """JSON 앞뒤 텍스트 무시하고 추출"""
        # Arrange
        text = 'Some text before {"key": "value"} some text after'

        # Act
        result = extract_first_json(text)

        # Assert
        assert result == {"key": "value"}

    def test_extract_first_json_중복_json_첫번째만_추출(self) -> None:
        """중복 JSON 중 첫 번째만 추출 (FR-005)"""
        # Arrange
        text = '{"first": 1} user 다음 질문... assistant {"second": 2}'

        # Act
        result = extract_first_json(text)

        # Assert
        assert result == {"first": 1}

    def test_extract_first_json_유효하지_않은_json_예외발생(self) -> None:
        """유효하지 않은 JSON 텍스트에서 예외 발생"""
        # Arrange
        text = "no json here"

        # Act & Assert
        with pytest.raises(ValueError, match="유효한 JSON"):
            extract_first_json(text)

    def test_get_nested_value_정상조회(self) -> None:
        """중첩 경로에서 값 정상 조회"""
        # Arrange
        data = {
            "stats": {
                "keywords_summary": "테스트 값",
            }
        }

        # Act
        result = get_nested_value(data, "stats.keywords_summary")

        # Assert
        assert result == "테스트 값"

    def test_get_nested_value_경로_없음_None반환(self) -> None:
        """존재하지 않는 경로에서 None 반환"""
        # Arrange
        data = {"stats": {}}

        # Act
        result = get_nested_value(data, "stats.keywords_summary")

        # Assert
        assert result is None

    def test_set_nested_value_정상설정(self) -> None:
        """중첩 경로에 값 정상 설정"""
        # Arrange
        data: dict = {"stats": {}}

        # Act
        set_nested_value(data, "stats.keywords_summary", "새 값")

        # Assert
        assert data["stats"]["keywords_summary"] == "새 값"

    def test_set_nested_value_중간경로_자동생성(self) -> None:
        """중간 경로가 없는 경우 자동 생성"""
        # Arrange
        data: dict = {}

        # Act
        set_nested_value(data, "a.b.c", "value")

        # Assert
        assert data["a"]["b"]["c"] == "value"


# ============================================================
# PostprocessResult 테스트
# ============================================================


class TestPostprocessResult:
    """PostprocessResult 데이터 클래스 테스트"""

    def test_is_success_에러없으면_True(self) -> None:
        """에러가 없으면 is_success가 True"""
        # Arrange
        result = PostprocessResult(
            data={"key": "value"},
            original={"key": "value"},
            steps_applied=["step1"],
            errors=[],
        )

        # Assert
        assert result.is_success is True

    def test_is_success_에러있으면_False(self) -> None:
        """에러가 있으면 is_success가 False"""
        # Arrange
        error = PostprocessError(
            step_name="test",
            error_type=PostprocessErrorType.UNKNOWN,
            message="테스트 에러",
        )
        result = PostprocessResult(
            data={"key": "value"},
            original={"key": "value"},
            steps_applied=["step1"],
            errors=[error],
        )

        # Assert
        assert result.is_success is False

    def test_partial_success_일부성공시_True(self) -> None:
        """일부 단계만 성공하면 partial_success가 True"""
        # Arrange
        error = PostprocessError(
            step_name="test",
            error_type=PostprocessErrorType.UNKNOWN,
            message="테스트 에러",
        )
        result = PostprocessResult(
            data={"key": "value"},
            original={"key": "value"},
            steps_applied=["step1"],  # 일부 성공
            errors=[error],  # 에러도 있음
        )

        # Assert
        assert result.partial_success is True


# ============================================================
# 통합 테스트
# ============================================================


# ============================================================
# 혼합 스크립트 토큰 수정 테스트
# ============================================================


class TestMixedScriptTokenFixer:
    """한글+영문 혼합 토큰 오류 수정 테스트 (AWQ 양자화 모델 문제)"""

    def test_알려진_오류_패턴_수정_꾸urly(self) -> None:
        """알려진 오류 패턴 '꾸urly' → '꾸준히' 수정"""
        # Arrange
        text = "꾸urly 노력하면 좋은 결과가 있소."

        # Act
        result = fix_mixed_script_tokens(text)

        # Assert
        assert result == "꾸준히 노력하면 좋은 결과가 있소."
        assert "꾸urly" not in result

    def test_알려진_오류_패턴_수정_꾸ulous(self) -> None:
        """알려진 오류 패턴 '꾸ulous' → '꾸준히' 수정"""
        # Arrange
        text = "꾸ulous 노력하시오."

        # Act
        result = fix_mixed_script_tokens(text)

        # Assert
        assert result == "꾸준히 노력하시오."

    def test_알려진_오류_패턴_수정_꾸rly(self) -> None:
        """알려진 오류 패턴 '꾸rly' → '꾸준히' 수정"""
        # Arrange
        text = "꾸rly한 자세가 중요하오."

        # Act
        result = fix_mixed_script_tokens(text)

        # Assert
        assert result == "꾸준히한 자세가 중요하오."

    def test_여러_오류_패턴_한번에_수정(self) -> None:
        """문장 내 여러 오류 패턴 동시 수정"""
        # Arrange
        text = "꾸urly 노력하고 꾸ulous 정진하시오."

        # Act
        result = fix_mixed_script_tokens(text)

        # Assert
        assert result == "꾸준히 노력하고 꾸준히 정진하시오."

    def test_오류패턴_없는_정상_텍스트_그대로_유지(self) -> None:
        """오류 패턴이 없는 정상 텍스트는 그대로 유지"""
        # Arrange
        text = "꾸준히 노력하면 좋은 결과가 있소."

        # Act
        result = fix_mixed_script_tokens(text)

        # Assert
        assert result == text

    def test_빈_텍스트_처리(self) -> None:
        """빈 텍스트 입력 시 빈 문자열 반환"""
        # Act & Assert
        assert fix_mixed_script_tokens("") == ""
        assert fix_mixed_script_tokens(None) is None  # type: ignore

    def test_알려진_오류_매핑_상수_존재(self) -> None:
        """KNOWN_MIXED_SCRIPT_ERRORS 상수가 예상 값 포함"""
        # Assert
        assert "꾸urly" in KNOWN_MIXED_SCRIPT_ERRORS
        assert "꾸ulous" in KNOWN_MIXED_SCRIPT_ERRORS
        assert "꾸rly" in KNOWN_MIXED_SCRIPT_ERRORS
        # 모두 '꾸준히'로 매핑되어야 함
        for key in KNOWN_MIXED_SCRIPT_ERRORS:
            assert KNOWN_MIXED_SCRIPT_ERRORS[key] == "꾸준히"


class TestFilterNoiseWithMixedScript:
    """filter_noise 함수 통합 테스트 (혼합 스크립트 수정 포함)"""

    def test_filter_noise에서_혼합_스크립트_수정_적용(self) -> None:
        """filter_noise 함수가 혼합 스크립트 오류를 먼저 수정"""
        # Arrange
        text = "꾸urly 노력하면 좋은 결과가 있소."

        # Act
        result = filter_noise(text, aggressive=False)

        # Assert
        assert "꾸준히" in result
        assert "꾸urly" not in result

    def test_filter_noise_혼합_스크립트와_외래문자_동시처리(self) -> None:
        """혼합 스크립트와 외래 문자 동시 처리"""
        # Arrange: 혼합 스크립트 + 태국어 노이즈
        text = "꾸urly 노력하시오.ครี糖เริ่ม 좋은 하루 보내시오."

        # Act
        result = filter_noise(text, aggressive=False)

        # Assert
        assert "꾸준히" in result
        assert "꾸urly" not in result
        # 태국어도 제거되어야 함
        assert "ครี" not in result

    def test_filter_noise_aggressive모드에서도_혼합_스크립트_수정(self) -> None:
        """aggressive 모드에서도 혼합 스크립트 먼저 수정"""
        # Arrange
        text = "꾸urly 노력하시오."

        # Act
        result = filter_noise(text, aggressive=True)

        # Assert
        assert "꾸준히" in result


# ============================================================
# 통합 테스트
# ============================================================


class TestIntegration:
    """통합 테스트 - 전체 파이프라인 동작 확인"""

    def test_western_전체_파이프라인_성공(self) -> None:
        """Western 후처리 전체 파이프라인 성공 케이스"""
        # Arrange
        raw = {
            "main_sign": "aquarius",  # 별자리 소문자
            "element": "fire",
            "stats": {
                "keywords_summary": "리더십과 열정이 핵심입니다.",
                "keywords": [],
                "element_4_distribution": {
                    "fire": 30,
                    "earth": 25,
                    "air": 25,
                    "water": 20,
                },
                "modality_3_distribution": {
                    "fixed": 40,
                    "cardinal": 30,
                    "mutable": 30,
                },
            },
            "fortune_content": {},
            "lucky": {},
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        # 별자리 정규화 확인
        assert result["main_sign"] == "AQUARIUS"
        assert result["main_sign_label"] == "물병자리"
        # 코드 정규화 확인
        assert result["element"] == "FIRE"
        # 구조 변환 확인
        assert isinstance(result["stats"]["element_4_distribution"], list)
        assert isinstance(result["stats"]["modality_3_distribution"], list)
        # 키워드 추출 확인
        assert len(result["stats"]["keywords"]) >= 1
        # 기본값 채우기 확인
        assert result["lucky"]["color"] == "보라색"

    def test_eastern_전체_파이프라인_성공(self) -> None:
        """Eastern 후처리 전체 파이프라인 성공 케이스"""
        # Arrange
        raw = {
            "element": "fire",
            "chart": {
                "year": {"gan": "甲", "ji": "子", "element_code": "wood"},
                "month": {"gan": "乙", "ji": "丑", "element_code": "earth"},
                "day": {"gan": "丙", "ji": "寅", "element_code": "fire"},
                "hour": {"gan": "丁", "ji": "卯", "element_code": "fire"},
            },
            "stats": {
                "five_elements": {
                    "WOOD": 20,
                    "FIRE": 30,
                    "EARTH": 20,
                    "METAL": 20,
                    "WATER": 10,
                },
                "ten_gods": {
                    "bi_gyeon": 15,
                    "sik_sin": 25,
                },
            },
            "final_verdict": {},
            "lucky": {},
        }
        pp = EasternPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        # 코드 정규화 확인
        assert result["element"] == "FIRE"
        # 구조 변환 확인
        assert isinstance(result["stats"]["five_elements"]["list"], list)
        assert isinstance(result["stats"]["ten_gods"]["list"], list)
        # 천간지지 동기화 확인
        assert "cheongan_jiji" in result["stats"]
        assert result["stats"]["cheongan_jiji"]["year"]["cheon_gan"] == "甲"
        # 기본값 채우기 확인
        assert result["lucky"]["color"] == "파란색"
        assert result["final_verdict"]["summary"] == "종합 분석 결과입니다."

    def test_레이턴시_50ms_이내(self) -> None:
        """NFR-001: 후처리 레이턴시 50ms 이내"""
        # Arrange
        raw = {
            "element": "fire",
            "stats": {
                "keywords_summary": "리더십과 열정이 핵심입니다.",
                "keywords": [],
                "element_4_distribution": {
                    "fire": 30,
                    "earth": 25,
                    "air": 25,
                    "water": 20,
                },
            },
        }
        pp = WesternPostprocessor()

        # Act
        result = pp.process_with_result(raw)

        # Assert
        assert result.latency_ms < 50


# ============================================================
# Tarot 후처리기 테스트
# ============================================================


class TestTarotPostprocessor:
    """타로 후처리기 테스트"""

    def test_normalize_cards_orientation_대소문자(self) -> None:
        """카드 orientation 대소문자 정규화"""
        from yeji_ai.services.postprocessor.tarot import TarotPostprocessor

        # Arrange
        raw = {
            "cards": [
                {"orientation": "upright", "position": "past"},
                {"orientation": "Reversed", "position": "present"},
                {"orientation": "UPRIGHT", "position": "future"},
            ]
        }
        pp = TarotPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        cards = result["cards"]
        assert cards[0]["orientation"] == "UPRIGHT"
        assert cards[1]["orientation"] == "REVERSED"
        assert cards[2]["orientation"] == "UPRIGHT"

    def test_normalize_cards_position_label_자동생성(self) -> None:
        """카드 position_label 자동 생성"""
        from yeji_ai.services.postprocessor.tarot import TarotPostprocessor

        # Arrange
        raw = {
            "cards": [
                {"position": "PAST", "orientation": "UPRIGHT"},
                {"position": "PRESENT", "orientation": "UPRIGHT"},
                {"position": "FUTURE", "orientation": "UPRIGHT"},
            ]
        }
        pp = TarotPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        cards = result["cards"]
        assert cards[0]["position_label"] == "과거"
        assert cards[1]["position_label"] == "현재"
        assert cards[2]["position_label"] == "미래"

    def test_normalize_cards_orientation_label_자동생성(self) -> None:
        """카드 orientation_label 자동 생성"""
        from yeji_ai.services.postprocessor.tarot import TarotPostprocessor

        # Arrange
        raw = {
            "cards": [
                {"orientation": "UPRIGHT", "position": "PAST"},
                {"orientation": "REVERSED", "position": "PRESENT"},
            ]
        }
        pp = TarotPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        cards = result["cards"]
        assert cards[0]["orientation_label"] == "정위치"
        assert cards[1]["orientation_label"] == "역위치"

    def test_normalize_cards_keywords_기본값(self) -> None:
        """카드 keywords 없으면 기본값 채우기"""
        from yeji_ai.services.postprocessor.tarot import TarotPostprocessor

        # Arrange
        raw = {
            "cards": [
                {"name": "The Fool", "orientation": "UPRIGHT"},
                {"name": "The Magician", "orientation": "REVERSED", "keywords": []},
            ]
        }
        pp = TarotPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        cards = result["cards"]
        assert "keywords" in cards[0]
        assert cards[0]["keywords"] == ["해석 키워드"]
        assert cards[1]["keywords"] == ["해석 키워드"]

    def test_fill_summary_기본값(self) -> None:
        """summary 필드 기본값 채우기"""
        from yeji_ai.services.postprocessor.tarot import TarotPostprocessor

        # Arrange
        raw = {}
        pp = TarotPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert "summary" in result
        summary = result["summary"]
        assert "overall_theme" in summary
        assert "past_to_present" in summary
        assert "present_to_future" in summary
        assert "advice" in summary

    def test_fill_lucky_기본값(self) -> None:
        """lucky 필드 기본값 채우기"""
        from yeji_ai.services.postprocessor.tarot import TarotPostprocessor

        # Arrange
        raw = {}
        pp = TarotPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        assert "lucky" in result
        lucky = result["lucky"]
        assert lucky["color"] == "보라색"
        assert lucky["number"] == "7"
        assert lucky["element"] == "물"
        assert "timing" in lucky

    def test_fail_safe_원본반환(self) -> None:
        """치명적 오류 시 원본 반환 (fail-safe)"""
        from yeji_ai.services.postprocessor.tarot import TarotPostprocessor

        # Arrange
        raw = {"cards": "not a list"}  # 잘못된 구조
        pp = TarotPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        # 오류가 발생해도 원본이 반환되어야 함
        assert result == raw or "cards" in result

    def test_한글_orientation_정규화(self) -> None:
        """한글 orientation도 정규화"""
        from yeji_ai.services.postprocessor.tarot import TarotPostprocessor

        # Arrange
        raw = {
            "cards": [
                {"orientation": "정위치", "position": "PAST"},
                {"orientation": "역위치", "position": "PRESENT"},
            ]
        }
        pp = TarotPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        cards = result["cards"]
        assert cards[0]["orientation"] == "UPRIGHT"
        assert cards[1]["orientation"] == "REVERSED"

    def test_position_소문자_정규화(self) -> None:
        """position 소문자도 대문자로 정규화"""
        from yeji_ai.services.postprocessor.tarot import TarotPostprocessor

        # Arrange
        raw = {
            "cards": [
                {"position": "past", "orientation": "UPRIGHT"},
                {"position": "Present", "orientation": "UPRIGHT"},
            ]
        }
        pp = TarotPostprocessor()

        # Act
        result = pp.process(raw)

        # Assert
        cards = result["cards"]
        assert cards[0]["position"] == "PAST"
        assert cards[1]["position"] == "PRESENT"
