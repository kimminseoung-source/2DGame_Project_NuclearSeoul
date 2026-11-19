# 주인공 생성 프롬프트 (2026-11-19)

설계: 건장하지만 과하지 않은 20대 중반 한국 남성(어깨는 보통보다 조금 넓게), 검정 항공점퍼(주황 안감) + 소매 걷음 + 흰 티 + 청바지. 오른팔이 칼날로 변이한다.
사용자 피드백: "별로다, 건장한 성인 청년으로" → "어깨가 너무 넓은데, 그냥 적절하게 프롬프트 줘 봐, 생성해 볼게". 기록은 `../ART_FEEDBACK.md`.

## 1. 큰 그림 (설정화, 무료 AI 그림 도구)

```
Full-body character concept art of a Korean man in his mid-20s. Fit, athletic build with
natural, only slightly broad shoulders (not bulky, not a bodybuilder), about 7.5 heads tall,
upright posture. Short black hair, light stubble, tired but determined eyes.
Black MA-1 bomber jacket with orange lining visible at the collar, sleeves pushed up to the
elbows showing his forearms, plain white t-shirt, dark blue jeans, worn white sneakers,
small dark crossbody bag. Light dust and scratches, a bandage wrapped on his left hand.
Front view, neutral standing pose, arms slightly away from the body.
Plain light gray background. Semi-realistic illustration, muted cold colors,
post-nuclear-disaster Korea. Clean readable silhouette.
No weapon, no gas mask, no hood, no cape, no armor.
```

## 2. 큰 그림, 칼날 팔 (1번 결과를 참고 이미지로 넣고)

```
Same man, same outfit and face. His right arm has mutated from radiation:
the right jacket sleeve is torn off at the shoulder, the arm is swollen and gray-violet
with faintly glowing violet cracks, and the forearm bone extends past the hand into one
long, pale, slightly curved blade. The rest of his body is still fully human.
Front view, same pose, plain light gray background, same art style.
```

## 3. 게임 도트 (PixelLab)

```
young Korean man, fit athletic build, short black hair, black bomber jacket with orange
lining, sleeves rolled up, white t-shirt, dark blue jeans, white sneakers, small crossbody bag
```

설정: 크기 32px(작으면 48px), 시점 low top-down, 8방향, 외곽선 single color black, 명암 basic, 디테일 medium. 1번 그림이 있으면 참고 이미지로 넣는다.

## 4. 기준 그림 v1 (ChatGPT, 2026-11-19)

`ref_chatgpt_v1.png`. 사용자 "요런 느낌으로 해 보자". 살릴 것: 체격(적당히 단단함), 얼굴, 어두운 도트풍, 몸 위 노드(변이 부위 고르기 화면 아이디어). 바꿀 것: 군인 장비(하네스·파우치·카고·전투화) → 평범한 옷, 포인트 색 하나, 변이 색은 보라 하나, 기본 그림은 사람 모습.

이 그림을 참고 이미지로 넣고:

```
Use the attached image as the style and character reference: same young Korean man,
same face, hair, body build, pose, and the same dark detailed pixel-art style and background.
Change only these things:
1. Outfit: an ordinary civilian, not a soldier. Black bomber jacket with orange lining,
   sleeves pushed up to the elbows, plain white t-shirt, dark jeans, worn white sneakers,
   one small crossbody bag strap. Remove the harness, chest straps, belt pouches,
   thigh pouch, cargo pants and combat boots.
2. Both arms are fully human (no mutation) in this version.
3. Keep the glowing nodes and lines on the body parts (arms, chest, knees), but make
   every node and line one color: violet.
```

칼날 팔 버전: 위 결과를 넣고 "Same image, but only his right forearm has mutated into a long pale curved bone blade with glowing violet cracks; the right sleeve is torn. The left arm stays human. The right arm node glows brighter."

## 결과 넣는 곳

이 폴더(`assets/characters/hero_concept/`)에 저장: `concept_human.png`, `concept_blade.png`, PixelLab은 `pixellab/` 폴더.

## 5. 기준 그림 v2: 작업 재킷 (2026-11-19)

`ref_v2_workjacket.png`. 사용자 "이걸 기반으로 해서 만들어 보려고 하는데 프롬프트 주세요". 갈색 작업 재킷(소매 걷음), 회색 티, 짙은 카고바지, 갈색 부츠, 헝클어진 검은 머리. 시안 B(작업 재킷)와 같은 방향. 갈색은 중간 밝기라 어두운 거리에서 검정보다 잘 보인다.

PixelLab (이 그림을 참고 이미지로):

```
young Korean man in his mid-20s, fit build, messy spiky black hair, brown canvas work
jacket worn open with sleeves rolled up to the elbows, bare forearms, plain gray t-shirt,
dark belt, dark navy cargo pants, brown leather lace-up boots, no weapon, no bag
```

설정: 크기 **32px**(게임 속 사람 키 32px과 맞음. 48px는 게임에서 1.4배 커짐), 시점 low top-down, 8방향, 외곽선 single color black, 명암 medium, 디테일 medium.

칼날 팔(나중에): 같은 캐릭터에 "right forearm mutated into a long pale curved bone blade with faint violet glowing cracks, right sleeve torn off, left arm human".
