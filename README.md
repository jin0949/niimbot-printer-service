# Niimbot Printer Service

자동 세탁물 QR코드 라벨 프린팅 서비스입니다. Supabase Realtime을 활용하여 데이터베이스 변경 사항을 실시간으로 감지하고, Niimbot 라벨 프린터로 QR코드를 자동 출력합니다.

## 주요 기능

- Supabase Realtime 이벤트 실시간 모니터링
- 세탁물 정보 기반 QR코드 자동 생성
- 사용자별 커스텀 라벨 레이아웃 지원
- 비동기 이벤트 처리 시스템

## 시스템 구성

- `LaundryHandler`: 메인 서비스 핸들러
- `SupaDB`: Supabase 데이터베이스 연동
- `RealtimeService`: 실시간 이벤트 처리
- `NiimbotPrint`: 라벨 프린터 제어
- `ImageLayout`: QR코드 이미지 생성

## 설치 요구사항

- Python 3.7+
- asyncio
- Supabase 클라이언트
- Niimbot 프린터 드라이버

## 환경 설정

서비스 실행을 위해 다음 환경 변수가 필요합니다:
- DATABASE_URL
- JWT

## 사용 방법

1. 환경 변수 설정
2. 필요한 패키지 설치
3. 메인 스크립트 실행

```bash
python main.py
```

pillow 종속성 설치
```bash
sudo apt-get update
sudo apt-get install -y libopenjp2-7 python3-pil libjpeg-dev zlib1g-dev
```

## 프로세스 흐름

1. 데이터베이스 변경 감지
2. 세탁물 정보 추출
3. QR코드 생성
4. 라벨 프린팅

---
