#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
금 김치프리미엄 데이터 수집 스크립트 (디버깅 버전)
"""

import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
import traceback

# ==================== 설정 영역 ====================
EXIM_API_KEY = "LadS1IpKN2DQynQ4jIn9KcqSXBSpg21X"
KRX_API_KEY = "A565FC8AB3A94EFA8D55C3AFD888B58DA452D41E"

# 테스트용으로 짧은 기간만
START_DATE = "2024-01-01"
END_DATE = "2024-01-10"

USE_KRX_API = True
SAMPLE_DOMESTIC_PRICE = 85000
# ===================================================

DEBUG = True  # 디버깅 모드


def debug_print(message):
    """디버깅 메시지 출력"""
    if DEBUG:
        print(f"[DEBUG] {message}")


def get_exchange_rate(auth_key, date_str):
    """환율 API 호출"""
    url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
    params = {
        'authkey': auth_key,
        'searchdate': date_str,
        'data': 'AP01'
    }
    
    try:
        debug_print(f"환율 API 호출: {date_str}")
        response = requests.get(url, params=params, timeout=10)
        debug_print(f"환율 API 응답 코드: {response.status_code}")
        
        if response.status_code != 200:
            debug_print(f"환율 API 실패: HTTP {response.status_code}")
            debug_print(f"응답 내용: {response.text[:200]}")
            return None
        
        try:
            data = response.json()
            debug_print(f"환율 API JSON 파싱 성공, 데이터 타입: {type(data)}")
            
            if isinstance(data, dict):
                debug_print(f"응답이 딕셔너리: {list(data.keys())}")
                if 'error' in data:
                    debug_print(f"API 에러 응답: {data['error']}")
                    return None
            elif isinstance(data, list):
                debug_print(f"응답이 리스트, 길이: {len(data)}")
        except Exception as e:
            debug_print(f"JSON 파싱 실패: {e}")
            debug_print(f"응답 내용: {response.text[:500]}")
            return None
        
        # USD 환율 찾기
        for item in data:
            if item.get('cur_unit') == 'USD':
                rate = item.get('deal_bas_r', '').replace(',', '')
                debug_print(f"USD 환율 찾음: {rate}")
                return float(rate) if rate else None
        
        debug_print("USD 환율을 찾을 수 없음")
        return None
        
    except Exception as e:
        debug_print(f"환율 조회 예외: {e}")
        traceback.print_exc()
        return None


def get_krx_gold_price(auth_key, date_str):
    """KRX 금 시세 API 호출"""
    # KRX API 엔드포인트 (실제 엔드포인트 확인 필요)
    url = "https://openapi.krx.co.kr/contents/OPP/DATA/data.cmd"
    
    headers = {
        'AUTH_KEY': auth_key
    }
    
    params = {
        'BO_ID': 'SsgXTEspyJESKvyXZtCU',
        'isu_cd': 'GOLD',
        'trd_dd': date_str,
        'req_tp': 'json'
    }
    
    try:
        debug_print(f"KRX API 호출: {date_str}")
        debug_print(f"URL: {url}")
        debug_print(f"Headers: AUTH_KEY={auth_key[:20]}...")
        debug_print(f"Params: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        debug_print(f"KRX API 응답 코드: {response.status_code}")
        debug_print(f"KRX API 응답 헤더: {dict(response.headers)}")
        debug_print(f"KRX API 응답 내용 (처음 500자): {response.text[:500]}")
        
        if response.status_code != 200:
            return None
        
        try:
            data = response.json()
            debug_print(f"KRX API JSON 파싱 성공")
            debug_print(f"데이터 구조: {type(data)}, 키: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            
            # 실제 데이터 구조 출력
            debug_print(f"전체 응답: {data}")
            
        except:
            debug_print("KRX API JSON 파싱 실패")
        
        return None
        
    except Exception as e:
        debug_print(f"KRX 조회 예외: {e}")
        traceback.print_exc()
        return None


def get_domestic_price(date_str, krx_api_key=None, sample_price=85000, use_krx_api=True):
    """국내 금 시세 조회"""
    if use_krx_api and krx_api_key:
        date_api_format = date_str.replace("-", "")
        price = get_krx_gold_price(krx_api_key, date_api_format)
        
        if price is not None:
            debug_print(f"KRX API에서 가격 조회 성공: {price}")
            return price
        else:
            debug_print("KRX API 실패, 샘플 가격 사용")
    
    # 샘플 가격 사용
    import random
    variation = random.uniform(-1000, 1000)
    final_price = sample_price + variation
    debug_print(f"샘플 가격 사용: {final_price:.2f}")
    return final_price


def test_apis():
    """API 테스트 함수"""
    print("\n" + "=" * 60)
    print("API 테스트 시작")
    print("=" * 60)
    
    # 1. 환율 API 테스트
    print("\n[1/2] 환율 API 테스트")
    print("-" * 60)
    test_date = datetime.now().strftime("%Y%m%d")
    print(f"테스트 날짜: {test_date}")
    
    rate = get_exchange_rate(EXIM_API_KEY, test_date)
    if rate:
        print(f"✅ 환율 API 성공: {rate}원")
    else:
        print(f"❌ 환율 API 실패")
        print(f"API 키 확인: {EXIM_API_KEY[:20]}...")
    
    # 2. KRX API 테스트
    print("\n[2/2] KRX API 테스트")
    print("-" * 60)
    test_date = datetime.now().strftime("%Y%m%d")
    print(f"테스트 날짜: {test_date}")
    
    price = get_krx_gold_price(KRX_API_KEY, test_date)
    if price:
        print(f"✅ KRX API 성공: {price}원/g")
    else:
        print(f"❌ KRX API 실패")
        print(f"API 키 확인: {KRX_API_KEY[:20]}...")
        print("\n⚠️  참고: KRX는 공개 API가 제한적일 수 있습니다.")
        print("실제 API 문서를 확인하여 정확한 엔드포인트와 파라미터를 사용하세요.")


def collect_data_test():
    """데이터 수집 테스트 (소량)"""
    print("\n" + "=" * 60)
    print("데이터 수집 테스트 (2024-01-01 ~ 2024-01-10)")
    print("=" * 60)
    
    # 1. 국제 금 시세
    print("\n[1/3] 국제 금 시세 수집")
    try:
        debug_print("yfinance 초기화")
        gold_ticker = yf.Ticker("GC=F")
        
        debug_print(f"데이터 요청: {START_DATE} ~ {END_DATE}")
        gold_data = gold_ticker.history(start=START_DATE, end=END_DATE)
        
        print(f"✓ 수집 완료: {len(gold_data)}일")
        debug_print(f"첫 5개 행:\n{gold_data.head()}")
        
        if len(gold_data) == 0:
            print("❌ 국제 금 시세 데이터가 없습니다")
            return None
            
    except Exception as e:
        print(f"❌ 국제 금 시세 수집 실패: {e}")
        traceback.print_exc()
        return None
    
    # 2. 환율 및 국내 금 시세
    print("\n[2/3] 환율 및 국내 금 시세 조회")
    print("-" * 60)
    
    results = []
    success_count = 0
    fail_count = 0
    
    for idx, (date, row) in enumerate(gold_data.iterrows(), 1):
        date_str_api = date.strftime("%Y%m%d")
        date_str_csv = date.strftime("%Y-%m-%d")
        
        print(f"\n날짜 {idx}/{len(gold_data)}: {date_str_csv}")
        
        # 환율
        exchange_rate = get_exchange_rate(EXIM_API_KEY, date_str_api)
        if exchange_rate is None:
            print(f"  ✗ 환율 조회 실패")
            fail_count += 1
            continue
        else:
            print(f"  ✓ 환율: {exchange_rate}원")
        
        # 국내 금 시세
        domestic_price = get_domestic_price(
            date_str_csv,
            KRX_API_KEY,
            SAMPLE_DOMESTIC_PRICE,
            USE_KRX_API
        )
        print(f"  ✓ 국내 금: {domestic_price:.2f}원/g")
        
        # 국제 금 시세
        international_price = row['Close']
        print(f"  ✓ 국제 금: ${international_price:.2f}/oz")
        
        # 김치프리미엄
        premium = calculate_kimchi_premium(domestic_price, international_price, exchange_rate)
        print(f"  ✓ 김치프리미엄: {premium}%")
        
        results.append({
            'date': date_str_csv,
            'domestic_price': round(domestic_price, 2),
            'international_price': round(international_price, 2),
            'exchange_rate': exchange_rate,
            'premium': premium
        })
        
        success_count += 1
    
    print(f"\n✓ 데이터 수집 완료: 성공 {success_count}건, 실패 {fail_count}건")
    
    if success_count == 0:
        print("❌ 수집된 데이터가 없습니다")
        return None
    
    # 3. CSV 저장
    print("\n[3/3] CSV 저장")
    df = pd.DataFrame(results)
    filename = f"gold_data_test_{START_DATE}_{END_DATE}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"✓ 파일 저장: {filename}")
    
    # 통계
    print("\n" + "=" * 60)
    print("📊 통계")
    print("=" * 60)
    print(f"평균 김치프리미엄: {df['premium'].mean():.2f}%")
    print(f"평균 환율: {df['exchange_rate'].mean():,.2f}원")
    
    return df


def calculate_kimchi_premium(domestic_price_krw_g, international_price_usd_oz, exchange_rate):
    """김치프리미엄 계산"""
    OZ_TO_GRAM = 31.1034768
    international_krw_g = (international_price_usd_oz * exchange_rate) / OZ_TO_GRAM
    premium = ((domestic_price_krw_g / international_krw_g) - 1) * 100
    return round(premium, 2)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("금 김치프리미엄 데이터 수집 - 디버깅 버전")
    print("=" * 60)
    
    print("\n선택하세요:")
    print("1. API 테스트만 실행")
    print("2. 데이터 수집 테스트 (10일치)")
    
    choice = input("\n선택 (1 또는 2): ").strip()
    
    if choice == "1":
        test_apis()
    elif choice == "2":
        collect_data_test()
    else:
        print("잘못된 선택입니다.")
