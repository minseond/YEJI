"""vLLM Guided Decoding 관련 단위 테스트

guided_json/json_schema response_format 기능 테스트

테스트 실행:
    pytest C:/Users/SSAFY/yeji-ai-server/ai/tests/test_guided_decoding.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from yeji_ai.models.llm_schemas import (
    EasternFullLLMOutput,
    WesternFullLLMOutput,
    EasternInterpretationResult,
    CharacterMessage,
)
from yeji_ai.config import Settings


class TestSchemaJsonGeneration:
    """Pydantic 스키마에서 JSON 스키마 생성 테스트"""

    def test_eastern_full_schema_generation(self):
        """동양 사주 LLM 출력 스키마 생성 테스트"""
        schema = EasternFullLLMOutput.model_json_schema()

        # 스키마 기본 구조 확인
        assert "properties" in schema
        assert "required" in schema

        # 필수 필드 확인
        required_fields = schema.get("required", [])
        expected_required = [
            "personality",
            "strength",
            "weakness",
            "advice",
            "summary",
            "message",
            "badges",
            "lucky",
        ]
        for field in expected_required:
            assert field in required_fields, f"필수 필드 {field}가 누락됨"

    def test_western_full_schema_generation(self):
        """서양 점성술 LLM 출력 스키마 생성 테스트"""
        schema = WesternFullLLMOutput.model_json_schema()

        # 필수 필드 확인
        required_fields = schema.get("required", [])
        expected_required = [
            "personality",
            "strength",
            "weakness",
            "advice",
            "summary",
            "message",
            "badges",
            "lucky",
        ]
        for field in expected_required:
            assert field in required_fields, f"필수 필드 {field}가 누락됨"

    def test_schema_property_types(self):
        """스키마 속성 타입 확인"""
        schema = EasternFullLLMOutput.model_json_schema()
        properties = schema.get("properties", {})

        # 문자열 타입 확인
        assert properties["personality"]["type"] == "string"
        assert properties["strength"]["type"] == "string"
        assert properties["message"]["type"] == "string"

        # 배열 타입 확인
        assert properties["badges"]["type"] == "array"

    def test_schema_complexity_xgrammar_compatible(self):
        """스키마 복잡도 검증 (XGrammar 호환성)"""

        def get_max_depth(obj: dict, depth: int = 0) -> int:
            """스키마 중첩 깊이 계산"""
            if not isinstance(obj, dict):
                return depth
            max_child_depth = depth
            for v in obj.values():
                if isinstance(v, dict):
                    max_child_depth = max(max_child_depth, get_max_depth(v, depth + 1))
            return max_child_depth

        schema = EasternFullLLMOutput.model_json_schema()
        max_depth = get_max_depth(schema)

        # XGrammar는 깊이 6 이하 권장
        assert max_depth <= 6, f"스키마 중첩 깊이가 너무 깊음: {max_depth}"


class TestGuidedJsonPayload:
    """Guided JSON 페이로드 생성 테스트"""

    def test_json_schema_payload_format(self):
        """json_schema response_format 페이로드 형식 테스트"""
        schema = EasternFullLLMOutput.model_json_schema()
        schema_name = EasternFullLLMOutput.__name__.replace("_", "-").lower()

        # 예상 페이로드 형식
        expected_response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "schema": schema,
                "strict": True,
            },
        }

        # 검증
        assert expected_response_format["type"] == "json_schema"
        assert "json_schema" in expected_response_format
        assert expected_response_format["json_schema"]["strict"] is True
        assert expected_response_format["json_schema"]["name"] == "easternfullllmoutput"

    def test_json_object_payload_format(self):
        """json_object response_format 페이로드 형식 테스트 (폴백)"""
        expected_response_format = {"type": "json_object"}

        assert expected_response_format["type"] == "json_object"


class TestConfigSettings:
    """설정 관련 테스트"""

    def test_default_guided_json_enabled(self):
        """기본 guided_json 비활성화 확인 (v0.3.2 이후 기본값 변경)"""
        # 기본값으로 Settings 생성 - 프로덕션 안정성을 위해 기본 False
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()
            assert settings.use_guided_json is False  # v0.3.2: 기본 비활성화
            assert settings.guided_json_fallback is True

    def test_guided_json_disabled_via_env(self):
        """환경변수로 guided_json 비활성화"""
        with patch.dict("os.environ", {"USE_GUIDED_JSON": "false"}):
            settings = Settings()
            assert settings.use_guided_json is False

    def test_fallback_disabled_via_env(self):
        """환경변수로 폴백 비활성화"""
        with patch.dict("os.environ", {"GUIDED_JSON_FALLBACK": "false"}):
            settings = Settings()
            assert settings.guided_json_fallback is False


class TestLLMInterpreterGuidedJson:
    """LLMInterpreter guided_json 테스트"""

    @pytest.fixture
    def mock_settings_guided_enabled(self):
        """guided_json 활성화된 설정 모킹"""
        mock_settings = MagicMock()
        mock_settings.use_guided_json = True
        mock_settings.guided_json_fallback = True
        mock_settings.vllm_base_url = "http://localhost:8001/v1"
        mock_settings.vllm_model = "test-model"
        return mock_settings

    @pytest.fixture
    def mock_settings_guided_disabled(self):
        """guided_json 비활성화된 설정 모킹"""
        mock_settings = MagicMock()
        mock_settings.use_guided_json = False
        mock_settings.guided_json_fallback = True
        mock_settings.vllm_base_url = "http://localhost:8001/v1"
        mock_settings.vllm_model = "test-model"
        return mock_settings

    def _create_mock_response_content(
        self,
        personality: str = "테스트 성격",
        badges: list | None = None,
        lucky_color: str = "파랑",
    ) -> str:
        """유효한 JSON 응답 컨텐츠 생성"""
        if badges is None:
            badges = ["WOOD_STRONG", "YANG_DOMINANT"]
        return json.dumps(
            {
                "personality": personality,
                "strength": "테스트 강점",
                "weakness": "테스트 약점",
                "advice": "테스트 조언",
                "summary": "테스트 요약",
                "message": "테스트 메시지",
                "badges": badges,
                "lucky": {
                    "color": lucky_color,
                    "number": "7",
                    "item": "수정",
                    "direction": "북쪽",
                    "place": "물가",
                },
            },
            ensure_ascii=False,
        )

    @pytest.mark.asyncio
    async def test_guided_json_payload_sent(self, mock_settings_guided_enabled):
        """guided_json 활성화 시 json_schema 페이로드 전송 확인"""
        from yeji_ai.services.llm_interpreter import LLMInterpreter

        # 유효한 JSON 응답 생성
        valid_json_content = self._create_mock_response_content()

        # 응답 모킹
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": valid_json_content}}]
        }

        with patch("yeji_ai.services.llm_interpreter.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings_guided_enabled

            # _clean_llm_response 모킹 (원본 반환)
            with patch(
                "yeji_ai.services.llm_interpreter._clean_llm_response",
                side_effect=lambda x: x,
            ):
                with patch("httpx.AsyncClient") as mock_client_class:
                    mock_client = AsyncMock()
                    mock_client.post.return_value = mock_response
                    mock_client.__aenter__.return_value = mock_client
                    mock_client.__aexit__.return_value = None
                    mock_client_class.return_value = mock_client

                    interpreter = LLMInterpreter(
                        base_url="http://localhost:8001/v1",
                        model="test-model",
                    )

                    result = await interpreter._call_llm_structured(
                        system_prompt="테스트 시스템",
                        user_prompt="테스트 사용자",
                        response_schema=EasternFullLLMOutput,
                        use_guided_json=True,
                    )

                    # post 호출 검증
                    call_args = mock_client.post.call_args
                    payload = call_args.kwargs.get("json") or call_args[1].get("json")

                    # json_schema response_format 확인
                    assert payload["response_format"]["type"] == "json_schema"
                    assert "json_schema" in payload["response_format"]
                    assert payload["response_format"]["json_schema"]["strict"] is True

                    # 결과 검증
                    assert result.personality == "테스트 성격"
                    assert "WOOD_STRONG" in result.badges

    @pytest.mark.asyncio
    async def test_json_object_fallback_payload(self, mock_settings_guided_disabled):
        """guided_json 비활성화 시 json_object 페이로드 전송 확인"""
        from yeji_ai.services.llm_interpreter import LLMInterpreter

        # 유효한 JSON 응답 생성
        valid_json_content = self._create_mock_response_content(
            badges=["WOOD_STRONG"]
        )

        # 응답 모킹
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": valid_json_content}}]
        }

        with patch("yeji_ai.services.llm_interpreter.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings_guided_disabled

            # _clean_llm_response 모킹 (원본 반환)
            with patch(
                "yeji_ai.services.llm_interpreter._clean_llm_response",
                side_effect=lambda x: x,
            ):
                with patch("httpx.AsyncClient") as mock_client_class:
                    mock_client = AsyncMock()
                    mock_client.post.return_value = mock_response
                    mock_client.__aenter__.return_value = mock_client
                    mock_client.__aexit__.return_value = None
                    mock_client_class.return_value = mock_client

                    interpreter = LLMInterpreter(
                        base_url="http://localhost:8001/v1",
                        model="test-model",
                    )

                    result = await interpreter._call_llm_structured(
                        system_prompt="테스트 시스템",
                        user_prompt="테스트 사용자",
                        response_schema=EasternFullLLMOutput,
                        use_guided_json=False,
                    )

                    # post 호출 검증
                    call_args = mock_client.post.call_args
                    payload = call_args.kwargs.get("json") or call_args[1].get("json")

                    # json_object response_format 확인
                    assert payload["response_format"]["type"] == "json_object"
                    assert "json_schema" not in payload["response_format"]

                    # 결과 검증
                    assert result.personality == "테스트 성격"

    @pytest.mark.asyncio
    async def test_fallback_on_400_error(self, mock_settings_guided_enabled):
        """400 에러 시 json_object로 폴백 테스트"""
        from yeji_ai.services.llm_interpreter import LLMInterpreter

        # 첫 번째 호출: 400 에러 (json_schema 미지원)
        mock_error_response = MagicMock()
        mock_error_response.status_code = 400
        mock_error_response.text = "json_schema is not supported"

        # 두 번째 호출: 성공 응답
        valid_json_content = json.dumps(
            {
                "personality": "폴백 성격",
                "strength": "폴백 강점",
                "weakness": "폴백 약점",
                "advice": "폴백 조언",
                "summary": "폴백 요약",
                "message": "폴백 메시지",
                "badges": ["FIRE_STRONG"],
                "lucky": {
                    "color": "빨강",
                    "number": "9",
                    "item": "루비",
                    "direction": "남쪽",
                    "place": "양지",
                },
            },
            ensure_ascii=False,
        )

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.raise_for_status = MagicMock()
        mock_success_response.json.return_value = {
            "choices": [{"message": {"content": valid_json_content}}]
        }

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_error_response
            return mock_success_response

        with patch("yeji_ai.services.llm_interpreter.get_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_settings_guided_enabled

            # _clean_llm_response 모킹 (원본 반환)
            with patch(
                "yeji_ai.services.llm_interpreter._clean_llm_response",
                side_effect=lambda x: x,
            ):
                with patch("httpx.AsyncClient") as mock_client_class:
                    mock_client = AsyncMock()
                    mock_client.post.side_effect = mock_post
                    mock_client.__aenter__.return_value = mock_client
                    mock_client.__aexit__.return_value = None
                    mock_client_class.return_value = mock_client

                    interpreter = LLMInterpreter(
                        base_url="http://localhost:8001/v1",
                        model="test-model",
                    )

                    result = await interpreter._call_llm_structured(
                        system_prompt="테스트",
                        user_prompt="테스트",
                        response_schema=EasternFullLLMOutput,
                        use_guided_json=True,
                    )

                    # 결과 검증 (폴백 성공)
                    assert result.personality == "폴백 성격"
                    assert "FIRE_STRONG" in result.badges

                    # 두 번 호출 확인 (첫 번째: json_schema, 두 번째: json_object)
                    assert call_count == 2


class TestSchemaNameFormatting:
    """스키마 이름 포맷팅 테스트"""

    def test_schema_name_formatting(self):
        """스키마 이름이 올바르게 포맷팅되는지 확인"""
        test_cases = [
            ("EasternFullLLMOutput", "easternfullllmoutput"),
            ("Western_Full_Output", "western-full-output"),
            ("CharacterMessage", "charactermessage"),
        ]

        for original, expected in test_cases:
            formatted = original.replace("_", "-").lower()
            assert formatted == expected, f"{original} -> {formatted} (예상: {expected})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
