"""복합 메시지 프롬프트 테스트 v2"""

import asyncio
import json
import re
import httpx

VLLM_URL = "http://13.125.68.166:8001/v1/chat/completions"
MODEL = "tellang/yeji-8b-rslora-v7"

def is_clean_korean(text: str) -> bool:
    if not isinstance(text, str):
        return False
    if not re.search(r'[가-힣]', text):
        return False
    foreign_ranges = [
        (0x0E00, 0x0E7F), (0x0600, 0x06FF), (0x0590, 0x05FF),
        (0x3040, 0x309F), (0x30A0, 0x30FF),
    ]
    for char in text:
        code = ord(char)
        for start, end in foreign_ranges:
            if start <= code <= end:
                return False
    return True

TEST_CASES = [
    ("FIRE", "WOOD", "MONEY", "화", "목"),
    ("WATER", "METAL", "LOVE", "수", "금"),
    ("EARTH", "FIRE", "CAREER", "토", "화"),
    ("WOOD", "WATER", "STUDY", "목", "수"),
]

async def test_v2(elem1: str, elem2: str, category: str, name1: str, name2: str):
    category_kr = {
        "GENERAL": "총운", "LOVE": "연애운", "MONEY": "금전운",
        "CAREER": "직장운", "HEALTH": "건강운", "STUDY": "학업운"
    }[category]
    
    system = f"""사주 운세 메시지 작성. 오행 두 가지를 조합해서 해석.

[필수 규칙]
1. 한국어만 사용
2. 반드시 "{name1}"와 "{name2}" 두 글자를 문장에 포함
3. 40-60자 한 문장
4. 마침표로 끝
5. JSON 배열 3개

[좋은 예시]
- "{name1}의 열정과 {name2}의 성장력이 만나 {category_kr}이 좋아집니다."
- "{name1}가 강하고 {name2}도 있어서 기회가 열립니다."

[나쁜 예시]
- "열정과 추진력이 좋습니다." (요소 이름 없음 - 금지)"""

    user = f"""{category_kr} 메시지. "{name1}"와 "{name2}" 반드시 포함.
JSON 배열 3개:"""

    print(f"\n{'='*60}")
    print(f"테스트: {name1} + {name2} → {category_kr}")
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
                "max_tokens": 250,
                "temperature": 0.6,
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        
        # JSON 추출
        match = re.search(r'\[.*?\]', content, re.DOTALL)
        if not match:
            print(f"JSON 파싱 실패: {content[:100]}")
            return 0
            
        try:
            messages = json.loads(match.group())
        except:
            print(f"JSON 파싱 실패")
            return 0
            
        print(f"\n결과:")
        success = 0
        for i, msg in enumerate(messages[:3], 1):
            if not isinstance(msg, str):
                print(f"  {i}. [✗] 문자열 아님: {type(msg)}")
                continue
                
            has_e1 = name1 in msg
            has_e2 = name2 in msg
            clean = is_clean_korean(msg)
            length = len(msg)
            ok = clean and has_e1 and has_e2 and 30 <= length <= 70
            
            status = "✓" if ok else "✗"
            if ok:
                success += 1
            print(f"  {i}. [{status}] ({length}자) {msg}")
            if not has_e1:
                print(f"     ⚠ '{name1}' 미포함")
            if not has_e2:
                print(f"     ⚠ '{name2}' 미포함")
        
        print(f"\n성공률: {success}/3")
        return success

async def main():
    print("복합 메시지 프롬프트 v2 테스트")
    print("=" * 60)
    
    total = 0
    for case in TEST_CASES:
        result = await test_v2(*case)
        total += result
        await asyncio.sleep(0.3)
    
    print(f"\n{'='*60}")
    print(f"총 성공률: {total}/{len(TEST_CASES)*3} ({total/(len(TEST_CASES)*3)*100:.0f}%)")

if __name__ == "__main__":
    asyncio.run(main())
