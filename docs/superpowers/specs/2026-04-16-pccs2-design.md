# PCCS2 Design Specification

**Date:** 2026-04-16
**Version:** 1.0

---

## 1. 시스템 개요

### 1.1 목적
타겟 컬러 (Lab 값) 와 인쇄 조건 (동판 깊이，베이스 컬러) 을 입력하면，최적의 잉크 배합비를 추천하는 시스템을 구축한다. 사용자가 데이터를 축적할수록 추천 정확도가 자동으로 향상되는 자기학습 구조를 갖는다.

### 1.2 핵심 원리
시스템은 2 단계 하이브리드 엔진으로 작동한다:
1. **1 단계:** 수정된 Kubelka-Munk 이론 기반 물리 모델
2. **2 단계:** 축적된 실측 데이터 기반 머신러닝 보정

### 1.3 잉크 분류 체계

| 카테고리 | 잉크명 | 처리 방식 |
|---------|-----|---|
| 투명 베이스 | 투명 (무광), 투명 (유광) | 색 성분 |
| 컬러 잉크 | 흰색，검정，레드，블루 등 | 색 성분 |
| 특수 첨가제 | 실버，소광제 | 색 성분 |
| 공정 보조제 | 경화제 | **색 성분 (투명 유광 합산)** |
| 공정 보조제 | 신너 | **휘발 성분 (색 성분 제외)** |

---

## 2. 데이터 모델

### 2.1 Project (프로젝트)
```
Project {
    project_id: string (PK)
    project_name: string
    customer: string (optional)
    status: IN_PROGRESS | COMPLETED | ON_HOLD
    start_date: date
    target_completion: date
    memo: string
    created_at: datetime
    updated_at: datetime
}
```

### 2.2 Pattern (패턴)
```
Pattern {
    pattern_id: string (PK)
    project_id: string (FK)
    pattern_name: string
    total_print_layers: int  (총 인쇄 도수)
    target_base_color_sci: {L, a, b}
    target_base_color_sce: {L, a, b}
    target_base_material: string
    status: DEVELOPING | COMPLETED | ON_HOLD
    notes: string
    approved_sample_id: string (FK)
    success_rate: float
    avg_delta_e: float
    created_at: datetime
    updated_at: datetime
}
```

### 2.3 Round (작업 라운드)
```
Round {
    round_id: string (PK)
    pattern_id: string (FK)
    round_number: int
    work_date: date
    operator: string
    work_location: string
    created_at: datetime
    updated_at: datetime
}
```

### 2.4 Sample (샘플)
```
Sample {
    sample_id: string (PK)
    round_id: string (FK)
    pattern_id: string (FK)
    sample_number: int

    base_color_sci: {L, a, b}
    base_color_sce: {L, a, b}
    base_material: string

    layers: [{
        layer_number: int
        ink_items: [{ink_id, amount}]
        thinner_pct: float
        hardener_pct: float
        print_color_sci: {L, a, b}
        print_color_sce: {L, a, b}
        delta_E_from_target: float
        note: string
    }]

    final_delta_e: float
    success_flag: SUCCESS | FAILED | PENDING
    success_notes: string
    created_at: datetime
    updated_at: datetime
}
```

### 2.5 Ink (마스터 잉크)
```
Ink {
    ink_id: string (PK)
    ink_name: string
    ink_category: COLOR | TRANSPARENT | EFFECT | ADDITIVE
    manufacturer: string
    is_blend_ink: bool
    blend_recipe: JSON (optional)
    solid_color_sci: {L, a, b}
    solid_color_sce: {L, a, b}
    delta_sci_sce: float (auto)
    gloss_index: float (auto)
    gloss_GU: float
    viscosity: float
    density: float
    memo: string
    registered_at: datetime
    updated_at: datetime
}
```

---

## 3. 핵심 기능

### 3.1 배합비 복사
- 샘플 리스트에서 특정 샘플의 "베이스", "1 도", "2 도" 버튼 클릭
- 현재 편집 중인 Sample 입력창에 해당 레이어 정보 자동 로드

### 3.2 마스터 잉크 등록
- 배합비 옆 "마스터 잉크로 등록" 버튼
- 배합 잉크를 마스터 잉크로 등록 (is_blend_ink=True)

### 3.3 SCI/SCE 입력
- 베이스 컬러: SCI + SCE 입력
- 인쇄 결과 (레이어별): SCI + SCE 입력
- 자동 파생: ΔE(SCI-SCE), 광택 지수

### 3.4 배합비 시각화
- InkDonutChart: 레이어별 배합 비율 시각화
- 호버 시 잉크명 + 비율 표시
- 총중량, 신너 비율 표시

---

## 4. API 엔드포인트

```
POST   /api/projects/              # 프로젝트 생성
GET    /api/projects/              # 프로젝트 목록
GET    /api/projects/{id}          # 프로젝트 상세
PUT    /api/projects/{id}          # 프로젝트 수정
DELETE /api/projects/{id}          # 프로젝트 삭제

POST   /api/patterns/              # 패턴 생성
GET    /api/patterns/              # 패턴 목록
GET    /api/patterns/{id}          # 패턴 상세
PUT    /api/patterns/{id}          # 패턴 수정
DELETE /api/patterns/{id}          # 패턴 삭제

POST   /api/rounds/pattern/{id}    # 라운드 생성
GET    /api/rounds/                # 라운드 목록
GET    /api/rounds/{id}            # 라운드 상세
PUT    /api/rounds/{id}            # 라운드 수정
DELETE /api/rounds/{id}            # 라운드 삭제

POST   /api/samples/round/{id}     # 샘플 생성
GET    /api/samples/               # 샘플 목록
GET    /api/samples/{id}           # 샘플 상세
PUT    /api/samples/{id}           # 샘플 수정
DELETE /api/samples/{id}           # 샘플 삭제
POST   /api/samples/{id}/copy-layer # 배합비 복사

POST   /api/inks/                  # 잉크 생성
GET    /api/inks/                  # 잉크 목록
GET    /api/inks/{id}              # 잉크 상세
PUT    /api/inks/{id}              # 잉크 수정
DELETE /api/inks/{id}              # 잉크 삭제
POST   /api/inks/{id}/register-blend # 마스터 잉크 등록

POST   /api/match/                 # 배합 추천
```

---

## 5. 구현 우선순위

### Phase 1 — Backend Foundation
- [x] 데이터 모델 정의
- [x] API 엔드포인트
- [x] 색 계산 서비스

### Phase 2 — Engine Implementation
- 1 단계 K-M 엔진
- 2 단계 ML 엔진

### Phase 3 — Frontend
- 프로젝트/패턴 관리 UI
- 샘플 입력 UI (SCI/SCE 입력)
- 배합비 시각화

### Phase 4 — Integration
- 추천 기능 연결
- 피드백 루프
