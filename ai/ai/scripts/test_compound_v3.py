"""복합 메시지 테스트 v3 - 한 번에 하나씩, 명확한 예시"""

import asyncio
import re
import httpx

VLLM_URL = "http://13.125.68.166:8001/v1/chat/completions"
MODEL = "tellang/yeji-8b-rslora-v7"

def clean_response(text: str) -> str:
    """응답 정제 - 첫 문장만 추출"""
    text = text.strip().strip('"').strip("'").strip()
    # 첫 문장만
    for sep in ['.', '!', '?']:
        if sep in text:
            text = text.split(sep)[0] + sep
            break
    # 외래 문자 제거
    result = []
    for char in text:
        code = ord(char)
        if code < 0x0E00 or code > 0x0E7F:  # Thai 제외
            if code < 0x0600 or code > 0x06FF:  # Arabic 제외
                result.append(char)
    return ''.join(result).strip()

TEST_CASES = [
    ("화", "목", "금전운"),
    ("수", "금", "연애운"),
    ("토", "화", "직장운"),
    ("목", "수", "학업운"),
    ("금", "토", "건강운"),
]

async def test_single(name1: str, name2: str, category: str):
    """단일 메시지 생성 테스트"""
    
    # 아주 구체적인 프롬프트
    system = f"""당신은 사주 운세 전문가입니다.

두 오행 기운을 조합해서 {category} 메시지를 작성하세요.

[조건]
- "{name1}"와 "{name2}" 두 글자가 반드시 문장에 포함
- 40-60자 한 문장
- 마침표로 끝

[예시]
- {name1}의 기운과 {name2}의 힘이 만나 {category}이 상승합니다.
- {name1}가 강하고 {name2}도 있어서 좋은 흐름입니다."""

    user = f"""{name1}와 {name2} 기운의 {category} 메시지 하나만 작성:"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            VLLM_URL,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": 100,
                "temperature": 0.7,
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        
        # 정제
        msg = clean_response(content)
        
        # 검증
        has_e1 = name1 in msg
        has_e2 = name2 in msg
        length = len(msg)
        ok = has_e1 and has_e2 and 25 <= length <= 80
        
        status = "✓" if ok else "✗"
        print(f"[{status}] {name1}+{name2} → {category}: ({length}자) {msg}")
        if not has_e1:
            print(f"    ⚠ '{name1}' 미포함")
        if not has_e2:
            print(f"    ⚠ '{name2}' 미포함")
        
        return ok, msg

async def main():
    print("복합 메시지 v3 테스트 (단일 생성)")
    print("=" * 70)
    
    success = 0
    results = []
    
    for name1, name2, category in TEST_CASES:
        ok, msg = await test_single(name1, name2, category)
        if ok:
            success += 1
            results.append((name1, name2, category, msg))
        await asyncio.sleep(0.3)
    
    print(f"\n{'='*70}")
    print(f"성공률: {success}/{len(TEST_CASES)} ({success/len(TEST_CASES)*100:.0f}%)")
    
    if results:
        print(f"\n성공한 메시지:")
        for name1, name2, category, msg in results:
            print(f"  - {name1}+{name2} ({category}): {msg}")

if __name__ == "__main__":
    asyncio.run(main())
