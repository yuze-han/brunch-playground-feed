# Brunch Playground Feed

브런치 작가 피드를 읽어 `yuzehan.com`의 Playground에서 사용할 정적 JSON을 생성합니다.

## 생성되는 파일

- `data/index.json`: 카드 목록
- `data/articles/<slug>.json`: 개별 글 상세 데이터. 문단, 소제목, 인용문, 이미지 순서를 `contentBlocks`에 보존합니다.

## 로컬 실행

```bash
python3 scripts/sync_brunch.py
python3 -m unittest discover -s tests
npm install
npm run dev
```

GitHub Actions가 매일 03:17(KST)에 실행되며, 새 글이나 변경된 글이 있을 때만 JSON을 갱신합니다. 네트워크 요청은 최대 세 번 재시도하고, RSS가 일시적으로 빈 응답을 반환하면 기존 목록을 유지한 채 실패 처리합니다.

브런치 RSS가 나중에 최신 글 일부만 제공하더라도 이미 수집한 오래된 글은 목록 뒤에 보존하므로 Playground 아카이브가 줄어들지 않습니다.

동기화 후 `scripts/validate_data.py`가 목록과 상세 데이터의 일치 여부, 필수 필드, 중복 ID, 본문 블록, HTTPS 이미지 URL을 검사합니다. 검증 실패 시 잘못된 데이터는 커밋되지 않습니다.

로컬 미리보기는 데스크톱 동작과 상세 본문 순서를 검수하기 위한 용도입니다. 현재 반응형 조정은 의도적으로 포함하지 않았습니다.

## Figma Sites 연결

`figma/Playground.tsx`를 Playground용 Code Layer 또는 Code Component에 붙여 넣습니다.
컴포넌트는 아래 공개 JSON을 읽습니다.

```text
https://raw.githubusercontent.com/yuze-han/brunch-playground-feed/main/data/index.json
```
