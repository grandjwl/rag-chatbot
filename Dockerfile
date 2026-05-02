FROM python:3.10-slim

# 로그 바로 출력
ENV PYTHONUNBUFFERED=1

WORKDIR /llmServerWorkspace

# 필수 패키지 설치
RUN apt-get update && apt-get install -y curl procps

# cloudflared 설치
RUN curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb \
    && dpkg -i cloudflared.deb \
    && rm cloudflared.deb


# 의존성 먼저 복사 (캐시 효율)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# backend 전체 복사
COPY . .

EXPOSE 9000

# 이건 stage나 dev나 어떤 환경에서든 들어갈 명령어니까 프로세스는 재시작 안할래. compose에서 override할래.
CMD ["uvicorn", "api.test.test_main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]  