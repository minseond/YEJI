#!/usr/bin/env python3
"""SSH를 통해 AWS vLLM에 직접 요청

개선 사항:
- stop 토큰 추가 (응답 반복 방지)
- JSON 후처리 (첫 번째 완전한 JSON만 추출)
- 스키마 검증 (Pydantic)
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# 프롬프트 가져오기
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ai" / "src"))
from yeji_ai.prompts.fortune_prompts import (
    EASTERN_SYSTEM_PROMPT,
    WESTERN_SYSTEM_PROMPT,
    build_eastern_generation_prompt,
    build_western_generation_prompt,
)

SSH_KEY = "~/Downloads/yeji-gpu-key.pem"
SSH_HOST = "ubuntu@43.201.17.48"
VLLM_MODEL = "tellang/yeji-8b-rslora-v7-AWQ"

# stop 토큰: 응답 반복 방지
STOP_TOKENS = [
    "\n\nuser",
    "\nassistant",
    "\n\nassistant",
    "<|im_end|>",
    "<|endoftext|>",
    "</s>",
]


def extract_first_json(text: str) -> dict[str, Any]:
    """텍스트에서 첫 번째 완전한 JSON 객체만 추출.

    Args:
        text: LLM 원시 출력 (반복된 JSON, 쓰레기 텍스트 포함 가능)

    Returns:
        파싱된 JSON 딕셔너리

    Raises:
        ValueError: JSON 추출 실패
    """
    # 방법 1: 정규식으로 첫 번째 { ... } 블록 추출
    # 중첩된 중괄호를 처리하기 위해 균형 맞춤
    depth = 0
    start = -1
    for i, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start != -1:
                json_str = text[start : i + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # 이 블록이 유효하지 않으면 다음 시도
                    start = -1
                    continue

    # 방법 2: 단순 find/rfind (fallback)
    start = text.find("{")
    if start == -1:
        raise ValueError("JSON 객체를 찾을 수 없습니다")

    # 첫 번째 "user" 또는 "assistant" 토큰 전까지만
    end_markers = ["\nuser", "\nassistant", "<|im_end|>"]
    end = len(text)
    for marker in end_markers:
        pos = text.find(marker, start)
        if pos != -1 and pos < end:
            end = pos

    # 마지막 } 찾기
    json_candidate = text[start:end]
    last_brace = json_candidate.rfind("}")
    if last_brace == -1:
        raise ValueError("JSON 종료 괄호를 찾을 수 없습니다")

    json_str = json_candidate[: last_brace + 1]

    # 다국어 쓰레기 문자 제거 (태국어, 아랍어 등)
    json_str = re.sub(r"[^\x00-\x7F가-힣一-龥\s{}\"\':\[\],\.\-\d]", "", json_str)

    return json.loads(json_str)


def call_vllm_via_ssh(system_prompt: str, user_prompt: str) -> tuple[str, dict]:
    """SSH를 통해 vLLM API 호출.

    Returns:
        (raw_response, parsed_json) 튜플
    """
    payload = {
        "model": VLLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 2048,
        "temperature": 0.7,
        "top_p": 0.9,
        "stop": STOP_TOKENS,  # 중요: stop 토큰 추가
    }

    # JSON을 이스케이프하여 curl 명령어 생성
    payload_json = json.dumps(payload).replace('"', '\\"').replace("'", "'\\''")

    curl_cmd = (
        f'curl -s -X POST http://localhost:8001/v1/chat/completions '
        f'-H "Content-Type: application/json" -d "{payload_json}"'
    )
    ssh_cmd = f"ssh -i {SSH_KEY} -o StrictHostKeyChecking=no {SSH_HOST} '{curl_cmd}'"

    result = subprocess.run(
        ssh_cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=180,
    )

    if result.returncode != 0:
        raise Exception(f"SSH failed: {result.stderr}")

    response = json.loads(result.stdout)
    raw_content = response["choices"][0]["message"]["content"]

    # JSON 추출 및 파싱
    parsed = extract_first_json(raw_content)

    return raw_content, parsed


def validate_east_response(response: dict) -> list[str]:
    """EAST 응답 스키마 검증.

    Returns:
        발견된 오류 목록
    """
    errors = []

    # element 검증
    valid_elements = {"WOOD", "FIRE", "EARTH", "METAL", "WATER"}
    if response.get("element") not in valid_elements:
        errors.append(f"element: {response.get('element')} (유효값: {valid_elements})")

    # chart 구조 검증
    chart = response.get("chart", {})
    if isinstance(chart, list):
        errors.append("chart: 배열이 아닌 객체여야 함")
    else:
        for key in ["year", "month", "day", "hour"]:
            if key not in chart:
                errors.append(f"chart.{key} 누락")
            elif isinstance(chart.get(key), dict):
                pillar = chart[key]
                if "gan" not in pillar:
                    errors.append(f"chart.{key}.gan 누락")
                if "ji" not in pillar:
                    errors.append(f"chart.{key}.ji 누락")

    # ten_gods 검증
    ten_gods = response.get("stats", {}).get("ten_gods", {})
    valid_codes = {
        "BI_GYEON",
        "GANG_JAE",
        "SIK_SIN",
        "SANG_GWAN",
        "PYEON_JAE",
        "JEONG_JAE",
        "PYEON_GWAN",
        "JEONG_GWAN",
        "PYEON_IN",
        "JEONG_IN",
        "ETC",
    }
    if "list" in ten_gods:
        for item in ten_gods["list"]:
            code = item.get("code")
            if code and code not in valid_codes:
                errors.append(f"ten_gods.code: {code} (유효값: {valid_codes})")

    # final_verdict 검증
    if "final_verdict" not in response:
        errors.append("final_verdict 누락")

    return errors


def validate_west_response(response: dict) -> list[str]:
    """WEST 응답 스키마 검증.

    Returns:
        발견된 오류 목록
    """
    errors = []

    # element 검증
    valid_elements = {"FIRE", "EARTH", "AIR", "WATER"}
    if response.get("element") not in valid_elements:
        errors.append(f"element: {response.get('element')} (유효값: {valid_elements})")

    stats = response.get("stats", {})

    # element_4_distribution 검증
    elem_dist = stats.get("element_4_distribution", [])
    if isinstance(elem_dist, dict):
        errors.append("element_4_distribution: 객체가 아닌 배열이어야 함")
    elif isinstance(elem_dist, list) and len(elem_dist) != 4:
        errors.append(f"element_4_distribution: 4개 항목 필요 (현재: {len(elem_dist)})")

    # modality_3_distribution 검증
    mod_dist = stats.get("modality_3_distribution", [])
    valid_modality = {"CARDINAL", "FIXED", "MUTABLE"}
    if isinstance(mod_dist, dict):
        errors.append("modality_3_distribution: 객체가 아닌 배열이어야 함")
    elif isinstance(mod_dist, list):
        for item in mod_dist:
            code = item.get("code")
            if code and code not in valid_modality:
                errors.append(f"modality.code: {code} (유효값: {valid_modality})")

    # keywords 검증
    keywords = stats.get("keywords", [])
    valid_keywords = {
        "EMPATHY",
        "INTUITION",
        "IMAGINATION",
        "BOUNDARY",
        "LEADERSHIP",
        "PASSION",
        "ANALYSIS",
        "STABILITY",
        "COMMUNICATION",
        "INNOVATION",
    }
    for item in keywords:
        # "name" 대신 "code" 필드 사용 확인
        if "name" in item and "code" not in item:
            errors.append("keywords: 'name' 대신 'code' 필드 사용 필요")
        code = item.get("code")
        if code and code not in valid_keywords:
            errors.append(f"keywords.code: {code} (유효값: {valid_keywords})")

    # fortune_content 검증
    fc = response.get("fortune_content", {})
    if "overview" not in fc:
        errors.append("fortune_content.overview 누락")
    if "advice" not in fc:
        errors.append("fortune_content.advice 누락")

    return errors


def generate_response(type_: str, birth_data: dict) -> tuple[str, dict, list[str]]:
    """응답 생성 및 검증.

    Returns:
        (raw_response, parsed_json, validation_errors) 튜플
    """
    if type_ == "east":
        user_prompt = build_eastern_generation_prompt(
            birth_data["year"],
            birth_data["month"],
            birth_data["day"],
            birth_data["hour"],
            birth_data.get("gender", "unknown"),
        )
        raw, parsed = call_vllm_via_ssh(EASTERN_SYSTEM_PROMPT, user_prompt)
        errors = validate_east_response(parsed)
    else:
        user_prompt = build_western_generation_prompt(
            birth_data["year"],
            birth_data["month"],
            birth_data["day"],
            birth_data.get("hour", 12),
        )
        raw, parsed = call_vllm_via_ssh(WESTERN_SYSTEM_PROMPT, user_prompt)
        errors = validate_west_response(parsed)

    return raw, parsed, errors


def main():
    output_dir = Path(__file__).parent / "actual"
    output_dir.mkdir(exist_ok=True)
    (output_dir / "east").mkdir(exist_ok=True)
    (output_dir / "west").mkdir(exist_ok=True)
    (output_dir / "raw").mkdir(exist_ok=True)

    # 테스트 케이스
    cases = [
        {
            "id": "case_01",
            "east": {"year": 1990, "month": 3, "day": 15, "hour": 14, "gender": "male"},
            "west": {"year": 1990, "month": 2, "day": 5, "hour": 12},
        },
    ]

    print(f"Model: {VLLM_MODEL}")
    print(f"Stop tokens: {STOP_TOKENS[:3]}...")
    print("=" * 60)

    for case in cases:
        case_id = case["id"]
        print(f"\n[{case_id}]")
        print("-" * 50)

        # EAST 응답
        print("EAST 생성 중...")
        try:
            raw, parsed, errors = generate_response("east", case["east"])

            # Raw 응답 저장 (디버깅용)
            raw_file = output_dir / "raw" / f"{case_id}_east_raw.txt"
            raw_file.write_text(raw, encoding="utf-8")

            # 파싱된 JSON 저장
            east_file = output_dir / "east" / f"{case_id}_actual.json"
            east_file.write_text(
                json.dumps(parsed, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(f"  ✓ 저장: {east_file}")
            print(f"  element: {parsed.get('element')}")
            if errors:
                print(f"  ⚠ 검증 오류 {len(errors)}개:")
                for e in errors[:5]:
                    print(f"    - {e}")
            else:
                print("  ✓ 스키마 검증 통과")

        except Exception as e:
            print(f"  ✗ EAST 실패: {e}")

        # WEST 응답
        print("\nWEST 생성 중...")
        try:
            raw, parsed, errors = generate_response("west", case["west"])

            # Raw 응답 저장 (디버깅용)
            raw_file = output_dir / "raw" / f"{case_id}_west_raw.txt"
            raw_file.write_text(raw, encoding="utf-8")

            # 파싱된 JSON 저장
            west_file = output_dir / "west" / f"{case_id}_actual.json"
            west_file.write_text(
                json.dumps(parsed, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(f"  ✓ 저장: {west_file}")
            print(f"  element: {parsed.get('element')}")
            if errors:
                print(f"  ⚠ 검증 오류 {len(errors)}개:")
                for e in errors[:5]:
                    print(f"    - {e}")
            else:
                print("  ✓ 스키마 검증 통과")

        except Exception as e:
            print(f"  ✗ WEST 실패: {e}")

    print("\n" + "=" * 60)
    print("완료! actual/ 폴더에서 결과를 확인하세요.")
    print("raw/ 폴더에서 원시 응답을 확인할 수 있습니다.")


if __name__ == "__main__":
    main()
