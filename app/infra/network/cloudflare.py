# app\infra\network\cloudflare.py
import subprocess
import time
import os
import platform

class CloudflareTunnel:
    def __init__(self, hostname: str, db_host: str, db_port: int):
        self.hostname = hostname
        self.db_host = db_host
        self.db_port = db_port
        self._proc = None

    def start(self, wait_sec: int = 5):
        # 1. 기존 cloudflared 프로세스 종료 (윈도우용 taskkill 사용)
        try:
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/f", "/im", "cloudflared.exe"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-f", "cloudflared"], stderr=subprocess.DEVNULL)
        except Exception:
            pass

        # 2. 터널 명령어 (경로를 "cloudflared"로만 설정하여 시스템 PATH 활용)
        # 만약 그래도 못 찾으면 r"C:\Users\k\miniconda3\cloudflared.exe" 처럼 절대경로 사용
        cmd = [
            "cloudflared", 
            "access", 
            "tcp", 
            "--hostname", self.hostname,
            "--listener", f"localhost:{self.db_port}"
        ]

        print(f"🔗 Cloudflare 연결 시도: {self.hostname} -> localhost:{self.db_port}")

        # 3. 프로세스 실행
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=(platform.system() == "Windows") # 윈도우에서 명령어를 더 잘 찾게 함
        )

        time.sleep(wait_sec)
        print("✅ Cloudflare 터널링 입구(Access) 활성화됨")

    def stop(self):
        if self._proc:
            self._proc.terminate()
            print("🔒 Cloudflare 터널 종료")