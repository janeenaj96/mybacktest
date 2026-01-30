# 금 김치프리미엄 백테스팅 - 무료 API 가이드

## 📌 데이터 수집 방법

이 가이드는 **무료로** 금 김치프리미엄 데이터를 수집하는 방법을 설명합니다.

---

## 🔧 필요한 라이브러리 설치

```bash
pip install yfinance pykrx requests pandas
```

---

## 📊 1. 국제 금 시세 (Yahoo Finance)

### 코드 예시:
```python
import yfinance as yf
import pandas as pd

# 금 선물 가격 (GC=F)
gold_ticker = yf.Ticker("GC=F")

# 특정 기간 데이터 가져오기
start_date = "2023-01-01"
end_date = "2024-01-29"

gold_data = gold_ticker.history(start=start_date, end=end_date)
print(gold_data[['Close']])  # USD/oz 가격
```

**데이터**: COMEX 금 선물 가격 (USD/온스)
**업데이트**: 실시간
**무료 제한**: 없음

---

## 💱 2. 환율 정보 (한국수출입은행 API)

### API 신청:
1. https://www.koreaexim.go.kr/ir/HPHKIR020M01 접속
2. 회원가입 후 API 인증키 발급 (무료)

### 코드 예시:
```python
import requests
from datetime import datetime

def get_exchange_rate(auth_key, date):
    """
    한국수출입은행 환율 API
    auth_key: 발급받은 인증키
    date: YYYYMMDD 형식
    """
    url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
    params = {
        'authkey': auth_key,
        'searchdate': date,
        'data': 'AP01'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # USD 환율 찾기
    for item in data:
        if item['cur_unit'] == 'USD':
            return float(item['deal_bas_r'].replace(',', ''))
    
    return None

# 사용 예시
auth_key = "YOUR_AUTH_KEY"  # 발급받은 키 입력
today = datetime.now().strftime("%Y%m%d")
usd_krw = get_exchange_rate(auth_key, today)
print(f"USD/KRW: {usd_krw}")
```

---

## 🇰🇷 3. 국내 금 시세 (pykrx)

### 코드 예시:
```python
from pykrx import stock

# KRX 금시장 데이터
# 주의: pykrx는 주식 데이터만 제공하므로, 금 시세는 다른 방법 필요

# 대안 1: 한국금거래소 웹사이트 스크래핑
import requests
from bs4 import BeautifulSoup

def get_domestic_gold_price():
    """
    한국금거래소 시세 (웹 스크래핑)
    """
    url = "http://www.koreagoldx.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 실제 HTML 구조에 맞게 수정 필요
    # 예시: price_element = soup.find('div', class_='price')
    
    return None  # 파싱된 가격 반환

# 대안 2: KRX 데이터마켓 CSV 다운로드
# http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020506
# 수동으로 CSV 다운로드 후 사용
```

### KRX 금현물 데이터 다운로드 (수동):
1. http://data.krx.co.kr 접속
2. 시장데이터 > 파생상품 > 금시장 > 금현물시세
3. 기간 설정 후 CSV 다운로드

---

## 🧮 4. 김치프리미엄 계산

```python
def calculate_kimchi_premium(domestic_price_krw_per_g, 
                             international_price_usd_per_oz, 
                             usd_krw_rate):
    """
    김치프리미엄 계산
    
    domestic_price_krw_per_g: 국내 금 가격 (원/g)
    international_price_usd_per_oz: 국제 금 가격 (달러/온스)
    usd_krw_rate: USD/KRW 환율
    """
    OZ_TO_GRAM = 31.1034768  # 1온스 = 31.1034768그램
    
    # 국제 금 가격을 원/g으로 환산
    international_price_krw_per_g = (international_price_usd_per_oz * usd_krw_rate) / OZ_TO_GRAM
    
    # 김치프리미엄 계산
    premium = ((domestic_price_krw_per_g / international_price_krw_per_g) - 1) * 100
    
    return round(premium, 2)

# 사용 예시
domestic = 85000  # 원/g
international = 2000  # USD/oz
exchange_rate = 1300  # USD/KRW

premium = calculate_kimchi_premium(domestic, international, exchange_rate)
print(f"김치프리미엄: {premium}%")
```

---

## 📁 5. 전체 데이터 수집 스크립트

```python
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

def collect_gold_data(start_date, end_date, exim_auth_key):
    """
    전체 금 데이터 수집
    """
    # 1. 국제 금 시세
    gold_ticker = yf.Ticker("GC=F")
    gold_data = gold_ticker.history(start=start_date, end=end_date)
    
    results = []
    
    for date, row in gold_data.iterrows():
        date_str = date.strftime("%Y%m%d")
        
        # 2. 환율 가져오기
        exchange_rate = get_exchange_rate(exim_auth_key, date_str)
        if not exchange_rate:
            continue
            
        # 3. 국내 금 시세 (여기서는 샘플 데이터)
        # 실제로는 KRX CSV 또는 웹 스크래핑 필요
        domestic_price = 85000  # 원/g (샘플)
        
        # 4. 김치프리미엄 계산
        international_usd_oz = row['Close']
        premium = calculate_kimchi_premium(
            domestic_price, 
            international_usd_oz, 
            exchange_rate
        )
        
        results.append({
            'date': date.strftime("%Y-%m-%d"),
            'domestic_price': domestic_price,
            'international_price': international_usd_oz,
            'exchange_rate': exchange_rate,
            'premium': premium
        })
    
    return pd.DataFrame(results)

# 실행
df = collect_gold_data("2023-01-01", "2024-01-29", "YOUR_AUTH_KEY")
df.to_csv("gold_kimchi_premium_data.csv", index=False, encoding='utf-8-sig')
print("데이터 저장 완료!")
```

---

## 🎯 권장 워크플로우

### 방법 1: API 직접 사용 (Python 스크립트)
1. 위 스크립트로 데이터 수집
2. CSV로 저장
3. HTML 백테스팅 도구에 업로드

### 방법 2: 수동 데이터 수집
1. **국제 금**: https://finance.yahoo.com/quote/GC=F/history
2. **환율**: https://www.koreaexim.go.kr/ir/HPHKIR020M01
3. **국내 금**: http://data.krx.co.kr (금현물시세)
4. Excel에서 김치프리미엄 계산
5. CSV로 저장

---

## 📝 CSV 파일 형식

백테스팅 도구에서 사용할 CSV 형식:

```csv
date,domestic_price,international_price,exchange_rate,premium
2023-01-01,85000,1850.5,1300.5,8.5
2023-01-02,86000,1855.0,1302.0,9.2
...
```

**컬럼 설명**:
- `date`: 날짜 (YYYY-MM-DD)
- `domestic_price`: 국내 금 가격 (원/g)
- `international_price`: 국제 금 가격 (USD/oz)
- `exchange_rate`: USD/KRW 환율
- `premium`: 김치프리미엄 (%)

---

## ⚠️ 주의사항

1. **한국수출입은행 API**: 인증키 발급 필수 (무료)
2. **KRX 금 데이터**: 공식 API 없음, CSV 다운로드 또는 스크래핑 필요
3. **Yahoo Finance**: 국제 금 선물 가격 (실제 현물과 약간 차이 있음)
4. **거래일**: 한국과 미국의 휴일이 다르므로 데이터 정합성 확인 필요

---

## 🚀 다음 단계

1. 한국수출입은행에서 API 키 발급
2. 위 스크립트 실행하여 데이터 수집
3. CSV 파일을 백테스팅 도구에 업로드
4. 백테스팅 결과 분석
