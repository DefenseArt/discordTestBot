# GCP를 이용한 24시간 디스코드 봇 실행 방법

이 문서는 **Google Cloud Platform(GCP)**을 사용하여 **디스코드 봇을 24시간 실행하는 방법**을 설명합니다.

## 1. GCP VM 인스턴스 생성

### 1.1 GCP 콘솔 접속
- **Google Cloud Console**: [GCP 콘솔](https://console.cloud.google.com/)
- **Compute Engine → VM 인스턴스** 이동

### 1.2 새로운 VM 인스턴스 생성
- **이름:** `discord-bot`
- **리전:** 가까운 리전 선택 (예: `asia-northeast3` 서울)
- **머신 타입:** `e2-micro` (무료 티어 가능)
- **부트 디스크:** `Ubuntu 22.04 LTS` 선택
- **방화벽:** HTTP 및 HTTPS 트래픽 허용 체크
- **생성** 버튼 클릭 후 완료될 때까지 기다립니다.

---

## 2. VM에 SSH 접속 및 환경 설정

### 2.1 SSH 접속
GCP 콘솔에서 **SSH 연결** 버튼을 클릭합니다.

### 2.2 필수 패키지 설치
```sh
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip ffmpeg -y
```
