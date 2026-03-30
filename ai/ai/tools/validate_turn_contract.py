"""턴 계약 검증 도구

Fortune Chat Turn Contract JSON 검증 스크립트

Usage:
    python tools/validate_turn_contract.py samples/fortune_chat_turn/turn1_sample_01.json
    python tools/validate_turn_contract.py --all samples/fortune_chat_turn/
"""

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# 상수 정의
# ============================================================

VALID_SPEAKERS = {"EAST", "WEST"}

VALID_EMOTION_CODES = {
    "NEUTRAL",
    "WARM",
    "EXCITED",
    "THOUGHTFUL",
    "ENCOURAGING",
    "PLAYFUL",
    "MYSTERIOUS",
    "SURPRISED",
    "CONCERNED",
    "CONFIDENT",
    "GENTLE",
    "CURIOUS",
}

VALID_CATEGORIES = {"total", "love", "wealth", "career", "health"}

VALID_INPUT_TYPES = {"text", "choice", "date", "datetime"}


# ============================================================
# 결과 클래스
# ============================================================


@dataclass
class ValidationError:
    """검증 에러"""

    field: str
    message: str
    code: str


@dataclass
class ValidationResult:
    """검증 결과"""

    valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, field_path: str, message: str, code: str):
        """에러 추가"""
        self.errors.append(ValidationError(field=field_path, message=message, code=code))
        self.valid = False

    def add_warning(self, message: str):
        """경고 추가"""
        self.warnings.append(message)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "valid": self.valid,
            "errors": [
                {"field": e.field, "message": e.message, "code": e.code} for e in self.errors
            ],
            "warnings": self.warnings,
        }


# ============================================================
# 검증 함수
# ============================================================


def validate_turn_response(data: dict[str, Any]) -> ValidationResult:
    """TurnResponse 검증

    Args:
        data: JSON 데이터

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    # 1. 최상위 필수 필드 검증
    _validate_top_level_fields(data, result)

    if not result.valid:
        return result  # 기본 구조 오류 시 조기 반환

    # 2. bubbles 검증
    _validate_bubbles(data.get("bubbles", []), result)

    # 3. turn_end 검증
    _validate_turn_end(data.get("turn_end", {}), result)

    # 4. meta 검증
    _validate_meta(data.get("meta", {}), result)

    # 5. 경고 검증 (필수 검증 통과 후)
    if result.valid:
        _check_warnings(data, result)

    return result


def _validate_top_level_fields(data: dict[str, Any], result: ValidationResult):
    """최상위 필드 검증"""
    # session_id
    session_id = data.get("session_id")
    if not session_id or not isinstance(session_id, str):
        result.add_error("session_id", "session_id는 필수이며 문자열이어야 함", "MISSING_REQUIRED_FIELD")
    elif len(session_id) > 100:
        result.add_error("session_id", "session_id는 100자 이하여야 함", "INVALID_TYPE")

    # turn_id
    turn_id = data.get("turn_id")
    if turn_id is None or not isinstance(turn_id, int):
        result.add_error("turn_id", "turn_id는 필수이며 정수여야 함", "MISSING_REQUIRED_FIELD")
    elif turn_id < 1:
        result.add_error("turn_id", "turn_id는 1 이상이어야 함", "INVALID_TYPE")

    # bubbles
    bubbles = data.get("bubbles")
    if bubbles is None:
        result.add_error("bubbles", "bubbles는 필수 필드", "MISSING_REQUIRED_FIELD")
    elif not isinstance(bubbles, list):
        result.add_error("bubbles", "bubbles는 배열이어야 함", "INVALID_TYPE")
    elif len(bubbles) < 1:
        result.add_error("bubbles", "bubbles는 최소 1개 필수", "EMPTY_BUBBLES")

    # turn_end
    if "turn_end" not in data:
        result.add_error("turn_end", "turn_end는 필수 필드", "MISSING_REQUIRED_FIELD")

    # meta
    if "meta" not in data:
        result.add_error("meta", "meta는 필수 필드", "MISSING_REQUIRED_FIELD")


def _validate_bubbles(bubbles: list[dict], result: ValidationResult):
    """bubbles 배열 검증"""
    if not bubbles:
        return

    bubble_ids = set()

    for i, bubble in enumerate(bubbles):
        prefix = f"bubbles[{i}]"

        # bubble_id
        bubble_id = bubble.get("bubble_id")
        if not bubble_id:
            result.add_error(f"{prefix}.bubble_id", "bubble_id는 필수", "MISSING_REQUIRED_FIELD")
        elif bubble_id in bubble_ids:
            result.add_error(f"{prefix}.bubble_id", "bubble_id 중복", "DUPLICATE_BUBBLE_ID")
        else:
            bubble_ids.add(bubble_id)

        # speaker
        speaker = bubble.get("speaker")
        if speaker not in VALID_SPEAKERS:
            result.add_error(
                f"{prefix}.speaker",
                f"speaker는 {VALID_SPEAKERS} 중 하나여야 함",
                "INVALID_SPEAKER",
            )

        # text
        text = bubble.get("text")
        if not text or not isinstance(text, str):
            result.add_error(f"{prefix}.text", "text는 필수이며 문자열이어야 함", "EMPTY_TEXT")
        elif len(text) > 500:
            result.add_error(f"{prefix}.text", "text는 500자 이하여야 함", "TEXT_TOO_LONG")

        # emotion
        emotion = bubble.get("emotion", {})
        if not emotion:
            result.add_error(f"{prefix}.emotion", "emotion은 필수", "MISSING_REQUIRED_FIELD")
        else:
            code = emotion.get("code")
            if code not in VALID_EMOTION_CODES:
                result.add_error(
                    f"{prefix}.emotion.code",
                    f"emotion.code는 {VALID_EMOTION_CODES} 중 하나여야 함",
                    "INVALID_EMOTION_CODE",
                )

            intensity = emotion.get("intensity")
            if intensity is None:
                result.add_error(
                    f"{prefix}.emotion.intensity",
                    "emotion.intensity는 필수",
                    "MISSING_REQUIRED_FIELD",
                )
            elif not isinstance(intensity, (int, float)) or not (0 <= intensity <= 1):
                result.add_error(
                    f"{prefix}.emotion.intensity",
                    "emotion.intensity는 0~1 사이여야 함",
                    "INVALID_INTENSITY",
                )

        # timestamp (선택적 검증)
        timestamp = bubble.get("timestamp")
        if timestamp:
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                result.add_error(
                    f"{prefix}.timestamp", "timestamp는 ISO 8601 형식이어야 함", "INVALID_TYPE"
                )


def _validate_turn_end(turn_end: dict, result: ValidationResult):
    """turn_end 검증"""
    if not turn_end:
        return

    turn_type = turn_end.get("type")

    if turn_type not in ("await_user_input", "completed"):
        result.add_error(
            "turn_end.type",
            "turn_end.type은 await_user_input 또는 completed여야 함",
            "INVALID_TURN_END_TYPE",
        )
        return

    # 상호 배타 규칙 검증
    has_user_prompt = "user_prompt" in turn_end and turn_end["user_prompt"]
    has_closure = "closure" in turn_end and turn_end["closure"]

    if turn_type == "await_user_input":
        if not has_user_prompt:
            result.add_error(
                "turn_end.user_prompt",
                "await_user_input일 때 user_prompt 필수",
                "MISSING_REQUIRED_FIELD",
            )
        if has_closure:
            result.add_error(
                "turn_end.closure",
                "await_user_input일 때 closure 금지",
                "MUTUAL_EXCLUSION_VIOLATION",
            )
        else:
            _validate_user_prompt(turn_end.get("user_prompt", {}), result)

    elif turn_type == "completed":
        if not has_closure:
            result.add_error(
                "turn_end.closure",
                "completed일 때 closure 필수",
                "MISSING_REQUIRED_FIELD",
            )
        if has_user_prompt:
            result.add_error(
                "turn_end.user_prompt",
                "completed일 때 user_prompt 금지",
                "MUTUAL_EXCLUSION_VIOLATION",
            )
        else:
            _validate_closure(turn_end.get("closure", {}), result)


def _validate_user_prompt(user_prompt: dict, result: ValidationResult):
    """user_prompt 검증"""
    if not user_prompt:
        return

    if not user_prompt.get("prompt_id"):
        result.add_error(
            "turn_end.user_prompt.prompt_id",
            "prompt_id는 필수",
            "MISSING_REQUIRED_FIELD",
        )

    if not user_prompt.get("text"):
        result.add_error(
            "turn_end.user_prompt.text",
            "text는 필수",
            "MISSING_REQUIRED_FIELD",
        )

    input_schema = user_prompt.get("input_schema", {})
    if not input_schema:
        result.add_error(
            "turn_end.user_prompt.input_schema",
            "input_schema는 필수",
            "MISSING_REQUIRED_FIELD",
        )
    elif input_schema.get("type") not in VALID_INPUT_TYPES:
        result.add_error(
            "turn_end.user_prompt.input_schema.type",
            f"input_schema.type은 {VALID_INPUT_TYPES} 중 하나여야 함",
            "INVALID_TYPE",
        )


def _validate_closure(closure: dict, result: ValidationResult):
    """closure 검증"""
    if not closure:
        return

    # summary
    summary = closure.get("summary")
    if not summary or not isinstance(summary, list) or len(summary) < 1:
        result.add_error(
            "turn_end.closure.summary",
            "summary는 최소 1개 필수",
            "MISSING_REQUIRED_FIELD",
        )

    # next_steps (빈 배열 허용)
    if "next_steps" not in closure:
        result.add_error(
            "turn_end.closure.next_steps",
            "next_steps는 필수 (빈 배열 허용)",
            "MISSING_REQUIRED_FIELD",
        )

    # upgrade_hook
    upgrade_hook = closure.get("upgrade_hook")
    if not upgrade_hook:
        result.add_error(
            "turn_end.closure.upgrade_hook",
            "upgrade_hook은 필수",
            "MISSING_REQUIRED_FIELD",
        )
    elif "enabled" not in upgrade_hook:
        result.add_error(
            "turn_end.closure.upgrade_hook.enabled",
            "upgrade_hook.enabled는 필수",
            "MISSING_REQUIRED_FIELD",
        )

    # end_marker
    if closure.get("end_marker") != "END_SESSION":
        result.add_error(
            "turn_end.closure.end_marker",
            'end_marker는 반드시 "END_SESSION"이어야 함',
            "INVALID_END_MARKER",
        )


def _validate_meta(meta: dict, result: ValidationResult):
    """meta 검증"""
    if not meta:
        return

    # current_turn
    current_turn = meta.get("current_turn")
    if current_turn is None or not isinstance(current_turn, int) or current_turn < 1:
        result.add_error("meta.current_turn", "current_turn은 1 이상의 정수여야 함", "INVALID_TYPE")

    # base_turns
    base_turns = meta.get("base_turns")
    if base_turns is None or not isinstance(base_turns, int) or base_turns < 1:
        result.add_error("meta.base_turns", "base_turns는 1 이상의 정수여야 함", "INVALID_TYPE")

    # max_turns
    max_turns = meta.get("max_turns")
    if max_turns is None or not isinstance(max_turns, int) or max_turns < 1:
        result.add_error("meta.max_turns", "max_turns는 1 이상의 정수여야 함", "INVALID_TYPE")
    elif base_turns and max_turns < base_turns:
        result.add_error(
            "meta.max_turns",
            "max_turns는 base_turns 이상이어야 함",
            "TURN_LIMIT_EXCEEDED",
        )

    # current_turn vs max_turns
    if current_turn and max_turns and current_turn > max_turns:
        result.add_error(
            "meta.current_turn",
            "current_turn은 max_turns를 초과할 수 없음",
            "TURN_LIMIT_EXCEEDED",
        )

    # category
    category = meta.get("category")
    if category not in VALID_CATEGORIES:
        result.add_error(
            "meta.category",
            f"category는 {VALID_CATEGORIES} 중 하나여야 함",
            "INVALID_CATEGORY",
        )


def _check_warnings(data: dict, result: ValidationResult):
    """경고 검증"""
    bubbles = data.get("bubbles", [])

    # 버블 개수 경고
    if len(bubbles) > 3:
        result.add_warning(f"bubbles 개수가 3개를 초과함 (현재: {len(bubbles)}개)")

    # 연속 speaker 경고
    consecutive = 1
    for i in range(1, len(bubbles)):
        if bubbles[i].get("speaker") == bubbles[i - 1].get("speaker"):
            consecutive += 1
            if consecutive >= 3:
                result.add_warning("같은 speaker가 연속 3회 이상 등장")
                break
        else:
            consecutive = 1

    # text 길이 경고
    for bubble in bubbles:
        text = bubble.get("text", "")
        if len(text) > 300:
            result.add_warning(f"버블 텍스트가 300자 초과 ({bubble.get('bubble_id')})")

    # intensity 극단값 경고
    for bubble in bubbles:
        intensity = bubble.get("emotion", {}).get("intensity", 0.5)
        if intensity <= 0.1 or intensity >= 0.95:
            result.add_warning(f"intensity 극단값 사용 ({bubble.get('bubble_id')})")

    # 프리미엄인데 upgrade_hook 활성화 경고
    meta = data.get("meta", {})
    turn_end = data.get("turn_end", {})
    if meta.get("is_premium") and turn_end.get("type") == "completed":
        closure = turn_end.get("closure", {})
        if closure.get("upgrade_hook", {}).get("enabled"):
            result.add_warning("프리미엄 사용자인데 upgrade_hook이 활성화됨")


# ============================================================
# CLI
# ============================================================


def validate_file(file_path: str) -> ValidationResult:
    """파일 검증"""
    path = Path(file_path)
    if not path.exists():
        result = ValidationResult()
        result.add_error("file", f"파일을 찾을 수 없음: {file_path}", "FILE_NOT_FOUND")
        return result

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result = ValidationResult()
        result.add_error("json", f"JSON 파싱 오류: {e}", "INVALID_JSON")
        return result

    return validate_turn_response(data)


def main():
    """CLI 진입점"""
    if len(sys.argv) < 2:
        print("Usage: python validate_turn_contract.py <file.json>")
        print("       python validate_turn_contract.py --all <directory>")
        sys.exit(1)

    if sys.argv[1] == "--all":
        if len(sys.argv) < 3:
            print("Error: --all 옵션 사용 시 디렉토리 경로 필요")
            sys.exit(1)

        directory = Path(sys.argv[2])
        if not directory.is_dir():
            print(f"Error: 디렉토리가 아님: {directory}")
            sys.exit(1)

        all_valid = True
        for json_file in directory.glob("*.json"):
            print(f"\n--- {json_file.name} ---")
            result = validate_file(str(json_file))
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
            if not result.valid:
                all_valid = False

        sys.exit(0 if all_valid else 1)
    else:
        result = validate_file(sys.argv[1])
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        sys.exit(0 if result.valid else 1)


if __name__ == "__main__":
    main()
