from pykrx import stock
from dateutil.relativedelta import relativedelta

import logging.config
import json

# json load
config = json.load(open('../config/logger.json'))
logging.config.dictConfig(config)
logger = logging.getLogger(__name__)


def find_maxvol_mon(predate, base_day, ticker):
    """
        최대 거래량 찾기 (월)

    :param predate: 시작년도
    :param base_day: 기준일자
    :param ticker: 종목
    :return: max_tick
    """

    max_tick = []

    # 종목별 시세 조회,  # 종가 1000 이하
    df = stock.get_market_ohlcv(predate.strftime("%Y%m%d"), base_day.strftime("%Y%m%d"), ticker)

    if df.empty:
        return

    df = df.resample('M').last()

    base_day_price = int(df['종가'].iloc[-1])
    max_mon_price = df['종가'].idxmax().strftime("%Y%m")

    # 6개월 이전에 종목 상장 여부 확인
    pre_day = base_day - relativedelta(months=7)
    i_tick = stock.get_market_ticker_list(date=pre_day, market="KOSPI")
    q_tick = stock.get_market_ticker_list(date=pre_day, market="KOSDAQ")
    tick_list = i_tick + q_tick

    # "500 원 이하, 최고 종가 월 == 기준월", 6개월안에 상장된 신생 종목은 PASS
    if df.empty or base_day_price < 500 or max_mon_price == base_day.strftime("%Y%m") or (ticker not in tick_list):
        # logger.debug(f"PASS 종목 {ticker}, 기준일 {base_day.strftime('%Y%m%d')}, 가격 {base_day_price}, "
        #              f"최고가 월 {max_mon_price}")
        return

    # 최대거래 월 날짜
    maxidx = df['거래량'].idxmax()
    maxvol_price = df.loc[maxidx]['종가']

    subset_df = df.iloc[-(int(n_lowest) * 13):]
    lowest_price_day = subset_df['종가'].idxmin()
    lowest_price = subset_df.loc[lowest_price_day]['종가']

    # 날짜 비교를 위해 년월까지
    # maxidx = datetime.strftime(maxidx, "%Y%m")
    # std = datetime.strftime(base_day, "%Y%m")

    annual_df = naver_financial_data(ticker)
    logger.debug(f'ticker:{ticker}')
    logger.debug(annual_df.loc['PER(배)'].iloc[:-1])

    PER평균 = annual_df.loc['PER(배)'].iloc[:-1].astype(float).mean()
    부채비율 = annual_df.loc['부채비율'].iloc[:-1].astype(float).mean()
    영업이익률 = annual_df.loc['영업이익률'].iloc[:-1].astype(float).mean()
    logger.debug(f'base_day: {base_day}, n_month:{n_month}, maxidx:{maxidx}, lowest_price:{lowest_price}, maxvol_price:'
                 f'{maxvol_price}, n_mag:{n_mag}, PER평균: {PER평균}, 부채비율:{부채비율}, 영업이익률:{영업이익률}')
    # 최대 거래 월이 현재로부터 N 개월 안에 터졌다면 종목 추가
    if (base_day - relativedelta(months=int(n_month) + 1)) <= maxidx <= base_day and lowest_price <= maxvol_price <= \
            lowest_price * float(n_mag) and PER평균 < int(input_per) and 부채비율 < int(input_dept) and 영업이익률 \
            >= int(input_margin):
        max_tick.append(ticker)
        logger.info(f'{datetime.strftime(maxidx, "%Y%m")} 역대 거래량 ({n_year}년), ({n_month})개월 이내 '
                    f'{get_market_ticker_name(ticker)}')

    return max_tick
