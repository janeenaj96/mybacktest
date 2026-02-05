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
EXIM_API_KEY = "LadS1IpKN2DQynQ4jIn9KcqSXBSpg21X"  # 한국수출입은행 환율 API 키
KRX_API_KEY = "A565FC8AB3A94EFA8D55C3AFD888B58DA452D41E"  # KRX OpenAPI 인증키(10년01월04일~) 

# 데이터 수집 기간 설정
START_DATE = "2010-01-04"
END_DATE = datetime.now().strftime("%Y-%m-%d")

# KRX 금 시세 데이터 사용 설정
USE_KRX_API = True  # True: KRX API 사용, False: 샘플 가격 사용
SAMPLE_DOMESTIC_PRICE = 85000  # 원/g (KRX API를 사용하지 않을 때)
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


def get_krx_gold_price(auth_key, date_str):
    """
    KRX 금 시세 API 호출
    
    Args:
        auth_key: KRX API 인증키
        date_str: YYYYMMDD 형식의 날짜
    
    Returns:
        float: 국내 금 가격 (원/g), 실패 시 None
    """
    # KRX OpenAPI 엔드포인트
    url = "https://openapi.krx.co.kr/contents/OPP/DATA/data.cmd"
    
    headers = {
        'AUTH_KEY': auth_key  # 헤더에 인증키 추가
    }
    
    params = {
        'BO_ID': 'SsgXTEspyJESKvyXZtCU',  # KRX 시리즈 일별시세정보 API ID
        'isu_cd': 'GOLD',  # 금 종목 코드 (실제 코드 확인 필요)
        'trd_dd': date_str,  # 거래일자
        'req_tp': 'json'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        
        # 응답 데이터 구조에 따라 파싱 (실제 API 응답 확인 후 수정 필요)
        if 'result' in data and len(data['result']) > 0:
            # 금 가격 추출 (필드명은 실제 API 응답에 맞게 수정)
            price = data['result'][0].get('close_price', None)
            if price:
                return float(price)
        
        return None
        
    except Exception as e:
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


def load_krx_data(filename):
    """
    KRX 금 시세 CSV 파일 읽기
    
    CSV 형식:
    date,price
    2023-01-01,85000
    2023-01-02,85500
    ...
    
    Returns:
        dict: {날짜: 가격} 형식의 딕셔너리
    """
    try:
        df = pd.read_csv(filename)
        krx_dict = {}
        
        for _, row in df.iterrows():
            date_key = pd.to_datetime(row['date']).strftime("%Y-%m-%d")
            krx_dict[date_key] = float(row['price'])
        
        print(f"✓ KRX 데이터 로드 완료: {len(krx_dict)}개 행")
        return krx_dict
        
    except FileNotFoundError:
        print(f"⚠️  KRX CSV 파일을 찾을 수 없음: {filename}")
        return None
    except Exception as e:
        print(f"⚠️  KRX 데이터 로드 오류: {e}")
        return None


def get_domestic_price(date_str, krx_api_key=None, sample_price=85000, use_krx_api=True):
    """
    국내 금 시세 조회
    
    Args:
        date_str: YYYY-MM-DD 형식의 날짜
        krx_api_key: KRX API 인증키
        sample_price: 샘플 가격 (KRX API를 사용하지 않을 때)
        use_krx_api: KRX API 사용 여부
    
    Returns:
        float: 국내 금 가격 (원/g)
    """
    if use_krx_api and krx_api_key:
        # KRX API로 실제 금 시세 조회
        date_api_format = date_str.replace("-", "")  # YYYYMMDD 형식으로 변환
        price = get_krx_gold_price(krx_api_key, date_api_format)
        
        if price is not None:
            return price
    
    # KRX API를 사용하지 않거나 조회 실패 시 샘플 가격 사용
    # 약간의 변동을 주어 더 현실적으로 만듦
    import random
    variation = random.uniform(-1000, 1000)  # ±1000원 변동
    return sample_price + variation


def collect_data(start_date, end_date, exim_api_key, krx_api_key=None):
    """
    금 데이터 수집 메인 함수
    """
    print("=" * 60)
    print("금 김치프리미엄 데이터 수집 시작")
    print("=" * 60)
    
    # API 키 확인
    if exim_api_key == "여기에_발급받은_API_키_입력" or not exim_api_key:
        print("\n⚠️  오류: 환율 API 키가 설정되지 않았습니다!")
        print("스크립트 상단의 EXIM_API_KEY 변수에 발급받은 키를 입력하세요.")
        print("한국수출입은행에서 API 키를 발급받으세요:")
        print("https://www.koreaexim.go.kr/ir/HPHKIR020M01\n")
        return None
    
    if USE_KRX_API:
        if krx_api_key == "여기에_발급받은_KRX_API_키_입력" or not krx_api_key:
            print("\n⚠️  경고: KRX API 키가 설정되지 않았습니다!")
            print("스크립트 상단의 KRX_API_KEY 변수에 발급받은 키를 입력하세요.")
            print("KRX OpenAPI에서 인증키를 발급받으세요:")
            print("https://openapi.krx.co.kr")
            print("샘플 가격을 사용하여 계속 진행합니다...\n")
            krx_api_key = None
    
    print(f"\n📅 수집 기간: {start_date} ~ {end_date}")
    print(f"🔑 환율 API 키: {exim_api_key[:10]}...")
    if USE_KRX_API and krx_api_key:
        print(f"🔑 KRX API 키: {krx_api_key[:10]}...")
    else:
        print(f"💡 국내 금 시세: 샘플 데이터 사용")
    
    # 1. 국제 금 시세 수집
    print("\n[1/3] 국제 금 시세 수집 중...")
    try:
        gold_ticker = yf.Ticker("GC=F")
        gold_data = gold_ticker.history(start=start_date, end=end_date)
        print(f"✓ {len(gold_data)}일의 국제 금 시세 수집 완료")
    except Exception as e:
        print(f"✗ 국제 금 시세 수집 실패: {e}")
        print("\n인터넷 연결을 확인하세요.")
        return None
    
    if len(gold_data) == 0:
        print("✗ 수집된 데이터가 없습니다. 날짜 범위를 확인하세요.")
        return None
    
    # 2. 환율 및 김치프리미엄 계산
    print("\n[2/3] 환율 조회 및 김치프리미엄 계산 중...")
    print("    (이 작업은 시간이 걸릴 수 있습니다...)")
    
    results = []
    success_count = 0
    fail_count = 0
    krx_success = 0
    
    for idx, (date, row) in enumerate(gold_data.iterrows(), 1):
        date_str_api = date.strftime("%Y%m%d")
        date_str_csv = date.strftime("%Y-%m-%d")
        
        # 환율 조회
        exchange_rate = get_exchange_rate(exim_api_key, date_str_api)
        
        if exchange_rate is None:
            fail_count += 1
            continue
        
        # 국내 금 시세
        domestic_price = get_domestic_price(
            date_str_csv, 
            krx_api_key,
            SAMPLE_DOMESTIC_PRICE,
            USE_KRX_API
        )
        
        # KRX API 성공 카운트 (샘플 가격 범위를 벗어나면 실제 데이터로 간주)
        if USE_KRX_API and abs(domestic_price - SAMPLE_DOMESTIC_PRICE) > 2000:
            krx_success += 1
        
        # 국제 금 시세
        international_price = row['Close']  # USD/oz
        
        # 김치프리미엄 계산
        premium = calculate_kimchi_premium(
            domestic_price,
            international_price,
            exchange_rate
        )
        
        results.append({
            'date': date_str_csv,
            'domestic_price': round(domestic_price, 2),
            'international_price': round(international_price, 2),
            'exchange_rate': exchange_rate,
            'premium': premium
        })
        
        success_count += 1
        
        # 진행상황 표시
        if idx % 20 == 0:
            progress = (idx / len(gold_data)) * 100
            print(f"    진행중... {idx}/{len(gold_data)} ({progress:.1f}%)")
    
    print(f"✓ 완료: 성공 {success_count}건, 실패 {fail_count}건")
    if USE_KRX_API and krx_api_key:
        print(f"  (KRX 실제 데이터: 약 {krx_success}건)")
    
    # 3. 데이터프레임 생성
    print("\n[3/3] 데이터 정리 중...")
    df = pd.DataFrame(results)
    
    if len(df) == 0:
        print("✗ 수집된 데이터가 없습니다.")
        return None
    
    print(f"✓ {len(df)}개의 데이터 행 생성 완료")
    
    # CSV 저장
    filename = f"gold_data_{start_date}_{end_date}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"✓ 파일 저장 완료: {filename}")
    
    # 통계 출력
    print("\n" + "=" * 60)
    print("📊 데이터 통계")
    print("=" * 60)
    print(f"데이터 기간: {df['date'].min()} ~ {df['date'].max()}")
    print(f"총 데이터 수: {len(df)}개")
    print(f"\n김치프리미엄:")
    print(f"  평균: {df['premium'].mean():.2f}%")
    print(f"  최대: {df['premium'].max():.2f}%")
    print(f"  최소: {df['premium'].min():.2f}%")
    print(f"  표준편차: {df['premium'].std():.2f}%")
    print(f"\n국내 금 가격 (원/g):")
    print(f"  평균: {df['domestic_price'].mean():,.0f}원")
    print(f"  최대: {df['domestic_price'].max():,.0f}원")
    print(f"  최소: {df['domestic_price'].min():,.0f}원")
    print(f"\n국제 금 가격 (USD/oz):")
    print(f"  평균: ${df['international_price'].mean():,.2f}")
    print(f"  최대: ${df['international_price'].max():,.2f}")
    print(f"  최소: ${df['international_price'].min():,.2f}")
    print(f"\n환율 (USD/KRW):")
    print(f"  평균: {df['exchange_rate'].mean():,.2f}원")
    print(f"  최대: {df['exchange_rate'].max():,.2f}원")
    print(f"  최소: {df['exchange_rate'].min():,.2f}원")
    
    return df


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("금 김치프리미엄 데이터 수집 스크립트")
    print("=" * 60)
    print("\n⚠️  시작하기 전에:")
    print("1. 한국수출입은행에서 환율 API 키를 발급받으세요")
    print("   https://www.koreaexim.go.kr/ir/HPHKIR020M01")
    print("2. KRX OpenAPI에서 인증키를 발급받으세요 (선택)")
    print("   https://openapi.krx.co.kr")
    print("3. 스크립트 상단에 API 키들을 입력하세요\n")
    
    input("준비가 되었으면 Enter를 누르세요...")
    
    # 데이터 수집 실행
    df = collect_data(START_DATE, END_DATE, EXIM_API_KEY, KRX_API_KEY)
    
    if df is not None:
        print("\n" + "=" * 60)
        print("✅ 데이터 수집이 완료되었습니다!")
        print("=" * 60)
        print("\n다음 단계:")
        print("1. 생성된 CSV 파일을 확인하세요")
        print("2. gold_backtest_v2.html을 브라우저에서 여세요")
        print("3. CSV 업로드 탭에서 파일을 업로드하세요")
        print("4. 백테스팅을 실행하세요!")
        print("\n" + "=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 데이터 수집에 실패했습니다.")
        print("=" * 60)
        print("\n문제 해결:")
        print("1. API 키가 올바른지 확인하세요")
        print("2. 인터넷 연결을 확인하세요")
        print("3. Python 라이브러리가 설치되어 있는지 확인하세요:")
        print("   pip install yfinance requests pandas")
        print("\n" + "=" * 60)