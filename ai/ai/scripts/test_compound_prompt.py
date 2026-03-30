"""복합 메시지 프롬프트 테스트 - 네트워크 협상식"""

import asyncio
import json
import re
import httpx

VLLM_URL = "http://13.125.68.166:8001/v1/chat/completions"
MODEL = "tellang/yeji-8b-rslora-v7"

# 한국어 필터
def is_clean_korean(text: str) -> bool:
    if not re.search(r'[가-힣]', text):
        return False
    foreign_ranges = [
        (0x0E00, 0x0E7F),  # Thai
        (0x0600, 0x06FF),  # Arabic
        (0x0590, 0x05FF),  # Hebrew
        (0x3040, 0x309F),  # Hiragana
        (0x30A0, 0x30FF),  # Katakana
    ]
    for char in text:
        code = ord(char)
        for start, end in foreign_ranges:
            if start <= code <= end:
                return False
    return True

# 테스트 케이스
TEST_CASES = [
    # (요소1, 요소2, 카테고리, 요소1_이름, 요소2_이름)
    ("FIRE", "WOOD", "MONEY", "화(火)", "목(木)"),
    ("WATER", "METAL", "LOVE", "수(水)", "금(金)"),
    ("EARTH", "FIRE", "CAREER", "토(土)", "화(火)"),
]

async def test_compound_prompt(elem1: str, elem2: str, category: str, name1: str, name2: str):
    """복합 메시지 프롬프트 테스트"""
    
    category_kr = {
        "GENERAL": "총운", "LOVE": "연애운", "MONEY": "금전운",
        "CAREER": "직장운", "HEALTH": "건강운", "STUDY": "학업운"
    }
    
    elem_meanings = {
        "FIRE": "열정, 추진력, 활력",
        "WOOD": "성장, 창의력, 시작",
        "WATER": "지혜, 유연성, 적응",
        "METAL": "결단력, 정리, 수확",
        "EARTH": "안정, 신뢰, 중재",
    }
    
    system = f"""운세 복합 메시지 생성기. 두 오행 요소를 결합한 해석.

[절대 규칙]
1. 한국어만 (외국어/특수문자 금지)
2. 한 문장, 40-60자
3. 두 요소 모두 언급 필수
4. 구조: "[요소1] 덕분에 [효과1], [요소2]도 있어서 [효과2]!"
5. 마침표 또는 느낌표로 끝
6. JSON 배열로 출력

[요소 정보]
- 요소1: {name1} - {elem_meanings[elem1]}
- 요소2: {name2} - {elem_meanings[elem2]}
- 카테고리: {category_kr[category]}

[출력 예시]
["{name1}의 열정과 {name2}의 성장력이 만나 {category_kr[category]}이 좋아요!", "..."]"""

    user = f"""{name1}와 {name2} 기운이 함께 있을 때 {category_kr[category]} 메시지 3개.
JSON 배열만 출력:"""

    print(f"\n{'='*60}")
    print(f"테스트: {name1} + {name2} → {category_kr[category]}")
    print(f"{'='*60}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            VLLM_URL,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": 200,
                "temperature": 0.7,
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        print(f"\n원본 응답:\n{content}")
        
        # JSON 파싱
        try:
            match = re.search(r'\[.*?\]', content, re.DOTALL)
            if match:
                messages = json.loads(match.group())
                print(f"\n파싱된 메시지:")
                for i, msg in enumerate(messages, 1):
                    clean = is_clean_korean(msg)
                    has_elem1 = name1.split("(")[0] in msg
                    has_elem2 = name2.split("(")[0] in msg
                    length = len(msg)
                    status = "✓" if clean and has_elem1 and has_elem2 and 30 <= length <= 70 else "✗"
                    print(f"  {i}. [{status}] ({length}자) {msg}")
                    if not has_elem1:
                        print(f"     ⚠ {name1} 미포함")
                    if not has_elem2:
                        print(f"     ⚠ {name2} 미포함")
                return messages
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 실패: {e}")
            return []

async def main():
    print("복합 메시지 프롬프트 품질 테스트")
    print("=" * 60)
    
    for elem1, elem2, category, name1, name2 in TEST_CASES:
        await test_compound_prompt(elem1, elem2, category, name1, name2)
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
