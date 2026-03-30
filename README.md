<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=YEJI&fontSize=60&fontColor=ffffff&animation=fadeIn&fontAlignY=34&desc=AI-Powered%20Fortune%20and%20Saju%20Platform&descSize=18&descAlignY=56" width="100%"/>

<br/>

<img src="./yeji-logo.png" width="120" alt="yeji"/>

<br/>

### 동양의 사주, 서양의 타로 -- AI가 풀어내는 당신의 운세

<br/>

[![Java](https://img.shields.io/badge/Java_21-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)](#)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot_3.4-6DB33F?style=for-the-badge&logo=springboot&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](#)
[![vLLM](https://img.shields.io/badge/vLLM-FF6F00?style=for-the-badge&logo=pytorch&logoColor=white)](#)

[![React](https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](#)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](#)
[![Framer Motion](https://img.shields.io/badge/Framer_Motion-0055FF?style=for-the-badge&logo=framer&logoColor=white)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](#)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](#)

</div>

---

## 프로젝트 소개

**예지(YEJI)** 는 단순한 텍스트 기반 운세를 넘어, **프리미엄 인터랙티브 경험**과 **AI 정밀 분석**, **소셜 게이미피케이션**을 결합한 차세대 운세 플랫폼입니다.

사용자는 물리 엔진 기반의 카드 셔플로 직접 타로/화투 카드를 선택하고, 커스텀 파인튜닝된 LLM이 동양 도사와 서양 마법사 캐릭터의 유머러스한 티키타카로 운세를 해석해줍니다.

> **SSAFY 14기 자율 프로젝트 A605팀** | 2026.01.05 - 2026.02.09 (6주)

---

## 핵심 기능

<table>
<tr>
<td width="50%">

### AI 운세 생성
- 커스텀 파인튜닝 LLM (`Qwen3 4B AWQ`)
- vLLM GPU 추론 서버 (실시간 생성)
- 동/서양 캐릭터 페르소나 스토리텔링
- SSE 기반 실시간 스트리밍 응답

</td>
<td width="50%">

### 인터랙티브 카드
- Framer Motion 물리 엔진 카드 셔플
- 타로 78장 + 화투 60장 + 오방 카드
- 카드 수집 도감 시스템
- 카테고리별 맞춤 해석

</td>
</tr>
<tr>
<td width="50%">

### 통합 운세 분석
- 사주팔자 기반 동양 운세 (연애/재물/건강/학업/직업)
- 별자리 + 타로 기반 서양 운세
- 두 사람의 동서양 통합 궁합 지수
- Radar Chart 궁합 시각화

</td>
<td width="50%">

### 소셜 게이미피케이션
- 축복/저주: 운세 결과를 친구와 교환
- 캐릭터 상점: 동양 6종 + 서양 5종 수집
- 친구 시스템: 운세 공유 기반 소셜 네트워크
- 운세 히스토리 아카이빙

</td>
</tr>
</table>

---

## 시스템 아키텍처

```
                         사용자
                           |
                    ┌──────▼──────┐
                    │    Nginx    │
                    │   Reverse   │
                    │    Proxy    │
                    └──┬──────┬───┘
                       │      │
              ┌────────▼┐  ┌──▼────────┐
              │ Backend  │  │ AI Server │
              │ Spring   │  │  FastAPI  │
              │ Boot 3.4 │  │  + vLLM   │
              └──┬───┬───┘  └─────┬─────┘
                 │   │            │
            ┌────▼┐ ┌▼────┐ ┌────▼─────┐
            │ RDS │ │Redis│ │  Qwen3   │
            │ PG  │ │     │ │  4B AWQ  │
            └─────┘ └─────┘ └──────────┘
                               (GPU)
```

| 계층 | 기술 | 설명 |
|:-----|:-----|:-----|
| **Frontend** | React 19, TypeScript, Framer Motion, Tailwind CSS | 물리 엔진 카드 인터랙션, 프리미엄 UI |
| **Backend** | Java 21, Spring Boot 3.4, Spring Security, JPA | 인증/인가, 도메인 로직, SSE 중계 |
| **AI Server** | Python 3.11, FastAPI, Pydantic v2, structlog | 운세 생성, 프롬프트 엔지니어링, 후처리 |
| **LLM 추론** | vLLM, `yeji-4b-instruct-v9-AWQ` | GPU 기반 실시간 텍스트 생성 |
| **Database** | PostgreSQL 16 (RDS), Redis | 영속 데이터 + 세션/캐시 |
| **Infra** | AWS EC2, Docker, Jenkins, Nginx | CI/CD 자동 배포 |

---

## 저장소

<div align="center">

| 저장소 | 설명 | 주요 기술 |
|:-------|:-----|:---------|
| [**yeji-ai**](https://github.com/yeji-service/yeji-ai) | AI 운세 생성 서버 | Python 3.11, FastAPI, vLLM, Qwen3 4B AWQ |
| [**yeji-backend**](https://github.com/yeji-service/yeji-backend) | 백엔드 API 서버 | Java 21, Spring Boot 3.4, PostgreSQL, Redis |
| [**yeji-frontend**](https://github.com/yeji-service/yeji-frontend) | 프론트엔드 웹 앱 | React 19, TypeScript, Framer Motion, Vite |
| [**yeji-code-review**](https://github.com/yeji-service/yeji-code-review) | 코드 리뷰 아카이브 | 7라운드 / 249건 (CRITICAL 26, HIGH 72) |

</div>

---

## 팀원

<div align="center">

<table>
<tr>
<td align="center" width="160">
<a href="https://github.com/HWISU96">
<img src="https://github.com/HWISU96.png" width="100" style="border-radius:50%"/><br/>
<sub><b>김휘수</b></sub>
</a><br/>
<sub>Frontend</sub>
</td>
<td align="center" width="160">
<a href="https://github.com/seolsa1014">
<img src="https://github.com/seolsa1014.png" width="100" style="border-radius:50%"/><br/>
<sub><b>설현원</b></sub>
</a><br/>
<sub>Frontend</sub>
</td>
<td align="center" width="160">
<a href="https://github.com/minseond">
<img src="https://github.com/minseond.png" width="100" style="border-radius:50%"/><br/>
<sub><b>김민선</b></sub>
</a><br/>
<sub>Backend</sub>
</td>
<td align="center" width="160">
<a href="https://github.com/pbjuni1007-cmyk">
<img src="https://github.com/pbjuni1007-cmyk.png" width="100" style="border-radius:50%"/><br/>
<sub><b>박병준</b></sub>
</a><br/>
<sub>Backend</sub>
</td>
<td align="center" width="160">
<a href="https://github.com/tellang">
<img src="https://github.com/tellang.png" width="100" style="border-radius:50%"/><br/>
<sub><b>박태언</b></sub>
</a><br/>
<sub>AI / Infra</sub>
</td>
</tr>
</table>

</div>

---

## AI 모델

이 프로젝트는 **직접 파인튜닝한 커스텀 LLM**을 사용합니다.

| 모델 | 기반 | 양자화 | 용도 |
|:-----|:-----|:------:|:-----|
| [`tellang/yeji-4b-instruct-v9-AWQ`](https://huggingface.co/tellang/yeji-4b-instruct-v9-AWQ) | Qwen3 4B | AWQ 4bit | 프로덕션 (GPU 추론) |

- **학습 데이터**: 사주/타로 도메인 특화 + 캐릭터 페르소나 + 구조화 출력 (JSON)
- **학습 기법**: QLoRA (Rank 16) + NEFTune + Cosine LR
- **추론 최적화**: vLLM + guided_json + AWQ 양자화 (메모리 75% 절감)

---

<div align="center">

<br/>

**SSAFY 14기 A605팀** | Samsung Software Academy For Youth

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

</div>
