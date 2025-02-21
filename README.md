# Niimbot Printer Service
니임봇 프린터 서비스

## Overview | 개요
An automated QR code label printing service for laundry items using Supabase Realtime. The service monitors database changes in real-time and automatically prints QR codes using a Niimbot label printer.
세탁물 QR코드 라벨 자동 출력 서비스입니다. Supabase Realtime을 활용해 데이터베이스 변경사항을 실시간으로 감지하고 Niimbot 프린터로 자동 출력합니다.

## Key Features | 주요 기능
- Real-time Supabase event monitoring | Supabase 실시간 이벤트 모니터링
- Automatic QR code generation | QR코드 자동 생성
- Custom label layout per user | 사용자별 맞춤 라벨 레이아웃
- Asynchronous event processing | 비동기 이벤트 처리

## System Components | 시스템 구성
- `LaundryHandler`: Main service handler | 메인 서비스 핸들러
- `SupaDB`: Database integration | 데이터베이스 연동
- `RealtimeService`: Real-time event processing | 실시간 이벤트 처리
- `NiimbotPrint`: Printer control | 프린터 제어
- `ImageLayout`: QR code generation | QR코드 이미지 생성

## Requirements | 요구사항
- Python 3.11
- Required packages | 필수 패키지:
  - asyncio
  - Supabase client
  - Pillow
  - Niimbot driver

System Dependencies | 시스템 의존성:
```bash
sudo apt-get update
sudo apt-get install -y libopenjp2-7 python3-pil libjpeg-dev zlib1g-dev
```

## Setup | 설정
Environment Variables | 환경 변수:
```bash
DATABASE_URL=your_supabase_url
JWT=your_supabase_jwt
```

Installation | 설치:
```bash
pip install -r requirements.txt
```

## Usage | 사용법
```bash
python main.py
```

## Process Flow | 처리 흐름
1. Database change detection | 데이터베이스 변경 감지
2. Laundry information extraction | 세탁물 정보 추출
3. QR code generation | QR코드 생성
4. Label printing | 라벨 출력

## Logging | 로깅
- INFO: Operation status | 작업 상태
- WARNING: Non-critical issues | 경미한 문제
- ERROR: Critical problems | 심각한 문제 
- DEBUG: Detailed process info | 상세 처리 정보

## Important Notes | 주의사항
- Ensure printer connection | 프린터 연결 상태 확인
- Check label paper supply | 라벨 용지 잔량 확인
- Monitor printer battery | 프린터 배터리 확인

---