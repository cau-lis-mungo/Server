import json
from pathlib import Path
import mimetypes
import boto3
from botocore.exceptions import ClientError

# 설정
LOCAL_DIR = r"C:\Users\wertt\OneDrive\바탕 화면\표지" # 로컬 표지 폴더 경로
BUCKET = "cau-lis-mungo"
PREFIX = "books/"
PUBLIC_READ = True

# secrets.json 불러오기
secrets_path = Path(r"C:\Users\wertt\OneDrive\바탕 화면\Server\secrets.json") # 로컬 secrets.json 경로
if not secrets_path.exists():
    raise FileNotFoundError("secrets.json 파일이 없습니다!")

with open(secrets_path, "r") as f:
    secrets = json.load(f)

aws_access_key = secrets.get("AWS_ACCESS_KEY_ID")
aws_secret_key = secrets.get("AWS_SECRET_ACCESS_KEY")
aws_region = "ap-northeast-2"

s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region
)

def upload_cover(file_path: Path):
    key = f"{PREFIX}{file_path.name}"
    ctype, _ = mimetypes.guess_type(file_path.name)
    extra_args = {"ContentType": ctype or "application/octet-stream"}

    try:
        s3.upload_file(str(file_path), BUCKET, key, ExtraArgs=extra_args)
        print(f"업로드 완료: {key}")
    except ClientError as e:
        print(f"업로드 실패 ({file_path.name}): {e}")

def main():
    folder = Path(LOCAL_DIR)
    if not folder.exists():
        print(f"폴더를 찾을 수 없습니다: {folder}")
        return

    files = [f for f in folder.iterdir() if f.is_file()]
    if not files:
        print("업로드할 파일이 없습니다.")
        return

    print(f"총 {len(files)}개 파일 업로드 시작...")
    for f in files:
        upload_cover(f)
    print("모든 파일 업로드 완료!")

if __name__ == "__main__":
    main()
