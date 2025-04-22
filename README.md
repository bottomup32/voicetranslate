# 음성 번역 애플리케이션 (Voice Translation App)

이 애플리케이션은 한국어와 영어 음성을 실시간으로 감지하고, 감지된 언어를 반대 언어로 번역하여 텍스트로 보여줍니다.

## 기능 (Features)

- 한국어 ↔ 영어 양방향 음성 번역
- 자동 언어 감지 (Automatic language detection)
- 실시간 처리 (Real-time processing)
- 직관적인 사용자 인터페이스 (Intuitive user interface)

## 설치 방법 (Installation)

1. 필요한 라이브러리 설치:
```
pip install -r requirements.txt
```

2. OpenAI API 키 설정:
   - `.env` 파일에 OpenAI API 키 추가 (이미 저장되어 있음)
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## 사용 방법 (Usage)

1. 프로그램 실행:
```
python app.py
```

2. "Start Translation" 버튼을 클릭하여 번역 시작
3. 한국어 또는 영어로 말하면 자동으로 번역됨
4. "Stop Translation" 버튼을 클릭하여 번역 중지
5. "Clear Text" 버튼으로 번역 결과 초기화
6. "Exit" 버튼으로 프로그램 종료

## 참고 사항 (Notes)

- 마이크가 필요합니다.
- 인터넷 연결이 필요합니다 (OpenAI API 사용).
- `silence_threshold` 값은 마이크 환경에 따라 조정이 필요할 수 있습니다. 