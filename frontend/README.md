<br>

<div align="center">
<img width="120" height="120" alt="Image" src="https://github.com/user-attachments/assets/bfcfef20-74bc-4649-8c3a-264fc697531a" />


<br>
 
# 예지(YEJI) - Frontend
</div>

<div align="center">
  <h3>Core Tech Stack</h3>
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white">
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white">
  <img src="https://img.shields.io/badge/React_Router-CA4245?style=for-the-badge&logo=react-router&logoColor=white">
  <br>
  <h3>UI & Interaction</h3>
  <img src="https://img.shields.io/badge/Framer_Motion-0055FF?style=for-the-badge&logo=framer&logoColor=white">
  <img src="https://img.shields.io/badge/Three.js-000000?style=for-the-badge&logo=three.js&logoColor=white">
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white">
  <img src="https://img.shields.io/badge/Lucide_React-F7B93E?style=for-the-badge&logo=lucide&logoColor=black">
  <br>
  <h3>Data & API</h3>
  <img src="https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white">
  <img src="https://img.shields.io/badge/JWT_Decode-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white">
  <img src="https://img.shields.io/badge/Recharts-22B5AD?style=for-the-badge&logo=recharts&logoColor=white">
  <img src="https://img.shields.io/badge/html--to--image-FF3E00?style=for-the-badge&logo=html5&logoColor=white">
</div>

---

## 프로젝트 소개

'예지'는 텍스트 기반의 운세를 넘어, **프리미엄 인터랙티브 경험**과 **AI 정밀 분석**을 결합한 게이미피케이션 운세 플랫폼입니다.

사용자는 동서양의 운세 데이터를 통합하여 개인별 맞춤형 리포트와 친구와의 궁합 분석을 세련된 UI로 확인할 수 있습니다. <br> 또한 물리 엔진 기반의 카드 셔플 알고리즘을 통해 직접 카드를 선택하며 몰입감 있는 경험을 제공받습니다.

### 프로젝트 기간
- **2026.01.06 ~ 2026.02.09 (6주)**
- **팀:** SSAFY 14기 자율 프로젝트 A605팀

<br>

## Key Frontend Features

### 1. 물리 기반 인터랙티브 카드 시스템
- **데크 시뮬레이션**: `Framer Motion`의 물리 엔진을 활용한 사실적인 카드 셔플 및 드래그 인터랙션 (`DraggableFanDeck`).
- **신비로운 연출**: 카드 선택 시 `MysticScatteredDeck`을 통한 자동 확산 연출 및 조명 효과.
- **3D 비주얼**: `React Three Fiber(R3F)`와 `@react-three/drei`를 활용하여 웹 환경에서도 부드러운 3D 그래픽을 구현했습니다.

### 2. 프리미엄 비주얼 스토리텔링
- **캐릭터 페르소나**: AI 분석 결과에 따라 동/서양 가이드 캐릭터가 실시간으로 반응하며 감정적인 연결을 제공.
- **다이나믹 결과지**: Canvas 및 `html-to-image` 기반의 맞춤형 운세 보고서 생성 및 이미지 저장 기능.

### 3. 고도화된 UI/UX 요소
- **타이핑 효과 엔진**: AI 응답의 실시간 스트리밍 감각을 최적화한 데이터 기반 타이핑 효과.
- **반응형 테마 시스템**: 동양(화투/사주)과 서양(타로) 각각의 감성에 맞춘 독립적인 애니메이션 및 컬러 팔레트 적용.


## 기술 스택 (Tech Stack)

### Frontend 🎨
| 구분 | 기술 |
|------|------|
| **Framework** | ⚛️ React 18, 🟦 TypeScript |
| **Animation** | 🎞️ Framer Motion |
| **Styling** | 💨 Tailwind CSS |
| **API Client** | 🌐 Axios |
| **Build Tool** | ⚡ Vite |


### Backend (be/main) 🧩
| 구분 | 기술 |
|------|------|
| **Framework** | ☕ Spring Boot (Java 17) |
| **Security** | 🔐 Spring Security |
| **ORM** | 🗃️ JPA, MyBatis |
| **Database** | 🐘 PostgreSQL 16 |
| **Cache** | ⚡ Redis |
| **Build Tool** | 🐘 Gradle |


### AI Server (ai/main)
| 구분 | 기술 |
|------|------|
| **Framework** | ⚡ FastAPI, 🐍 Python 3.11 |
| **LLM Provider** | 🧠 vLLM (GPU 추론 서버) |
| **AI Model** | 🤖 `tellang/yeji-8b-rslora-v7-AWQ` (Qwen3 8B 기반 파인튜닝) |
| **검증** | ✅ Pydantic v2 |
| **로깅** | 🪵 structlog |
| **Cache** | ⚡ Redis |
| **패키지 관리** | 📦 uv |

### Infrastructure
| 구분 | 기술 |
|------|------|
| **Cloud** | ☁️ AWS EC2 (SSAFY), 🎮 AWS EC2 GPU (g6.xlarge) |
| **Database** | 🐘 AWS RDS (PostgreSQL 16) |
| **CI/CD** | 🔁 Jenkins (Docker 기반 자동 배포) |
| **Proxy** | 🌐 Nginx |
| **Container** | 🐳 Docker, Docker Compose |
| **협업 도구** | 🧑‍💻 GitLab, 📋 Jira, 📝 Notion, 🎨 Figma |


---

---

## 트러블 슈팅

### 카드 대량 렌더링 시 최적화 문제
- **문제점**: 22장 이상의 타로 카드가 동시에 물리 엔진의 영향을 받으며 렌더링될 때 프레임 드랍 발생.
- **해결책**: `useMemo`와 React `memo`를 적극 활용하여 불필요한 리렌더링을 차단하고, 카드 상태 업데이트를 일괄 처리(Batching)하여 60FPS 이상의 매끄러운 성능을 확보했습니다.

### 타이핑 효과 내 '텍스트 겹침(Ghosting)' 현상
- **문제점**: 이전 렌더링의 타이핑 루프가 종료되지 않은 상태에서 새로운 텍스트가 들어올 때 텍스트가 엉키는 현상.
- **해결책**: `useRef`를 이용한 타이머 인스턴스 관리와 `useEffect`의 `cleanup` 함수를 통해 비동기 타이핑 프로세스를 철저히 제어하는 로직을 구축했습니다.

### 고해상도 보고서 이미지 저장 기능
- **문제점**: 복잡한 CSS 속성(Gradient, Shadow)이 적용된 UI를 이미지로 변환할 때 스타일이 누락되거나 깨지는 이슈.
- **해결책**: `html-to-image`와 `toPng` 라이브러리의 렌더링 옵션을 튜닝하고, 이미지 캡처 전 전용 레이아웃을 임시 생성하는 방식으로 스타일 정합성을 유지했습니다.

---

## 👥 팀원 소개 (Team Members)

<table>
  <tr>
    <td align="center"><a href="https://github.com/HWISU96"><img src="https://github.com/HWISU96.png" width="120px;" alt=""/><br /><sub><b>김휘수</b></sub></a><br />Frontend</td>
    <td align="center"><a href="https://github.com/seolsa1014"><img src="https://github.com/seolsa1014.png" width="120px;" alt=""/><br /><sub><b>설현원</b></sub></a><br />Frontend</td>
    <td align="center"><a href="#"><img src="https://github.com/github.png" width="120px;" alt=""/><br /><sub><b>박태언</b></sub></a><br />AI / Infra</td>
  </tr>
  <tr> 
    <td align="center"><a href="https://github.com/minseond"><img src="https://github.com/minseond.png" width="120px;" alt=""/><br /><sub><b>김민선</b></sub></a><br />Backend</td>
    <td align="center"><a href="#"><img src="https://github.com/github.png" width="120px;" alt=""/><br /><sub><b>박병준</b></sub></a><br />Backend</td>
    <td align="center"><b></b><br /></td>
  </tr>
</table>

---

## UI
### | 메인 화면 (Login) |
<img width="2880" height="1794" alt="YEJI_FRONT (2)" src="https://github.com/user-attachments/assets/d0407996-e5ae-4742-aef2-b9d75b4b7a21" />

### | 도감 화면 (Collections) |
<img width="2880" height="1800" alt="YEJI_FRONT (5)" src="https://github.com/user-attachments/assets/1f5f2740-273e-41f2-8dee-bff0451c6bc2" />

### | 캐릭터 선택 화면 (Collections) |
<img width="2880" height="1682" alt="YEJI_FRONT (4)" src="https://github.com/user-attachments/assets/58f4a740-824c-462f-9435-b2c5834762f3" />

### | 카드 점괘 선택 화면 |
<img width="2858" height="1800" alt="타로" src="https://github.com/user-attachments/assets/14e55887-3f0b-4e6d-8ccb-928b6db92113" />

### | 카드 점괘(화투) 진행 화면 |

<div align="center">
  <video src="https://github.com/user-attachments/assets/8afb0403-022f-4f3e-b7ae-6c1a667ca541" width="600" autoplay loop muted playsinline></video>
</div>

---

## 📄 라이선스

본 프로젝트는 SSAFY 교육 과정의 일환으로 제작되었습니다.

---
