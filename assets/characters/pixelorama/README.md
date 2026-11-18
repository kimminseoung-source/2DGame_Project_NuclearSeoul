# Pixelorama로 캐릭터 손질하기

2026-11-18 사용자: "지금까지 한 거를 pixelorama로 해 보죠". 지금 캐릭터는 Blender 3D 렌더를 32px 도트로 줄여서 만든다. 그 위에 **손으로 다듬는 단계**를 더한다(윤곽, 얼굴, 손, 옷 주름, 피폭 상처).

## 폴더

| 위치 | 무엇 |
|---|---|
| `work/<캐릭터>/<동작>.png` | **열어서 고칠 시트**(게임 것의 복사본) |
| `guide/<캐릭터>_<동작>.png` | 8배 확대, 프레임 번호, 파란 선 = 발 위치 |
| `palette_busan.gpl` | 게임 전체 색 30개(Pixelorama 팔레트) |
| `before/` | 게임에 넣기 전 원본(처음 한 번만 보관) |
| `compare/` | 넣은 뒤 전(위)·후(아래) 비교 |

지금 준비된 시트: 피폭체 `idle`(4프레임)·`walk`(12)·`attack`(8), 주인공 `idle`(4)·`walk`(12). **처음엔 피폭체 `idle` 하나만.**

## 순서

1. **설치:** [Pixelorama 공식 GitHub 릴리스](https://github.com/Orama-Interactive/Pixelorama/releases) 또는 [itch.io](https://orama-interactive.itch.io/pixelorama)에서 Windows 버전 받기 → 압축 풀고 실행.
2. **팔레트:** 팔레트 패널 → 가져오기(Import) → `palette_busan.gpl`. 이 색으로만 칠하면 게임 다른 그림과 어울린다.
3. **시트 열기:** 파일 → 가져오기(Import) → `work/infected_dot/idle.png` → **스프라이트 시트**로, 가로 **4**칸, 세로 **1**칸(프레임 수는 guide 그림 위쪽 글에 있다). 그러면 프레임 4개로 나뉜다.
4. **다듬기:** 연필 도구 + "픽셀 퍼펙트" 켜기. 앞뒤 프레임 겹쳐 보기(어니언 스킨)를 켜면 움직임이 튀지 않게 맞추기 쉽다.
   - 윤곽선은 1픽셀 어두운 색으로 끊김 없이
   - 머리·얼굴이 몸과 구분되게(지금은 덩어리처럼 보임)
   - 피폭 상처의 초록 빛을 또렷하게
   - **발 위치(파란 선)와 칸 크기 64×48은 그대로.** 바뀌면 캐릭터가 튄다
   - 반투명 픽셀은 쓰지 않는다(넣을 때 꽉 찬 픽셀로 바꾼다)
5. **저장:** 프로젝트 파일(.pxo)은 이 폴더에 따로 저장해 두고, 파일 → 내보내기(Export) → **스프라이트 시트**, 가로 4·세로 1, 크기 1배로 `work/infected_dot/idle.png`에 덮어쓰기.
6. **게임에 넣기:** Claude에게 말하면 아래를 돌리고 게임 안 전후 화면을 보여 준다.

```
.venv\Scripts\python.exe tools/sprites/pixelorama_kit.py in infected_dot/idle
```

다른 시트를 준비하려면: `.venv\Scripts\python.exe tools/sprites/pixelorama_kit.py kit hero_dot/run`
