# 화투 카드점괘 API 연동 규격 (프론트엔드 → 백엔드)

본 문서는 프론트엔드에서 화투 점괘(동양풍) 진행 시 백엔드 API를 호출하는 방식과 데이터 구조를 정리한 문서입니다.

## 1. API 기본 정보
- **Endpoint**: `POST /api/cards/readings`
- **Method**: `POST`
- **Authentication**: `Authorization: Bearer <JWT_TOKEN>`

## 2. 요청 데이터 구조 (Request Body)

```json
{
  "category": "HWATU",
  "topic": "LOVE", 
  "cards": [
    { "cardCode": 12, "position": 1, "isReversed": false },
    { "cardCode": 5, "position": 2, "isReversed": false },
    { "cardCode": 43, "position": 3, "isReversed": false },
    { "cardCode": 21, "position": 4, "isReversed": false }
  ]
}
```

### 필드 설명
- **`category`**: 카드 종류 (`"HWATU"` 또는 `"TARO"`)
- **`topic`**: 상담 주제 (String)
    - 가능한 값: `LOVE`(연애), `MONEY`(재물), `HEALTH`(건강), `STUDY`(학업), `CAREER`(직장)
- **`cards`**: 선택된 카드 리스트 (Array)
    - **`cardCode`**: 카드 고유 번호 (`0`~`47`)
    - **`position`**: 답변 순서 및 위치 (`1`~`4`)
    - **`isReversed`**: 화투의 경우 항상 `false` (타로 전용 필드)

## 3. 프론트엔드 호출 코드 예시

### (1) API 서비스 레이어 (`src/api/card.ts`)
Axios를 사용하여 백엔드 엔드포인트에 요청을 보냅니다.

```typescript
import api from './axios';

export const createCardReading = async (data: CardCreateReadingRequest) => {
    // POST /cards/readings 호출
    const response = await api.post<any>('/cards/readings', data);
    return response.data.data ? response.data.data : response.data;
};
```

### (2) 컴포넌트 내 호출 로직 (`CardReadingPage.tsx`)
화투 점괘는 **프리페치(Prefetch)** 방식을 사용하여 사용자가 패를 고르기 시작할 때 이미 API를 호출한 뒤 결과를 기다립니다.

```typescript
const handleStartReading = async (topicId: string) => {
    // 1. 서버에 보낼 4개의 랜덤 카드 번호를 미리 생성
    const generatedIds = generateRandomUniqueIds(4, 48);

    // 2. 요청 페이로드 구성
    const requestPayload = {
        category: 'HWATU',
        topic: topicId,
        cards: generatedIds.map((cardId, i) => ({
            cardCode: cardId,
            position: i + 1,
            isReversed: false
        }))
    };

    // 3. 백엔드 API 호출 (비동기)
    createCardReading(requestPayload).then(response => {
        // 백엔드로부터 받은 AI 해석 결과를 상태에 저장하여 나중에 표시
        setBackendResult(response);
    });
};
```

## 4. 백엔드 응답 기대 구조 (Response)
백엔드는 `aiReading` 필드 내에 상세 데이터(`data`)를 포함하여 반환해야 합니다.

- **`cards`**: 각 위치별 카드 이름, 키워드, 상세 해석
- **`summary`**: 전체적인 운세 테마와 조언
- **`lucky`**: 행운의 색상, 숫자, 방향, 시간대 정보

---
**작성일**: 2026-02-07
**작성자**: 프론트엔드 개발팀 / Antigravity AI
