# Brunch Playground Feed

브런치 작가 피드를 읽어 `yuzehan.com`의 Playground에서 사용할 정적 JSON을 생성합니다.

## 생성되는 파일

- `data/index.json`: 카드 목록
- `data/articles/<slug>.json`: 개별 글 상세 데이터

## 로컬 실행

```bash
python3 scripts/sync_brunch.py
python3 -m unittest discover -s tests
```

GitHub Actions가 매일 한 번 실행되며, 새 글이나 변경된 글이 있을 때만 JSON을 갱신합니다.

## Figma Sites 연결

`figma/Playground.tsx`를 Playground용 Code Layer 또는 Code Component에 붙여 넣습니다.
컴포넌트는 아래 공개 JSON을 읽습니다.

```text
https://raw.githubusercontent.com/yuze-han/brunch-playground-feed/main/data/index.json
```
