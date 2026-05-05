# 휴먼 AI 교육센터 심층 데이터 분석 과정 6기
## LLM/RAG 기반 기업 업무형 AI 비서 설계 및 구현

<hr>

### 📌 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [주요 기능](#주요-기능)
3. [시스템 아키텍처](#시스템-아키텍처)
4. [기술 스택](#기술-스택)
5. [LLM 서버 상세](#llm-서버-상세)
6. [모델 선정 과정](#모델-선정-과정)
7. [향후 개선 방안](#향후-개선-방안)

---

### 프로젝트 개요

#### 기존 챗봇의 한계

기존 AI 챗봇은 내부 DB와 직접 연결되지 않아 실무 데이터 조회가 불가능했고,
대화 맥락 유지나 완전 자동화에도 한계가 있었습니다.

| 문제 | 내용 |
|------|------|
| 완전 자동화 불가 | 사용자에게 추가 입력을 반복 요구 |
| 맥락 오류 | 세션 기억 오류로 부정확한 답변 |
| DB 연결 부재 | 실시간 업무 데이터 조회 불가 |
| 의사결정 한계 | 데이터 기반 인사이트 제공 어려움 |

#### 해결 방향

**LLM + RAG + Orchestration** 3가지를 결합하여 한계를 극복했습니다.

<!-- 이미지: LLM·RAG·Orchestration 삼각형 다이어그램 (PPT 6페이지) -->

| 구분 | LLM 단독 | LLM + RAG | LLM + RAG + Orchestration |
|------|----------|-----------|--------------------------|
| 데이터 범위 | 학습 데이터 | 외부/내부 문서 | 외부/내부 문서 + 동적 전략 |
| 신뢰성 | 환각 가능 | 근거 기반 응답 | 검색 검증 + 재시도 + 제어 로직 |
| 오류 대응 | 어려움 | 검색 의존 | Fallback / 재시도 / 모델 전환 |
| 기업 활용 | 제한적 | 실무 적용 가능 | 실무 최적화 및 전략적 운영 |

---

### 주요 기능

#### 💬 AI 업무 챗봇
자연어로 재고·매출·매입 데이터를 즉시 조회합니다.
대화 맥락을 기억하여 후속 질문도 자연스럽게 처리합니다.

<!-- 이미지: 챗봇 메인 화면 스크린샷 (PPT 22페이지) -->

#### 📊 업무 대시보드
재고 현황, 매출 인사이트 등 업무 특화 대시보드를 제공합니다.

<!-- 이미지: 대시보드 스크린샷 (PPT 24페이지) -->

#### 🤖 미니 챗봇
모든 화면에서 플로팅 형태로 즉시 질문할 수 있습니다.

<!-- 이미지: 미니챗봇 스크린샷 (PPT 23페이지) -->

#### 📦 재고 운영 관리
실시간 재고 현황 확인 및 제품 카탈로그 관리 기능을 제공합니다.

<!-- 이미지: 운영 관리 화면 스크린샷 (PPT 26페이지) -->

---

### 시스템 아키텍처

<!-- 이미지: 전체 아키텍처 다이어그램 (PPT 10페이지) -->

전체 서비스는 **React 프론트엔드**, **FastAPI 백엔드**, **LLM 서버**,
**PostgreSQL + ChromaDB** 로 구성됩니다.
각 컴포넌트는 Docker로 컨테이너화되어 Cloudflare 터널을 통해 연결됩니다.

#### 데이터 구조

**관계형 DB (PostgreSQL)**

<!-- 이미지: ERD 다이어그램 (PPT 12페이지) -->

| 테이블 | 설명 |
|--------|------|
| `products` | 전자부품 마스터 (300종) |
| `manufacturers` | 제조사 정보 (69개사) |
| `vendors` | 고객사 정보 (29개사) |
| `purchase_orders` | 매입 이력 (13,615건) |
| `sales_orders` | 매출 이력 (39,572건) |
| `current_products` | 실시간 재고 현황 |
| `initial_inventory` | 초기 재고 스냅샷 |

**벡터 DB (ChromaDB)**

| 컬렉션 | 용도 |
|--------|------|
| `fewshot` | 유사 질문-SQL 예시 |
| `bizterm_store` | 비즈니스 용어 정의 |
| `table_schema_store` | 테이블 스키마 정보 |
| `refine_store` | 파트넘버 오타 교정용 |

---

### 기술 스택

<!-- 이미지: 기술스택 이미지 (PPT 9페이지) -->

**LLM / AI**

![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=flat-square&logo=google&logoColor=white)
![Cohere](https://img.shields.io/badge/Cohere-D4A017?style=flat-square&logoColor=white)

**Backend / LLM Server**

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-121212?style=flat-square&logoColor=white)

**Database**

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6B35?style=flat-square&logoColor=white)

**Frontend**

![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat-square&logo=node.js&logoColor=white)

**Infra**

![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cloudflare-F38020?style=flat-square&logo=cloudflare&logoColor=white)

**개발 환경**

![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)
![VSCode](https://img.shields.io/badge/VSCode-007ACC?style=flat-square&logo=visualstudiocode&logoColor=white)
