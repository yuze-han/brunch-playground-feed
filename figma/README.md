# Figma Sites 적용

`Playground.tsx` 전체를 Figma Sites Code Layer의 코드 편집기에 붙여 넣습니다.

1. Playground Desktop의 `Main` 콘텐츠 영역에 1030px 폭의 Code Layer를 만듭니다.
2. Code Layer를 열고 기존 코드를 모두 `Playground.tsx` 내용으로 교체합니다.
3. Inline preview에서 목록 2개가 표시되는지 확인합니다.
4. 첫 카드를 눌러 상세 본문, 이미지, 캡션, 다음 글, 브런치 원문 링크를 확인합니다.

Code Layer의 Width는 `Fill container`, Height는 `Hug contents`로 설정합니다. `Clip content`는 꺼야 긴 상세 본문이 잘리지 않습니다. 코드 편집기의 고정 높이 미리보기에서는 아래가 잘린 것처럼 보일 수 있으므로 전체 사이트 Preview에서도 확인합니다.

API 키나 별도 환경 변수는 필요하지 않습니다. Navigation과 Footer는 기존 Figma Sites 레이어를 유지하고 Code Layer에는 포함하지 않습니다. 현재 코드는 Desktop 전용입니다.
