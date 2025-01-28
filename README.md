# GCP를 이용한 24시간 디스코드 봇 실행 방법

이 문서는 Google Cloud Platform(GCP)을 사용하여 **디스코드 봇을 24시간 실행하는 방법**을 설명합니다.

## 1. GCP VM 인스턴스 생성

### 1.1 GCP 콘솔 접속
- **Google Cloud Console**: [GCP 콘솔](https://console.cloud.google.com/)
- **Compute Engine → VM 인스턴스** 이동

### 1.2 새로운 VM 인스턴스 생성
- **이름:** 
- **리전:** 
- **머신 타입:** 
- **부트 디스크:** 
- **방화벽:** 
- **생성** 

---

## 2. VM에 SSH 접속 및 환경 설정

### 2.1 SSH 접속
GCP 콘솔에서 **SSH 연결** 버튼을 클릭합니다.

### 2.2 필수 패키지 설치
```sh
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip ffmpeg -y
```
### 3. Python 패키지 설치
```sh
pip3 install discord yt-dlp asyncio python-dotenv
```

### 3.1 .env 파일 설정 (직접 업로드)
