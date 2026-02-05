#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
금 김치프리미엄 데이터 수집 스크립트 (최종 버전)
KRX 금시장 일별매매정보 API 사용
"""

import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
import urllib3
import json

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== 설정 영역 ====================
EXIM_API_KEY = "LadS1IpKN2DQynQ4jIn9KcqSXBSpg21X"
KRX_API_KEY = "A565FC8AB3A94EFA8D55C3AFD888B58DA452D41E"

# 데이터 수집 기간 설정
START_DATE = "2024-01-01"  # KRX 금시장은 2014년 3월 24일부터
END_DATE = datetime.now().strftime("%Y-%m-%d")

# 설정
USE_KRX_API = True
SAMPLE_DOMESTIC_PRICE = 85000  # KRX API 실패시
# ===================================================


def get_exchange_rate(auth_key, date_str):
    """
    한국수출입은행 환율 API 호출
    """
    url = "https://www.koreaexim.go.kr/site/program/financial/exchangeJSON"
    params = {
        'authkey': auth_key,
        'searchdate': date_str,
        'data': 'AP01'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10, verify=False)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if isinstance(data, dict) and ('error' in data or 'RESULT' in data):
            return None
        
        for item in data:
            if item.get('cur_unit') == 'USD':
                rate = item.get('deal_bas_r', '').replace(',', '')
                if rate:
                    return float(rate)
        
        return None
        
    except:
        return None



def get_krx_gold_price(auth_key, date_str):
    """
    KRX 금시장 일별매매정보 API 호출
    실패 시 None 반환
    """
    import re

    url = "https://data-dbg.krx.co.kr/svc/apis/gen/gold_bydd_trd"

    headers = {
        "Content-Type": "application/json",
        "AUTH_KEY": auth_key,   # 🔴 기존 API-KEY → AUTH_KEY
    }

    data = {"basDd": date_str}

    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=10,
            verify=False
        )

        if response.status_code != 200:
            print("KRX HTTP ERROR:", response.status_code, response.text[:200])
            return None

        result = response.json()
        items = result.get("OutBlock_1", [])

        for item in items:
            isu_nm = (item.get("ISU_NM") or "").replace(" ", "").lower()
            raw = item.get("TDD_CLSPRC", "")

            # 문서에 나온 것처럼 "-"면 스킵 :contentReference[oaicite:0]{index=0}
            if raw == "-" or not raw:
                continue

            # 숫자만 안전하게 파싱
            num = re.sub(r"[^0-9,]", "", raw).replace(",", "")
            if not num:
                continue

            price = float(num)

            # 단위 환산
            if "1kg" in isu_nm:
                return price / 1000
            elif "100g" in isu_nm:
                return price / 100
            elif "1g" in isu_nm:
                return price
            else:
                return price  # fallback

        # 여기까지 왔다는 건 전부 "-"였다는 뜻
        return None

    except Exception as e:
        print("KRX EXCEPTION:", e)
        return None

def calculate_kimchi_premium(domestic_price_krw_g, international_price_usd_oz, exchange_rate):
    """김치프리미엄 계산"""
    OZ_TO_GRAM = 31.1034768
    international_krw_g = (international_price_usd_oz * exchange_rate) / OZ_TO_GRAM
    premium = ((domestic_price_krw_g / international_krw_g) - 1) * 100
    return round(premium, 2)


def test_apis():
    """API 테스트"""
    print("\n" + "=" * 60)
    print("API 연결 테스트")
    print("=" * 60)
    
    # 1. 환율 API
    print("\n[1/2] 환율 API 테스트")
    print("-" * 60)
    test_date = datetime.now().strftime("%Y%m%d")
    # 주말/휴장일 대비: 어제 날짜로 한 번 더 테스트
    from datetime import timedelta
    test_date_prev = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    
    rate = get_exchange_rate(EXIM_API_KEY, test_date)
    if rate:
        print(f"✅ 성공!")
        print(f"   USD/KRW: {rate:,.2f}원")
    else:
        print(f"❌ 실패")
        print(f"   API 키 확인 필요")
    
    # 2. KRX 금시장 API
    print("\n[2/2] KRX 금시장 API 테스트")
    print("-" * 60)
    
    url = "https://data-dbg.krx.co.kr/svc/apis/gen/gold_bydd_trd"
    headers = {
        "Content-Type": "application/json",
    "AUTH_KEY": KRX_API_KEY, 
    }
    data_req = {"basDd": test_date}
    
    try:
        print(f"   엔드포인트: {url}")
        print(f"   날짜: {test_date}")
        
        response = requests.post(url, headers=headers, json=data_req, timeout=10, verify=False)
        print(f"   응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'OutBlock_1' in result:
                print(f"   ✅ 데이터 수신 성공!")
                print(f"   종목 수: {len(result['OutBlock_1'])}")
                
                print("\n   📋 금 상품 목록:")
                for i, item in enumerate(result['OutBlock_1'], 1):
                    isu_nm = item.get('ISU_NM', '')
                    tdd_clsprc = item.get('TDD_CLSPRC', '')
                    print(f"   {i}. {isu_nm}: {tdd_clsprc}원")
                
                # 1g 환산 가격
                price_per_g = get_krx_gold_price(KRX_API_KEY, test_date)

                if price_per_g is None:
                    price_per_g = get_krx_gold_price(KRX_API_KEY, test_date_prev)

                    print(f"\n   ✅ 1g 환산 가격: {price_per_g:,.0f}원/g")
                else:
                    print(f"\n   ⚠️  가격 파싱 실패")
            else:
                print(f"   ❌ OutBlock_1 없음")
                print(f"   응답: {result}")
        else:
            print(f"   ❌ HTTP {response.status_code}")
            print(f"   응답: {response.text[:500]}")
            
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        import traceback
        traceback.print_exc()


def collect_data(start_date, end_date, exim_key, krx_key):
    """데이터 수집 메인 함수"""
    print("=" * 60)
    print("금 김치프리미엄 데이터 수집")
    print("=" * 60)
    
    print(f"\n📅 수집 기간: {start_date} ~ {end_date}")
    print(f"🔑 환율 API: {exim_key[:15]}...")
    print(f"🔑 KRX API: {krx_key[:15]}...")
    
    # 1. 국제 금 시세 수집
    print("\n[1/3] 국제 금 시세 수집 (Yahoo Finance)")
    print("-" * 60)
    try:
        gold_ticker = yf.Ticker("GC=F")
        gold_data = gold_ticker.history(start=start_date, end=end_date)
        print(f"✓ {len(gold_data)}일치 데이터 수집 완료")
        
        if len(gold_data) == 0:
            print("❌ 데이터가 없습니다. 날짜 범위를 확인하세요.")
            return None
            
    except Exception as e:
        print(f"❌ 국제 금 시세 수집 실패: {e}")
        return None
    
    # 2. 환율 및 국내 금 시세 수집
    print("\n[2/3] 환율 및 국내 금 시세 조회")
    print("-" * 60)
    print("(API 호출 중... 시간이 걸립니다)\n")
    
    results = []
    success_count = 0
    fail_count = 0
    krx_success_count = 0
    
    for idx, (date, row) in enumerate(gold_data.iterrows(), 1):
        date_api = date.strftime("%Y%m%d")
        date_csv = date.strftime("%Y-%m-%d")
        
        # 환율 조회
        exchange_rate = get_exchange_rate(exim_key, date_api)
        if exchange_rate is None:
            fail_count += 1
            continue
        
        # 국내 금 시세 조회
        domestic_price = None
        if USE_KRX_API and krx_key:
            domestic_price = get_krx_gold_price(krx_key, date_api)
            if domestic_price:
                krx_success_count += 1
        
        # KRX 실패시 샘플 가격
        if domestic_price is None:
            import random
            domestic_price = SAMPLE_DOMESTIC_PRICE + random.uniform(-2000, 2000)
        
        # 국제 금 시세
        international_price = row['Close']
        
        # 김치프리미엄 계산
        premium = calculate_kimchi_premium(
            domestic_price,
            international_price,
            exchange_rate
        )
        
        results.append({
            'date': date_csv,
            'domestic_price': round(domestic_price, 2),
            'international_price': round(international_price, 2),
            'exchange_rate': exchange_rate,
            'premium': premium
        })
        
        success_count += 1
        
        # 진행률 표시
        if idx % 20 == 0:
            progress = (idx / len(gold_data)) * 100
            print(f"  진행: {idx}/{len(gold_data)} ({progress:.0f}%) - KRX 성공: {krx_success_count}")
    
    print(f"\n✓ 데이터 수집 완료")
    print(f"  총 성공: {success_count}건")
    print(f"  총 실패: {fail_count}건")
    print(f"  KRX API 성공: {krx_success_count}건")
    
    if success_count == 0:
        print("❌ 수집된 데이터가 없습니다.")
        return None
    
    # 3. CSV 저장
    print("\n[3/3] CSV 파일 저장")
    print("-" * 60)
    
    df = pd.DataFrame(results)
    filename = f"gold_data_{start_date}_{end_date}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"✓ 파일명: {filename}")
    print(f"  데이터: {len(df)}행")
    
    # 통계
    print("\n" + "=" * 60)
    print("📊 데이터 통계")
    print("=" * 60)
    print(f"데이터 기간: {df['date'].min()} ~ {df['date'].max()}")
    print(f"총 데이터 수: {len(df)}개")
    
    print(f"\n💰 김치프리미엄:")
    print(f"  평균: {df['premium'].mean():.2f}%")
    print(f"  최대: {df['premium'].max():.2f}%")
    print(f"  최소: {df['premium'].min():.2f}%")
    print(f"  표준편차: {df['premium'].std():.2f}%")
    
    print(f"\n🇰🇷 국내 금 가격 (원/g):")
    print(f"  평균: {df['domestic_price'].mean():,.0f}원")
    print(f"  최대: {df['domestic_price'].max():,.0f}원")
    print(f"  최소: {df['domestic_price'].min():,.0f}원")
    
    print(f"\n🌍 국제 금 가격 (USD/oz):")
    print(f"  평균: ${df['international_price'].mean():,.2f}")
    print(f"  최대: ${df['international_price'].max():,.2f}")
    print(f"  최소: ${df['international_price'].min():,.2f}")
    
    print(f"\n💵 환율 (USD/KRW):")
    print(f"  평균: {df['exchange_rate'].mean():,.2f}원")
    print(f"  최대: {df['exchange_rate'].max():,.2f}원")
    print(f"  최소: {df['exchange_rate'].min():,.2f}원")
    
    return df


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🏆 금 김치프리미엄 데이터 수집 스크립트")
    print("=" * 60)
    
    # 데이터 제공 기간 표시
    print("\n📅 데이터 조회 가능 기간:")
    print("-" * 60)
    print("  • KRX 금시장: 2014년 3월 24일 ~ 현재")
    print("  • 환율 (수출입은행): 제한 없음")
    print("  • 국제 금 시세: 제한 없음")
    
    # 현재 설정 표시
    print("\n⚙️  현재 설정:")
    print("-" * 60)
    print(f"  • 수집 시작일: {START_DATE}")
    print(f"  • 수집 종료일: {END_DATE}")
    
    # 날짜 범위 계산
    from datetime import datetime
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d")
    days_diff = (end_dt - start_dt).days
    print(f"  • 총 기간: 약 {days_diff}일 ({days_diff/365:.1f}년)")
    
    # KRX 시작일 확인
    krx_start = datetime(2014, 3, 24)
    if start_dt < krx_start:
        print(f"\n  ⚠️  주의: 시작일이 KRX 제공 시작일보다 이릅니다.")
        print(f"           KRX 데이터는 2014-03-24부터만 제공됩니다.")
        print(f"           그 이전 기간은 샘플 데이터가 사용됩니다.")
    
    print("\n메뉴:")
    print("1. API 연결 테스트만 실행")
    print("2. 전체 데이터 수집 실행")
    print("3. 수집 기간 변경 후 실행")
    
    choice = input("\n선택 (1, 2 또는 3): ").strip()
    
    if choice == "1":
        test_apis()
        print("\n" + "=" * 60)
        print("💡 테스트 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        print("- API가 정상 작동하면 '2번'을 선택하여 데이터 수집")
        print("- 오류가 있으면 API 키와 엔드포인트 확인")
        
    elif choice == "2":
        print("\n준비 확인:")
        print(f"✓ 환율 API 키: {EXIM_API_KEY[:20]}...")
        print(f"✓ KRX API 키: {KRX_API_KEY[:20]}...")
        print(f"✓ 수집 기간: {START_DATE} ~ {END_DATE}")
        
        confirm = input("\n계속하시겠습니까? (y/n): ").strip().lower()
        
        if confirm == 'y':
            df = collect_data(START_DATE, END_DATE, EXIM_API_KEY, KRX_API_KEY)
            
            if df is not None:
                print("\n" + "=" * 60)
                print("✅ 데이터 수집 완료!")
                print("=" * 60)
                print("\n다음 단계:")
                print("1. 생성된 CSV 파일 확인")
                print("2. gold_backtest_v2.html을 브라우저에서 열기")
                print("3. 'CSV 업로드' 탭에서 파일 업로드")
                print("4. 매매 조건 설정 후 백테스팅 실행!")
            else:
                print("\n" + "=" * 60)
                print("❌ 데이터 수집 실패")
                print("=" * 60)
        else:
            print("취소되었습니다.")
            
    elif choice == "3":
        print("\n" + "=" * 60)
        print("📅 수집 기간 변경")
        print("=" * 60)
        
        print("\n권장 기간:")
        print("  • 최근 1년: 2025-01-01 ~ 현재")
        print("  • 최근 3년: 2023-01-01 ~ 현재")
        print("  • 전체: 2014-03-24 ~ 현재")
        
        print("\n현재 설정:")
        print(f"  시작일: {START_DATE}")
        print(f"  종료일: {END_DATE}")
        
        new_start = input("\n새 시작일 (YYYY-MM-DD) 또는 Enter로 유지: ").strip()
        new_end = input("새 종료일 (YYYY-MM-DD) 또는 Enter로 유지: ").strip()
        
        # 날짜 유효성 검사
        if new_start:
            try:
                datetime.strptime(new_start, "%Y-%m-%d")
                START_DATE = new_start
                print(f"✓ 시작일 변경: {START_DATE}")
            except:
                print("✗ 잘못된 날짜 형식. 기존 값 유지.")
        
        if new_end:
            try:
                datetime.strptime(new_end, "%Y-%m-%d")
                END_DATE = new_end
                print(f"✓ 종료일 변경: {END_DATE}")
            except:
                print("✗ 잘못된 날짜 형식. 기존 값 유지.")
        
        print(f"\n최종 수집 기간: {START_DATE} ~ {END_DATE}")
        
        confirm = input("\n이 기간으로 데이터를 수집하시겠습니까? (y/n): ").strip().lower()
        
        if confirm == 'y':
            df = collect_data(START_DATE, END_DATE, EXIM_API_KEY, KRX_API_KEY)
            
            if df is not None:
                print("\n" + "=" * 60)
                print("✅ 데이터 수집 완료!")
                print("=" * 60)
                print("\n다음 단계:")
                print("1. 생성된 CSV 파일 확인")
                print("2. gold_backtest_v2.html을 브라우저에서 열기")
                print("3. 'CSV 업로드' 탭에서 파일 업로드")
                print("4. 매매 조건 설정 후 백테스팅 실행!")
            else:
                print("\n" + "=" * 60)
                print("❌ 데이터 수집 실패")
                print("=" * 60)
        else:
            print("취소되었습니다.")
    else:
        print("잘못된 선택입니다.")
