<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=180&section=header&text=YEJI%20Backend&fontSize=42&fontColor=ffffff&animation=fadeIn&fontAlignY=36&desc=Spring%20Boot%203.4%20%7C%20Java%2021%20%7C%20REST%20API&descSize=16&descAlignY=56" width="100%"/>

<br/>


<br/>

**운세/사주 서비스 백엔드 API 서버**

<br/>

[![Java](https://img.shields.io/badge/Java_21-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)](#)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot_3.4-6DB33F?style=for-the-badge&logo=springboot&logoColor=white)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](#)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](#)
[![Gradle](https://img.shields.io/badge/Gradle-02303A?style=for-the-badge&logo=gradle&logoColor=white)](#)

</div>

<br/>

<details>
<summary><strong>목차</strong></summary>

- [개요](#개요)
- [핵심 기능](#핵심-기능)
- [기술 스택](#기술-스택)
- [도메인 구조](#도메인-구조)
- [프로젝트 구조](#프로젝트-구조)
- [시작하기](#시작하기)
- [API 개요](#api-개요)
- [배포](#배포)
- [관련 저장소](#관련-저장소)

</details>

---

## 개요

YEJI Backend는 운세/사주 서비스의 핵심 비즈니스 로직을 처리하는 REST API 서버입니다. 사용자 인증, 사주/운세 데이터 관리, 카드 시스템, 소셜 기능을 담당하며, AI Server와 연동하여 LLM 기반 운세 생성을 오케스트레이션합니다.

> **SSAFY 14기 A605팀** | 2026.01.05 - 2026.02.09

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 핵심 기능

### 사용자 시스템
- **소셜 로그인**: Kakao, Google, Naver OAuth2 인증
- **JWT 기반 인증/인가**: Access/Refresh 토큰 관리
- **프로필 관리**: 생년월일, 성별, 사주 정보 등록

### 운세/사주
- **사주 분석 요청**: AI Server로 사주 분석 요청 및 결과 저장
- **운세 조회**: 일별/주간/월간 운세 기록 관리
- **궁합 분석**: 두 사용자 간 궁합 데이터 관리
- **SSE 스트리밍**: AI Server 응답을 실시간 클라이언트 전달

### 카드 시스템
- **타로/화투 관리**: 카드 덱, 선택, 해석 결과 저장
- **오방 카드**: 오행 기반 특수 카드 시스템
- **컬렉션**: 카드 수집 및 도감 시스템

### 소셜 기능
- **친구 시스템**: 친구 요청, 수락, 차단
- **운세 공유**: 축복/저주 시스템 (운세 결과 교환)
- **이벤트**: 운세 기반 이벤트 및 보상

### 상점
- **캐릭터 상점**: 운세 캐릭터 구매/장착
- **지갑 시스템**: 인앱 재화 관리

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 기술 스택

| 구분 | 기술 |
|:-----|:-----|
| **Language** | Java 21 |
| **Framework** | Spring Boot 3.4 |
| **Security** | Spring Security, JWT |
| **ORM** | Spring Data JPA |
| **Database** | PostgreSQL 16 (AWS RDS) |
| **Cache** | Redis |
| **Build** | Gradle |
| **CI/CD** | Jenkins (Docker 자동 배포) |

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 도메인 구조

```
domain/
├── user/              # 사용자 (회원가입, 프로필, 인증)
├── saju/              # 사주 (사주 분석 요청/결과)
├── unse/              # 운세 (일별/주간/월간 운세)
├── card/              # 카드 (타로, 화투, 오방)
├── collection/        # 컬렉션 (카드 도감)
├── compatibility/     # 궁합 (두 사용자 궁합 분석)
├── friend/            # 친구 (요청, 수락, 차단)
├── event/             # 이벤트 (축복/저주)
├── luck/              # 행운 (행운 아이템)
├── session/           # 세션 (사용자 세션 관리)
├── shop/              # 상점 (캐릭터 구매)
└── wallet/            # 지갑 (재화 관리)

global/
├── auth/              # 인증 (OAuth2, JWT)
├── config/            # 설정 (Security, WebClient, CORS)
├── jwt/               # JWT 토큰 처리
├── exception/         # 전역 예외 처리
├── external/          # 외부 API 연동 (AI Server)
└── dto/               # 공통 DTO
```

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 프로젝트 구조

```
src/main/java/com/yeji/
├── domain/                    # 도메인 계층
│   ├── user/
│   │   ├── controller/        #   REST Controller
│   │   ├── service/           #   비즈니스 로직
│   │   ├── repository/        #   데이터 접근
│   │   ├── entity/            #   JPA Entity
│   │   └── dto/               #   Request/Response DTO
│   ├── saju/                  #   (동일 구조)
│   ├── card/
│   ├── unse/
│   ├── friend/
│   ├── compatibility/
│   ├── collection/
│   ├── event/
│   ├── luck/
│   ├── session/
│   ├── shop/
│   └── wallet/
│
├── global/                    # 전역 계층
│   ├── auth/                  #   OAuth2 핸들러
│   ├── config/                #   설정 (Security, WebClient)
│   ├── jwt/                   #   JWT Provider/Filter
│   ├── exception/             #   전역 예외 핸들러
│   ├── external/              #   AI Server 연동
│   └── dto/                   #   공통 응답 DTO
│
└── YejiApplication.java       # 메인 진입점
```

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 시작하기

### 요구사항

- Java 21
- Gradle 8.x
- PostgreSQL 16
- Redis

### 빌드 및 실행

```bash
# 빌드
./gradlew build

# 실행
./gradlew bootRun

# 테스트
./gradlew test
```

### 환경변수

```properties
# Database
spring.datasource.url=jdbc:postgresql://localhost:5432/yeji
spring.datasource.username=yeji
spring.datasource.password=****

# Redis
spring.data.redis.host=localhost
spring.data.redis.port=6379

# AI Server
ai.server.url=http://localhost:8000

# JWT
jwt.secret=****
jwt.access-token-expiration=3600000
jwt.refresh-token-expiration=604800000

# OAuth2 (Kakao, Google, Naver)
spring.security.oauth2.client.registration.kakao.client-id=****
```

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## API 개요

| 도메인 | 주요 엔드포인트 | 설명 |
|:-------|:---------------|:-----|
| **User** | `/api/users/**` | 회원가입, 프로필, 사주 정보 |
| **Saju** | `/api/saju/**` | 사주 분석 요청/결과 조회 |
| **Unse** | `/api/unse/**` | 운세 조회/생성 (SSE) |
| **Card** | `/api/cards/**` | 타로/화투/오방 카드 |
| **Friend** | `/api/friends/**` | 친구 요청/수락/차단 |
| **Compatibility** | `/api/compatibility/**` | 궁합 분석 |
| **Collection** | `/api/collections/**` | 카드 도감 |
| **Shop** | `/api/shop/**` | 캐릭터 구매/장착 |
| **Auth** | `/api/auth/**` | 로그인/로그아웃/토큰 갱신 |

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 배포

| 환경 | 브랜치 | 포트 | URL |
|:-----|:------:|:----:|:----|
| Production | `main` | 8081 | `/api/` |

Jenkins Webhook 트리거로 Docker 컨테이너 자동 배포.

<p align="right">(<a href="#목차">맨 위로</a>)</p>

---

## 관련 저장소

| 저장소 | 설명 |
|:-------|:-----|
| [yeji-ai](https://github.com/yeji-service/yeji-ai) | AI 운세 생성 서버 (Python, FastAPI, vLLM) |
| [yeji-frontend](https://github.com/yeji-service/yeji-frontend) | 프론트엔드 웹 앱 (React 19, Vite) |
| [yeji-code-review](https://github.com/yeji-service/yeji-code-review) | 코드 리뷰 아카이브 (249건) |

---

<div align="center">

**SSAFY 14기 A605팀** | 2026.01 - 02

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=80&section=footer" width="100%"/>

</div>
