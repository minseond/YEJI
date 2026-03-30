# 🔮 예지 (Yeji)

![Project Banner](https://placeholder.com/banner-image.png)
<div align="center">

<img src="https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white">
<img src="https://img.shields.io/badge/SpringBoot-6DB33F?style=for-the-badge&logo=springboot&logoColor=white">
<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
<img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white">
<img src="https://img.shields.io/badge/Three.js-000000?style=for-the-badge&logo=three.js&logoColor=white">

</div>

---

##  프로젝트 소개
**'예지'**는 단순한 텍스트 기반의 운세를 넘어, **3D 인터랙티브 경험**과 **소셜 게이미피케이션**을 결합한 차세대 운세 플랫폼입니다.

기존 운세 서비스의 정적인 경험을 탈피하여, 사용자는 3D 공간에서 직접 타로 카드를 섞고, 관상을 분석받으며, 결과(운세)를 친구들과 '거래(저주/축복)'하는 색다른 재미를 느낄 수 있습니다.

###  프로젝트 기간
- **2026.01.05 ~ 2026.02.09 (6주)**

---

##  핵심 기능

### 1.  몰입형 3D 운세
- **Tres.js & Three.js**를 활용한 웹 기반 3D 인터랙션 구현.
- 사용자가 직접 카드를 셔플하고 선택하는 타로 시뮬레이션.
- 별자리와 사주 정보가 3D 오브젝트로 시각화되는 배경 연출.

### 2.  AI 기반 정밀 분석
- **LLM (Large Language Model):** 동/서양 캐릭터(도사, 마법사) 페르소나를 반영한 사주/타로 스토리텔링.
- **Vision AI:** 관상 및 손금 이미지를 분석하여 특징점을 추출하고 운세 데이터와 매칭.

### 3.  소셜 액땜 & 축복
- **불운 처리반 (저주):** 나쁜 운세가 나오면 캐릭터에 담아 친구에게 공유하여 액땜하기.
- **행운 공유 (축복):** 좋은 운세는 캐릭터를 통해 친구에게 선물하고 칭호 획득.

### 4.  도감 및 커스터마이징
- 운세 분석을 도와주는 3D 캐릭터(도사, 산신령 등) 수집 및 장착 시스템.
- 나의 운세 기록을 3D 서재(History) 형태로 시각화하여 아카이빙.

---

##  기술 스택 (Tech Stack)

| 구분 | 기술 (Technology) |
| :--- | :--- |
| **Frontend** | Vue 3, TypeScript, Tres.js (Three.js), Pinia, Tailwind CSS, Vite |
| **Backend** | Java 17, Spring Boot, Spring Security, JPA/MyBatis, Gradle |
| **AI** | Python 3.10, FastAPI, LangChain, OpenCV/YOLO (Vision) |
| **Database** | PostgreSQL (RDB), Redis (Cache) |
| **Infra** | AWS (EC2, S3, RDS), Docker, Jenkins|
| **Collaboration** | GitLab, Jira, Notion, Figma |

---

##  프로젝트 구조 (Project Structure)
본 프로젝트는 **Monorepo** 방식으로 관리되며, 아래와 같은 폴더 구조를 가집니다.

```bash
root/
├── frontend/       # Vue.js 프론트엔드 프로젝트
├── backend/        # Spring Boot 백엔드 프로젝트
├── ai/             # AI 모델 서빙 및 로직 (FastAPI)
└── README.md       # 프로젝트 메인 설명
```

##  협업 규칙 (Convention)

###  브랜치 전략 (Git Flow)
- **master**: 배포 가능한 상태 (Direct Push 금지)
- **fe/develop**: 프론트엔드 통합 브랜치
- **be/develop**: 백엔드 통합 브랜치
- **ai/develop**: AI 통합 브랜치
- **feat 브랜치**: `fe/feat/login`, `be/feat/api` 형식 사용

###  커밋 메시지 (Commit Message)
> `type: Subject` 형식을 따릅니다.

- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅 (로직 변경 없음)
- `refactor`: 코드 리팩토링
- `chore`: 빌드 업무 수정, 패키지 매니저 설정 등