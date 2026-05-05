# 휴먼 AI 교육센터 심층 데이터 분석 과정 6기
## LLM/RAG 기반 기업 업무형 AI 비서 설계 및 구현

<hr>

### 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [주요 기능](#주요-기능)
3. [시스템 아키텍처](#시스템-아키텍처)
4. [기술 스택](#기술-스택)
5. [LLM 서버 상세](#llm-서버-상세)
6. [모델 선정 과정](#모델-선정-과정)
7. [향후 개선 방안](#향후-개선-방안)

<hr>

### 프로젝트 개요

<!-- 이미지: BizAI 서비스 전체 흐름 다이어그램 (PPT 11페이지) -->

- 전자부품 유통사의 업무 담당자가 **자연어 질문만으로** 재고·매출·매입 데이터를 즉시 조회하고 인사이트를 얻을 수 있는 기업 AI 비서 서비스입니다.
- 기존 챗봇은 내부 DB와 직접 연결되지 않아 실무 데이터 조회가 불가능했고, 대화 맥락 유지나 완전 자동화에도 한계가 있었습니다.
- **LLM + RAG + Orchestration** 세 가지를 결합하여 이러한 한계를 극복했습니다.

<!-- 이미지: LLM·RAG·Orchestration 삼각형 다이어그램 (PPT 6페이지) -->
<img width="374" height="250" alt="image" src="https://github.com/user-attachments/assets/84859b52-a7eb-4eb3-bbac-859202858881" />



- LLM의 부정확성은 RAG가 보완하고, RAG의 검색 의존성은 Orchestration이 통제하며, LLM의 비용·성능 문제는 Orchestration이 모델 전략으로 조정합니다.

> 프로젝트 기간 : 2025년 2월 9일 ~ 3월 6일 (4주)
<br><br>

### 주요 기능

#### 💬 AI 업무 챗봇
<!-- 이미지: 챗봇 메인 화면 스크린샷 (PPT 22페이지) -->
<img width="490" height="321" alt="image" src="https://github.com/user-attachments/assets/27ab6492-98a2-47f6-8159-a480b07db044" />
<img width="483" height="310" alt="image" src="https://github.com/user-attachments/assets/357cb27a-64ee-4980-8405-c6d9758e548e" />


- 자연어로 재고·매출·매입 데이터를 즉시 조회합니다.
- 이전 대화 맥락을 기억하여 후속 질문도 자연스럽게 처리합니다.
- 일상 대화(CHIT_CHAT)와 업무 데이터 질의(INVENTORY)를 자동으로 분류하여 처리합니다.
<br><br>

#### 🤖 미니 챗봇
<!-- 이미지: 미니챗봇 스크린샷 (PPT 23페이지) -->
<img width="395" height="325" alt="image" src="https://github.com/user-attachments/assets/bbcdfd0d-25bb-4cfe-b7d1-bb99bdb0c558" />


- 모든 화면에서 플로팅 형태로 즉시 질문할 수 있습니다.
- 확대·축소 가능한 반응형 UI로 작업 중 빠른 질문이 가능합니다.
<br><br>

#### 📊 업무 대시보드
<!-- 이미지: 대시보드 스크린샷 (PPT 24페이지) -->
<img width="539" height="275" alt="image" src="https://github.com/user-attachments/assets/876ceb6b-82bc-45dc-a59d-8b8dbc8e26ec" />
<img width="539" height="273" alt="image" src="https://github.com/user-attachments/assets/1c7c7672-6d2f-453d-98e8-2c01315fbc85" />


- 재고 현황, 매출 인사이트 등 업무 특화 대시보드를 제공합니다.
- 연도별·품목별 경영 실적 추이와 긴급 구매 필요 품목을 한눈에 확인할 수 있습니다.
<br><br>

#### 📦 재고 운영 관리
<!-- 이미지: 운영 관리 화면 스크린샷 (PPT 26페이지) -->
<img width="606" height="305" alt="image" src="https://github.com/user-attachments/assets/c619084c-cb65-49b6-ae39-1ba7f94a1d99" />
<img width="604" height="307" alt="image" src="https://github.com/user-attachments/assets/b8cc0590-2781-4899-a96e-219d57df4030" />


- 실시간 재고 현황 확인 및 제품 카탈로그 관리 기능을 제공합니다.
- 재고 50개 미만 품목을 자동으로 감지하여 구매 필요 수량을 표시합니다.
<br><br>

### 시스템 아키텍처

<!-- 이미지: 전체 아키텍처 다이어그램 (PPT 10페이지) -->

- 전체 서비스는 React 프론트엔드, FastAPI 백엔드, LLM 서버, PostgreSQL + ChromaDB로 구성됩니다.
- 각 컴포넌트는 Docker로 컨테이너화되어 Cloudflare 터널을 통해 연결됩니다.
<br><br>

#### 데이터 구조

<!-- 이미지: ERD + 벡터DB 컬렉션 구조 (PPT 12페이지) -->

- **관계형 DB (PostgreSQL)** — 전자부품 마스터, 제조사/고객사 정보, 매입/매출 이력, 실시간 재고 현황 등 7개 테이블로 구성됩니다.
- **벡터 DB (ChromaDB)** — SQL 생성 보조용 fewshot 예시, 비즈니스 용어 정의, 테이블 스키마 정보, 파트넘버 교정 데이터를 컬렉션으로 관리합니다.
<br><br>

### 기술 스택

<!-- 이미지: 기술스택 이미지 (PPT 9페이지) -->

- **LLM / AI** : Gemini 2.5 Flash, Cohere Reranker
- **LLM Server** : Python, FastAPI, LangGraph
- **Database** : PostgreSQL, ChromaDB
- **Frontend** : React, TypeScript, Node.js
- **Infra** : Docker, Cloudflare
- **개발 환경** : VSCode, GitHub
<br><br>
