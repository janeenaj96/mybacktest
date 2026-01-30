# 금 김치프리미엄 백테스팅 도구 - 완벽 설치 가이드

## 📋 목차
1. [시스템 요구사항](#시스템-요구사항)
2. [Python 환경 설정](#python-환경-설정)
3. [API 키 발급](#api-키-발급)
4. [데이터 수집 스크립트 실행](#데이터-수집-스크립트-실행)
5. [백테스팅 도구 실행](#백테스팅-도구-실행)
6. [문제 해결](#문제-해결)

---

## 1. 시스템 요구사항

### 필수 프로그램
- **Python 3.8 이상** (3.9 이상 권장)
- 웹 브라우저 (Chrome, Firefox, Safari 등)

### 확인 방법
```bash
# Python 버전 확인
python --version
# 또는
python3 --version
```

---

## 2. Python 환경 설정

### 단계 1: 작업 폴더 생성
```bash
# 터미널/명령 프롬프트에서 실행
mkdir gold_backtest
cd gold_backtest
```

### 단계 2: 필수 라이브러리 설치
```bash
# Windows
pip install yfinance requests pandas

# Mac/Linux
pip3 install yfinance requests pandas
```

**설치되는 라이브러리:**
- `yfinance`: 국제 금 시세 데이터
- `requests`: HTTP 요청 (환율 API)
- `pandas`: 데이터 처리 및 CSV 저장

### 단계 3: 설치 확인
```bash
python -c "import yfinance, requests, pandas; print('설치 완료!')"
```

---

## 3. API 키 발급

### A. 한국수출입은행 환율 API (필수)

#### 3-1. 회원가입
1. https://www.koreaexim.go.kr 접속
2. 상단 [회원가입] 클릭
3. 개인 회원가입 진행

#### 3-2. API 인증키 발급
1. 로그인 후 https://www.koreaexim.go.kr/ir/HPHKIR020M01 접속
2. **환율정보 OpenAPI 이용신청** 클릭
3. **서비스 인증키 발급** 버튼 클릭
4. **인증키 저장** (예: `ABC123DEF456GHI789`)

**⚠️ 중요:** 발급받은 인증키를 안전한 곳에 복사해두세요!

---

### B. KRX 금 시세 데이터 (수동 다운로드)

#### 옵션 1: KRX 데이터마켓 (권장)
1. http://data.krx.co.kr 접속
2. 회원가입 (무료)
3. **시장데이터 > 파생상품 > 금시장 > 금현물시세** 이동
4. 원하는 기간 설정 후 **CSV 다운로드**

#### 옵션 2: 한국금거래소
1. http://www.koreagoldx.com 접속
2. 시세정보 확인 (실시간)
3. 수동으로 데이터 기록

---

## 4. 데이터 수집 스크립트 실행

### 단계 1: 데이터 수집 스크립트 생성

아래 코드를 `collect_gold_data.py` 파일로 저장하세요:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
금 김치프리미엄 데이터 수집 스크립트
"""

import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta

# ==================== 설정 영역 ====================
# ⚠️ 여기에 발급받은 API 키를 입력하세요!
EXIM_API_KEY = "여기에_발급받은_API_키_입력"  # 예: "ABC123DEF456GHI789"

# 데이터 수집 기간 설정
START_DATE = "2023-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")
# ===================================================

def get_exchange_rate(auth_key, date_str):
    """
    한국수출입은행 환율 API 호출
    
    Args:
        auth_key: API 인증키
        date_str: YYYYMMDD 형식의 날짜
    
    Returns:
        float: USD/KRW 환율, 실패 시 None
    """
    url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
    params = {
        'authkey': auth_key,
        'searchdate': date_str,
        'data': 'AP01'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print(f"환율 API 오류 ({date_str}): HTTP {response.status_code}")
            return None
            
        data = response.json()
        
        # USD 환율 찾기
        for item in data:
            if item.get('cur_unit') == 'USD':
                rate = item.get('deal_bas_r', '').replace(',', '')
                return float(rate) if rate else None
        
        print(f"USD 환율을 찾을 수 없음 ({date_str})")
        return None
        
    except Exception as e:
        print(f"환율 조회 오류 ({date_str}): {e}")
        return None


def calculate_kimchi_premium(domestic_price_krw_g, international_price_usd_oz, exchange_rate):
    """
    김치프리미엄 계산
    
    Args:
        domestic_price_krw_g: 국내 금 가격 (원/g)
        international_price_usd_oz: 국제 금 가격 (USD/oz)
        exchange_rate: USD/KRW 환율
    
    Returns:
        float: 김치프리미엄 (%)
    """
    OZ_TO_GRAM = 31.1034768
    
    # 국제 금 가격을 원/g으로 환산
    international_krw_g = (international_price_usd_oz * exchange_rate) / OZ_TO_GRAM
    
    # 김치프리미엄 계산
    premium = ((domestic_price_krw_g / international_krw_g) - 1) * 100
    
    return round(premium, 2)


def collect_data(start_date, end_date, api_key):
    """
    금 데이터 수집 메인 함수
    """
    print("=" * 60)
    print("금 김치프리미엄 데이터 수집 시작")
    print("=" * 60)
    
    # API 키 확인
    if api_key == "여기에_발급받은_API_키_입력" or not api_key:
        print("\n⚠️  오류: API 키가 설정되지 않았습니다!")
        print("스크립트 상단의 EXIM_API_KEY 변수에 발급받은 키를 입력하세요.\n")
        return None
    
    print(f"\n📅 수집 기간: {start_date} ~ {end_date}")
    print(f"🔑 API 키: {api_key[:10]}...")
    
    # 1. 국제 금 시세 수집
    print("\n[1/3] 국제 금 시세 수집 중...")
    try:
        gold_ticker = yf.Ticker("GC=F")
        gold_data = gold_ticker.history(start=start_date, end=end_date)
        print(f"✓ {len(gold_data)}일의 국제 금 시세 수집 완료")
    except Exception as e:
        print(f"✗ 국제 금 시세 수집 실패: {e}")
        return None
    
    # 2. 환율 및 김치프리미엄 계산
    print("\n[2/3] 환율 조회 및 김치프리미엄 계산 중...")
    results = []
    success_count = 0
    fail_count = 0
    
    for date, row in gold_data.iterrows():
        date_str = date.strftime("%Y%m%d")
        
        # 환율 조회
        exchange_rate = get_exchange_rate(api_key, date_str)
        
        if exchange_rate is None:
            fail_count += 1
            continue
        
        # 국내 금 시세 (임시값 - 실제 데이터로 대체 필요)
        # KRX CSV를 업로드했다면 여기서 매칭
        domestic_price = 85000  # 원/g (샘플값)
        
        # 국제 금 시세
        international_price = row['Close']  # USD/oz
        
        # 김치프리미엄 계산
        premium = calculate_kimchi_premium(
            domestic_price,
            international_price,
            exchange_rate
        )
        
        results.append({
            'date': date.strftime("%Y-%m-%d"),
            'domestic_price': domestic_price,
            'international_price': round(international_price, 2),
            'exchange_rate': exchange_rate,
            'premium': premium
        })
        
        success_count += 1
        
        # 진행상황 표시
        if success_count % 50 == 0:
            print(f"  진행중... {success_count}/{len(gold_data)}")
    
    print(f"✓ 완료: 성공 {success_count}건, 실패 {fail_count}건")
    
    # 3. CSV 저장
    print("\n[3/3] CSV 파일 저장 중...")
    df = pd.DataFrame(results)
    
    filename = f"gold_data_{start_date}_{end_date}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"✓ 파일 저장 완료: {filename}")
    print(f"  총 {len(df)}개의 데이터 행 저장됨")
    
    # 통계 출력
    print("\n" + "=" * 60)
    print("📊 데이터 통계")
    print("=" * 60)
    print(f"평균 김치프리미엄: {df['premium'].mean():.2f}%")
    print(f"최대 김치프리미엄: {df['premium'].max():.2f}%")
    print(f"최소 김치프리미엄: {df['premium'].min():.2f}%")
    print(f"평균 환율: {df['exchange_rate'].mean():.2f} 원")
    
    return df


if __name__ == "__main__":
    # 데이터 수집 실행
    df = collect_data(START_DATE, END_DATE, EXIM_API_KEY)
    
    if df is not None:
        print("\n✅ 데이터 수집이 완료되었습니다!")
        print("📁 생성된 CSV 파일을 백테스팅 도구에 업로드하세요.")
    else:
        print("\n❌ 데이터 수집에 실패했습니다.")
```

### 단계 2: API 키 입력

스크립트 파일을 열고 **10번째 줄** 수정:
```python
EXIM_API_KEY = "ABC123DEF456GHI789"  # 발급받은 실제 키로 교체
```

### 단계 3: 스크립트 실행

```bash
# 실행
python collect_gold_data.py

# 또는
python3 collect_gold_data.py
```

### 단계 4: 결과 확인

실행이 완료되면 다음 파일이 생성됩니다:
```
gold_data_2023-01-01_2026-01-29.csv
```

---

## 5. 백테스팅 도구 실행

### 단계 1: HTML 파일 다운로드
1. 제공된 `gold_backtest_v2.html` 파일을 다운로드
2. 같은 폴더에 저장

### 단계 2: 웹 브라우저로 열기
```bash
# 방법 1: 파일 더블클릭

# 방법 2: 브라우저에서 직접 열기
# Chrome: Ctrl+O (Windows) / Cmd+O (Mac)
# 파일 선택: gold_backtest_v2.html
```

### 단계 3: 백테스팅 실행

#### 옵션 A: 샘플 데이터로 테스트
1. **"샘플 데이터"** 탭 선택
2. 기간, 매매 조건 설정
3. **"샘플 데이터로 백테스팅 시작"** 버튼 클릭

#### 옵션 B: 실제 데이터로 백테스팅
1. **"CSV 업로드"** 탭 선택
2. 생성된 CSV 파일 업로드
3. 매매 조건 설정
4. **"업로드된 데이터로 백테스팅 시작"** 버튼 클릭

---

## 6. 문제 해결

### 문제 1: Python 설치 안 됨
**증상**: `python: command not found`

**해결방법**:
```bash
# Windows
https://www.python.org/downloads/ 에서 다운로드

# Mac (Homebrew 사용)
brew install python3

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip
```

### 문제 2: 라이브러리 설치 실패
**증상**: `pip: command not found`

**해결방법**:
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 또는
python3 -m pip install --upgrade pip
```

### 문제 3: API 키 오류
**증상**: `환율 API 오류: HTTP 401`

**해결방법**:
1. API 키가 정확히 입력되었는지 확인
2. 공백이나 따옴표가 없는지 확인
3. 한국수출입은행 사이트에서 키 재확인

### 문제 4: 국내 금 시세 없음
**증상**: 모든 김치프리미엄이 동일함

**해결방법**:
현재 스크립트는 국내 금 시세를 고정값(85,000원/g)으로 사용합니다.

**실제 데이터 반영 방법**:
1. KRX에서 금현물시세 CSV 다운로드
2. 스크립트의 `# 국내 금 시세 (임시값)` 부분을 수정:

```python
# KRX CSV 읽기 예시
krx_data = pd.read_csv('krx_gold_prices.csv')
# date로 매칭하여 실제 가격 사용
domestic_price = krx_data[krx_data['date'] == date_str]['price'].values[0]
```

### 문제 5: CSV 업로드 오류
**증상**: `필수 컬럼이 누락되었습니다`

**해결방법**:
CSV 파일이 다음 컬럼을 포함하는지 확인:
- `date`
- `domestic_price`
- `premium`

---

## 📌 빠른 시작 체크리스트

- [ ] Python 3.8 이상 설치 확인
- [ ] 필수 라이브러리 설치 (`yfinance`, `requests`, `pandas`)
- [ ] 한국수출입은행 API 키 발급
- [ ] `collect_gold_data.py` 파일 생성
- [ ] API 키를 스크립트에 입력
- [ ] 스크립트 실행하여 CSV 생성
- [ ] `gold_backtest_v2.html` 다운로드
- [ ] 브라우저에서 HTML 파일 열기
- [ ] CSV 업로드하여 백테스팅 실행

---

## 🎯 추천 설정값

### 보수적 전략
- 매수 김치프리미엄: **3% 이하**
- 매도 김치프리미엄: **8% 이상**

### 적극적 전략
- 매수 김치프리미엄: **5% 이하**
- 매도 김치프리미엄: **10% 이상**

### 공격적 전략
- 매수 김치프리미엄: **7% 이하**
- 매도 김치프리미엄: **12% 이상**

---

## 📞 추가 도움말

- **한국수출입은행 API**: https://www.koreaexim.go.kr/ir/HPHKIR020M01
- **KRX 데이터마켓**: http://data.krx.co.kr
- **Python 공식 문서**: https://docs.python.org/ko/3/

---

## ⚠️ 면책사항

이 도구는 교육 및 연구 목적으로만 제공됩니다. 
실제 투자 결정에 사용하기 전에 반드시 전문가와 상담하세요.
과거 수익률이 미래 수익을 보장하지 않습니다.
