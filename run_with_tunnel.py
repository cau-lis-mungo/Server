# # import subprocess
# # import sys
# # from sshtunnel import SSHTunnelForwarder
# # import os, json

# # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# # SECRET_FILE = os.path.join(BASE_DIR, "secrets.json")

# # with open(SECRET_FILE) as f:
# #     secrets = json.load(f)

# # def get_secret(key):
# #     try:
# #         return secrets[key]
# #     except KeyError:
# #         raise Exception(f"'{key}' 키 에러")

# # # EC2 SSH 정보
# # EC2_HOST = get_secret("EC2_HOST")
# # EC2_USER = get_secret("EC2_USER")
# # EC2_KEY_PATH = get_secret("EC2_KEY_PATH")

# # # RDS 정보
# # RDS_HOST = get_secret("RDS_HOST")
# # RDS_PORT = 3306
# # LOCAL_PORT = 3307

# # if __name__ == "__main__":
# #     # 터널 열기
# #     with SSHTunnelForwarder(
# #         (EC2_HOST, 22),
# #         ssh_username=EC2_USER,
# #         ssh_pkey=EC2_KEY_PATH,
# #         remote_bind_address=(RDS_HOST, RDS_PORT),
# #         local_bind_address=('127.0.0.1', LOCAL_PORT),
# #     ) as tunnel:
# #         print(f"SSH 터널: localhost:{LOCAL_PORT} → {RDS_HOST}:{RDS_PORT}")

# #         # Django 명령어 실행
# #         try:
# #             subprocess.run(["python", "manage.py"] + sys.argv[1:], check=True)
# #         except subprocess.CalledProcessError as e:
# #             print("명령어 에러", e)

# # run_with_tunnel.py (안전 버전)
# import subprocess, sys, os, json
# from sshtunnel import SSHTunnelForwarder
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent
# secrets = json.load(open(BASE_DIR / "secrets.json", encoding="utf-8"))

# def get_secret(k): return secrets[k]

# EC2_HOST = get_secret("EC2_HOST")
# EC2_USER = get_secret("EC2_USER")
# EC2_KEY_PATH = get_secret("EC2_KEY_PATH")
# RDS_HOST = get_secret("RDS_HOST"); RDS_PORT = 3306
# LOCAL_PORT = 0  # 충돌 방지 위해 자동 배정 권장

# def run_manage(args, env=None):
#     # 1) venv 파이썬 강제: 우선 venv 경로, 없으면 현재 인터프리터
#     venv_py = BASE_DIR / "venv" / "Scripts" / "python.exe"  # Windows
#     py = str(venv_py) if venv_py.exists() else sys.executable
#     # 2) 해당 파이썬으로 manage.py 실행
#     subprocess.run([py, "manage.py", *args], check=True, env=env)

# if __name__ == "__main__":
#     with SSHTunnelForwarder(
#         (EC2_HOST, 22),
#         ssh_username=EC2_USER,
#         ssh_pkey=EC2_KEY_PATH,
#         remote_bind_address=(RDS_HOST, RDS_PORT),
#         local_bind_address=("127.0.0.1", LOCAL_PORT),
#         set_keepalive=30, allow_agent=False, compression=True,
#     ) as tunnel:
#         port = tunnel.local_bind_port
#         print(f"SSH 터널: 127.0.0.1:{port} → {RDS_HOST}:{RDS_PORT}")

#         env = os.environ.copy()
#         env["DB_HOST"] = "127.0.0.1"
#         env["DB_PORT"] = str(port)

#         run_manage(sys.argv[1:], env=env)
