# 휴먼 AI 교육센터 심층 데이터 분석 과정 6기
## LLM/RAG 기반 기업 업무형 AI 비서 설계 및 구현

<hr>

### 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [프로젝트 구조](#프로젝트-구조)
3. [프로젝트 환경](#프로젝트-환경)
4. [데이터와 모델](#데이터와-모델)
5. [LLM 서버 구현](#llm-서버-구현)
6. [추후 연구 방향](#추후-연구-방향)
7. [참고 문헌](#참고-문헌)

<hr>

### 프로젝트 개요

- 최근 기업 환경에서 AI 챗봇 도입이 늘어나고 있으나, 기존 챗봇은 내부 DB와 직접 연결되지 않아 실무 데이터 조회가 불가능한 한계가 있었습니다. 또한 대화 맥락 유지가 어렵고 완전 자동화에도 제약이 있어 의사결정 지원 도구로서의 기능이 제한적이었습니다.
   > 예시로, 매출 데이터를 묻는 질문에도 실제 DB 조회 없이 추정 답변만 제공하는 경우가 많았습니다.
- 본 프로젝트는 이러한 한계를 극복하기 위해 **LLM + RAG + Orchestration** 세 가지 기술을 결합하여, 자연어 질문만으로 내부 DB의 재고·매출·매입 데이터를 즉시 조회하고 인사이트를 얻을 수 있는 전자부품 유통사용 AI 비서 서비스를 구현했습니다.
- LLM의 부정확성은 RAG가 보완하고, RAG의 검색 의존성은 Orchestration이 통제하며, LLM의 비용·성능 문제는 모델 전략 조정으로 해결하는 구조입니다.
<br><br>

### 프로젝트 구조
![image](https://github.com/user-attachments/assets/69a9ab06-aee8-4d44-926e-17ccebb3e6dc)

- 사용자의 자연어 질문은 **LLM**을 거쳐 처리되며, **PostgreSQL**의 정형 데이터(구매·판매 정보)와 **ChromaDB**의 벡터 데이터(RAG 보조 자료)를 조합하여 답변을 생성합니다.
- 생성된 답변은 **AI 비서**를 통해 **프론트엔드**에 전달되며, 사용자는 챗봇·대시보드·업무 관리 화면에서 결과를 확인할 수 있습니다.
- 본 레포지터리는 이 중 **LLM과 데이터베이스 연결을 담당하는 LLM 서버 부분**의 설계 및 구현을 다룹니다.
<br><br>

### 프로젝트 환경
![image](https://github.com/user-attachments/assets/46885031-319b-47cb-90fc-9c84ebc5ca17)


- 전체 시스템은 **Docker Compose**로 컨테이너화되어 있으며, 각 컴포넌트는 독립적으로 실행됩니다.
- 사용자 인터페이스는 **React + TypeScript + Axios** 기반 프론트엔드로 구성됩니다.
- 백엔드와 LLM 서버는 모두 **Python + FastAPI**로 구현되어 RESTful API로 통신합니다.
- LLM 서버는 외부 AI API(**Gemini**, **Cohere**)를 호출하여 자연어 처리 및 검색 재정렬을 수행합니다.
- 데이터 계층은 정형 데이터용 **PostgreSQL**과 벡터 검색용 **ChromaDB**로 구성되며, **Cloudflare 터널**을 통해 외부에서 안전하게 접근합니다.
<br><br>

### 데이터와 모델

#### 데이터
![image](여기에_PPT_12페이지_ERD_이미지)

- **관계형 DB (PostgreSQL)** — 전자부품 유통 도메인을 반영하여 7개 테이블로 설계했습니다. 제품 마스터(`products`), 제조사(`manufacturers`), 고객사(`vendors`), 매입 이력(`purchase_orders`), 매출 이력(`sales_orders`), 실시간 재고(`current_products`), 초기 재고(`initial_inventory`) 테이블이 `part_number`를 중심으로 연결됩니다.
- **벡터 DB (ChromaDB)** — RAG 보조 데이터를 4개 컬렉션으로 분리 관리합니다.
   > `fewshot`(유사 질문-SQL 예시), `bizterm_store`(비즈니스 용어 정의), `table_schema_store`(테이블 스키마 정보), `refine_store`(파트넘버 오타 교정용)
<br><br>

#### 모델 선정
![image](여기에_PPT_15페이지_LLM_Test_이미지)

- LLM은 무료 모델 3종(Groq-Llama-3.3-70B, Groq-Llama-3.1-8B, Gemini-2.5-Flash)을 응답 시간과 정확도 기준으로 비교했습니다.
- Groq 계열이 응답 속도는 빠르나 SQL 생성 정확도와 한국어 이해도에 한계가 있었고, **Gemini-2.5-Flash**가 정확도와 안정성에서 우수하여 최종 선정했습니다.
<br><br>

![image](여기에_PPT_18페이지_임베딩_테스트_이미지)

- 임베딩 모델은 4종(OpenAI ada-002, Gemini embedding-v1, Upstage, OpenAI 3-large)을 논리 변별력과 맥락 파악력 기준으로 비교했습니다.
- 요약 정확도(0.67)와 논리 정확도(0.56)가 모두 준수한 **Gemini embedding-v1**을 선정했습니다.
<br><br>

### LLM 서버 구현

> 본 프로젝트에서 LLM 서버의 전체 설계 및 구현을 담당했습니다.
> FastAPI 기반의 에이전트 파이프라인으로, 자연어 질문을 SQL로 변환하여 DB를 조회하고 자연어 답변을 생성합니다.

#### 에이전트 그래프 흐름
![image](여기에_PPT_13페이지_Agent_Graph_이미지)

- 사용자의 질문은 LangGraph 기반 파이프라인을 통해 아래 순서로 처리됩니다.
   > **Memory → Refine → Router → (SQL Gen → Execute DB → Validate) → Answer → Save**
- **Memory** — 이전 대화 기록을 불러와 맥락을 주입합니다. 후속 질문("그때 그 제품은?")을 완전한 질문으로 재조립합니다.
- **Refine** — 제조사·고객사 이름 오타를 fuzzy 매칭으로 교정하고, 파트넘버 오타를 벡터 검색으로 보정합니다.
- **Router** — 키워드 매칭과 LLM fallback으로 질문 유형을 분류합니다. `INVENTORY` 질의는 SQL 생성으로, `CHIT_CHAT` / `TECH_SALES`는 답변 생성으로 바로 이동합니다.
- **SQL Gen** — fewshot 예시, 비즈니스 용어, 스키마 정보를 RAG로 검색하여 LLM이 SQL을 생성합니다.
- **Execute DB** — 보안·문법·논리·스키마·JOIN 규칙 5단계 검증 후 PostgreSQL에 실행합니다.
- **Validate** — NULL 비율, 음수 매출, 극단값 등 비즈니스 이상치를 검사합니다. 이상 감지 시 SQL Gen으로 재시도합니다.
- **Answer** — 실제 DB 조회 결과를 FACT로 LLM에 주입하여 자연어 답변을 생성합니다.
- **Save** — 질문·답변·SQL·처리시간을 DB에 저장하여 다음 대화의 기억으로 활용합니다.
   > 재시도는 최대 3회까지 수행되며, 초과 시 사용자에게 에러 메시지를 안내합니다.
<br><br>

#### 핵심 설계 포인트
- **하이브리드 RAG 검색** — 벡터 유사도(60%) + BM25 키워드 검색(40%)을 병합한 후 Cohere로 재정렬하는 3단계 검색을 구현했습니다. 개별 전략 실패 시 자동 fallback하여 서비스가 중단되지 않습니다.
- **SQL 안전 검증** — `SELECT *` 금지, 존재하지 않는 테이블·컬럼 차단, Cartesian Product 감지, 허용된 JOIN 조합 강제 등 5단계 정적 검증을 수행하여 LLM이 생성한 SQL의 안전성을 확보했습니다.
- **에러 기반 재시도** — DB 실행 실패 시 에러 메시지를 분석하여 수정 힌트를 생성하고 다음 SQL 생성 프롬프트에 삽입합니다. LLM이 같은 실수를 반복하지 않도록 설계했습니다.
- **Hallucination 방지** — 답변 생성 시 LLM에게 실제 DB 조회 결과만을 FACT로 명시하여 없는 데이터를 지어내는 것을 방지했습니다.
- **유연한 모델 교체 구조** — LLM, 임베딩, 리랭커를 각각 추상 인터페이스로 분리하여 `dependency.py` 한 곳만 수정하면 다른 모델로 교체할 수 있도록 설계했습니다.
<br><br>

#### 실제 동작 화면
![image](여기에_PPT_22페이지_챗봇_메인_이미지)

- LLM 서버를 호출하는 React 기반 챗봇 인터페이스입니다. 자연어로 질문하면 위 파이프라인을 거쳐 답변을 반환합니다.
<br><br>

![image](여기에_PPT_23페이지_미니챗봇_이미지)

- 모든 화면에서 플로팅 형태로 즉시 질문할 수 있는 미니 챗봇 UI도 제공됩니다.
<br><br>

### 추후 연구 방향
- 성공한 SQL을 자동으로 fewshot 데이터로 축적하여 RAG 검색 품질을 지속적으로 개선합니다.
- 맥락 기억 기능을 계층화하여 장기 기억과 단기 기억을 분리하고 성능을 고도화합니다.
- 다양한 임베딩 모델 추가 테스트를 통해 더 나은 검색 품질을 확보합니다.
- 챗봇 답변 시각화 기능(차트, 그래프)을 추가합니다.
- 데이터 축적 이후 LOCAL LLM 도입을 재시도합니다.
<br><br>

### 참고 문헌
- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [Gemini API 문서](https://ai.google.dev/gemini-api/docs)
- [Cohere Rerank 문서](https://docs.cohere.com/docs/rerank)
- [ChromaDB 공식 문서](https://docs.trychroma.com/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
<br><br>
