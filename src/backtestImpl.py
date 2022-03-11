from datetime import date

import requests
from pykrx import stock
from dateutil.relativedelta import relativedelta

import logging.config
import json

import pandas as pd

with open('../config/logger.json') as f:
    config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger('logger-1')


def find_maxvol_mon(args):
    """

        최대 거래량 찾기 (월)

    :param args: dict = {max_vol_duration, max_vol_occur, lowest_duration, lowest_contrast, per_rate,
    dept_rate, margin_rate}
    :return: max_tick
    """
    today = date.today()
    search_start_date = today - relativedelta(years=int(args['max_vol_duration']))

    # 전종목 조회하기
    kospi_market = stock.get_market_ticker_list(date=today, market="KOSPI")
    kosdaq_market = stock.get_market_ticker_list(date=today, market="KOSDAQ")
    total_market = kospi_market + kosdaq_market

    max_vol_code = []

    for code in total_market:
        logger.info('[%s] - 시세 조회', code)
        # 종목별 시세 조회
        df = stock.get_market_ohlcv(search_start_date.strftime("%Y%m%d"), today.strftime("%Y%m%d"), code)
        df = df.resample('M').last()  # 월로 변경

        base_day_price = int(df['종가'].iloc[-1])
        max_price_mon = df['종가'].idxmax().strftime("%Y%m")

        # 6개월 이전에 종목 상장 여부 확인
        six_mon_ago = today - relativedelta(months=6)
        kospi_six_ago = stock.get_market_ticker_list(date=six_mon_ago, market="KOSPI")
        kosdaq_six_ago = stock.get_market_ticker_list(date=six_mon_ago, market="KOSDAQ")
        total_six_list = kospi_six_ago + kosdaq_six_ago

        # "500 원 이하, 최고 종가 월 == 기준월", 6개월안에 상장된 신생 종목은 PASS
        if df.empty or base_day_price < 500 or max_price_mon == today.strftime("%Y%m") or (code not in total_six_list):
            logger.debug(f"[{code}], 가격 {base_day_price}, 최고가 {max_price_mon}월 - PASS")
            continue

        # 최대거래 월 날짜, 가격
        max_vol_date = df['거래량'].idxmax()
        max_vol_price = df.loc[max_vol_date]['종가']

        subset_df = df.iloc[-(int(args['lowest_duration']) * 13):]
        lowest_price_day = subset_df['종가'].idxmin()
        lowest_price = subset_df.loc[lowest_price_day]['종가']

        logger.info('[%s] - 재무정보 조회', code)
        annual_df = naver_financial_data(code)

        # 재무정보 없는거 일단 거르자, '리츠' 이런 종목 인거 같음
        if annual_df.empty:
            continue

        PER평균 = annual_df.loc['PER(배)'].iloc[:-1].astype(float).mean()
        부채비율 = annual_df.loc['부채비율'].iloc[:-1].astype(float).mean()
        영업이익률 = annual_df.loc['영업이익률'].iloc[:-1].astype(float).mean()

        logger.debug('[{0}] 최대 거래량 날짜: {1}, 최저가: {2}원, 최대 거래량 가격: {3}원, 최저가 대비: {4}배, PER평균: {5}%, '
                     '부채비율: {6}%, 영업이익률: {7}%'.format(code, max_vol_date.strftime("%Y%m%d"), lowest_price,
                                                      max_vol_price, args['lowest_contrast'], args['per_rate'],
                                                      args['dept_rate'], args['margin_rate']))
        max_vol_occur_date = (today - relativedelta(months=int(args['max_vol_occur']) + 1))
        # logger.debug('type 확인 max_vol_occur_date:%s, max_vol_date:%s, today:%s',type(max_vol_occur_date),
        #              type(max_vol_date),type(today))
        # 최대 거래 월이 현재로부터 N 개월 안에 터졌다면 종목 추가
        if max_vol_occur_date <= max_vol_date.date() <= today and \
                lowest_price <= max_vol_price <= lowest_price * float(args['lowest_contrast']) and \
                PER평균 < int(args['per_rate']) and 부채비율 < int(args['dept_rate']) and \
                영업이익률 >= int(args['margin_rate']):
            max_vol_code.append({'종목번호': code,'종목명': stock.get_market_ticker_name(code)})
            logger.info('%s년 역대 거래량, %s개월 이내 %s', args['max_vol_duration'],args['max_vol_occur'],
                        stock.get_market_ticker_name(code))

    logger.debug(max_vol_code)
    return max_vol_code


def naver_financial_data(code):
    url = f"https://finance.naver.com/item/main.nhn?code={code}"
    res = requests.get(url)
    try:
        financial_stmt = pd.read_html(res.text)[3]
    except Exception as e:
        logger.error(e)
        return pd.DataFrame()

    if ('주요재무정보', '주요재무정보', '주요재무정보') in financial_stmt.columns:
        financial_stmt.set_index(('주요재무정보', '주요재무정보', '주요재무정보'), inplace=True)
        financial_stmt.index.rename('주요재무정보', inplace=True)
        financial_stmt.columns = financial_stmt.columns.droplevel(2)
        annual_date = pd.DataFrame(financial_stmt).xs('최근 연간 실적', axis=1)
        # logger.debug(annual_date)
        return annual_date
    else:
        return pd.DataFrame()

    # "500 원 이하, 최고 종가 월 == 기준월", 6개월안에 상장된 신생 종목은 PASS
    # if df.empty or base_day_price < 500 or max_mon_price == base_day.strftime("%Y%m") or (ticker not in tick_list):
    # logger.debug(f"PASS 종목 {ticker}, 기준일 {base_day.strftime('%Y%m%d')}, 가격 {base_day_price}, "
    #              f"최고가 월 {max_mon_price}")
    # return

    # 날짜 비교를 위해 년월까지
    # maxidx = datetime.strftime(maxidx, "%Y%m")
    # std = datetime.strftime(base_day, "%Y%m")
