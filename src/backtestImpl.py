import math
from datetime import date

import requests
from bs4 import BeautifulSoup
from pykrx import stock
from dateutil.relativedelta import relativedelta

import logging.config
import json

import pandas as pd

import plotly.graph_objects as go
import plotly.subplots as ms

with open('../config/logger.json') as f:
    config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger('logger-1')


def find_maxvol_mon(window, args):
    """

        최대 거래량 찾기

    :param window: 윈도우 클래스
    :param args: dict = {base_date, search_duration, max_vol_occur, lowest_duration, lowest_contrast, per_rate,
    dept_rate, margin_rate}
    :return: max_tick
    """
    try:
        today = date.today()
        # 종목 찾기 시작 날짜
        search_start_date = args['base_date'] - relativedelta(months=int(args['search_duration']))

        # 6개월 이전에 종목 상장 여부 확인
        six_mon_ago = args['base_date'] - relativedelta(months=6)
        kospi_six_ago = stock.get_market_ticker_list(date=six_mon_ago, market="KOSPI")
        kosdaq_six_ago = stock.get_market_ticker_list(date=six_mon_ago, market="KOSDAQ")
        total_six_list = kospi_six_ago + kosdaq_six_ago

        # 최저가 시작 날짜
        start_low_dur = args['base_date'] - relativedelta(months=args['lowest_duration'])

        # 최대 거래 발생 시작일
        max_vol_within_date = (args['base_date'] - relativedelta(months=int(args['max_vol_within'])))

        logger.info(f"기준 일자 : {args['base_date']} 종목 찾기 시작 날짜 : {search_start_date}, "
                    f"기준일 6개월 전 날짜 : {six_mon_ago}, 최저가 시작 날짜 : {start_low_dur}, "
                    f"최대 거래 발생 시작일 : {max_vol_within_date}")

        # 전종목 조회하기
        kospi_market = stock.get_market_ticker_list(date=args['base_date'], market="KOSPI")
        kosdaq_market = stock.get_market_ticker_list(date=args['base_date'], market="KOSDAQ")
        total_market = kospi_market + kosdaq_market
        # total_market = ['377190']
        halt_list = trading_halt_list()
        mg_list = management_list()
        max_vol_code = []
        i = 0
    except Exception as e:
        logger.error(e)
    pre_progress_count = 0
    for code in total_market:
        try:
            i += 1
            total_count = len(total_market)
            progress_count = math.trunc(i / total_count * 100)
            logger.debug(f'======== total count : {len(total_market)}, count : {i}, '
                         f'progress : {progress_count} =======')
            if pre_progress_count < progress_count:
                pre_progress_count = progress_count
                window.progressBar.setValue(pre_progress_count)

            logger.info('[%s] ------ 시세 조회 ------ ', code)
            # 종목별 시세 조회
            df = stock.get_market_ohlcv(search_start_date.strftime("%Y%m%d"), args['base_date'].strftime("%Y%m%d"), code)
            # df = df.resample('M').last()  # 월로 변경

            logger.debug('******** 전체 dataframe **********')
            logger.debug(df)

            logger.debug(f'기준일 6개월 이전의 상장 종목 {total_six_list}')
            if df.empty or (code not in total_six_list):
                logger.info(f"[{code}] - 기준일 대비 6개월 이내에 상장(신규) - PASS")
                continue
            base_day_price = int(df['종가'].iloc[-1])
            # max_price_mon = df['종가'].idxmax().strftime("%Y%m")

            # "500 원 이하, 최고 종가 월 == 기준월", 6개월안에 상장된 신생 종목은 PASS
            if base_day_price < 700 or (stock.get_market_ticker_name(code) in halt_list) \
                    or (stock.get_market_ticker_name(code) in mg_list):
                logger.info(f"[{code}], 가격 {base_day_price} , 관리 , 거래정지 - PASS")
                continue

            # 최대거래 날짜, 가격
            max_vol_date = df['거래량'].idxmax()
            max_vol_price = df.loc[max_vol_date]['종가']

            subset_df = df.iloc[df.index.get_loc(start_low_dur.strftime("%Y%m%d")):]
            logger.debug('================== 최저가 기간의 dataframe =====================')
            logger.debug(subset_df)
            lowest_price_day = subset_df['종가'].idxmin()  # 최저가 날짜
            lowest_price = subset_df.loc[lowest_price_day]['종가']  # 최저가 가격

            subset_df_avg = subset_df['종가'].mean()
            logger.info(f'[{code}] ++ 주가 ++ ')
            logger.info(f'[{code}] - 최대 거래 날짜 {max_vol_date}, 최대 거래 가격 {max_vol_price}')
            logger.info(f'[{code}] - 최저가 날짜 {lowest_price_day}, 최저가 가격 {lowest_price},'
                         f' 최저가 기간 평균 가격 {subset_df_avg}')

        except Exception as e:
            logger.error(e)

        logger.info('[%s] ------ 재무정보 조회 ------ ', code)
        annual_df = naver_financial_data(code)

        # 재무정보 없는거 일단 거르자, '리츠' 이런 종목 인거 같음
        if annual_df.empty:
            continue

        try:
            PER평균 = annual_df.loc['PER(배)'].iloc[:-1].astype(float).mean()
            부채비율 = annual_df.loc['부채비율'].iloc[:-1].astype(float).mean()
            영업이익률 = annual_df.loc['영업이익률'].iloc[:-1].astype(float).mean()
        except ValueError as ve:
            logger.error('[%s] - %s', code, ve)
            continue

        logger.info(f'[{code}] ++ 성장성 ++ ')

        logger.info(f'PER 평균: {math.trunc(PER평균)}%, 부채비율 평균: {math.trunc(부채비율)}%, '
                    f'영업이익률 평균: {math.trunc(영업이익률)}%')
        # logger.debug(float(args['lowest_contrast']))
        # logger.debug(lowest_price * float(args['lowest_contrast']))
        # logger.debug('type 확인 max_vol_occur_date:%s, max_vol_date:%s, today:%s',type(max_vol_occur_date),
        #              type(max_vol_date),type(today))
        # 최대 거래 월이 현재로부터 N 개월 안에 터졌다면 종목 추가
        if max_vol_within_date <= max_vol_date.date() <= args['base_date'] and \
                lowest_price * float(args['lowest_contrast']) >= subset_df_avg and \
                PER평균 < int(args['per_rate']) and 부채비율 < int(args['dept_rate']) and \
                영업이익률 >= int(args['margin_rate']):
            max_vol_code.append({'종목번호': str(code), '종목명': stock.get_market_ticker_name(code),
                                 '재무정보': f'https://finance.naver.com/item/main.nhn?code={code}',
                                 '뉴스': f'https://finance.naver.com/item/news_news.nhn?code={code}'})
            logger.info('[%s] - %s년 역대 거래량, 최저가 대비 %s배 이하, %s', code, args['search_duration'],
                        args['lowest_contrast'], stock.get_market_ticker_name(code))
    # except Exception as e:
    #     logger.error('[%s] - %s', code, e)

    logger.info('======== 최대 거래량 종목 ==========')
    logger.info(max_vol_code)
    return max_vol_code


def naver_financial_data(code):
    url = f"https://finance.naver.com/item/main.nhn?code={code}"
    res = requests.get(url)
    try:
        financial_stmt = pd.read_html(res.text)[3]
    except Exception as e:
        logger.error('[%s] - %s', code, e)
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


def trading_halt_list():
    baseaddress = 'https://finance.naver.com/sise/trading_halt.naver'

    stoplist = []
    res = requests.get(baseaddress)
    soup = BeautifulSoup(res.content.decode('euc-kr', 'replace'), 'html.parser')
    lists = soup.select('div.box_type_l table tr')

    for item in lists:
        if len(item) == 9 and item.text.split('\n')[2] != '종목명':
            stoplist.append(item.text.split('\n')[2])

    return stoplist


def management_list():
    baseaddress = 'https://finance.naver.com/sise/management.nhn'
    stoplist = []
    res = requests.get(baseaddress)
    soup = BeautifulSoup(res.content.decode('euc-kr', 'replace'), 'html.parser')

    items = soup.select('div.box_type_l table tr')
    for item in items:
        if len(item) == 17 and item.text.split('\n')[2] != '종목명':
            stoplist.append(item.text.split('\n')[2])

    return stoplist


def make_chart(args, code):
    """
        차트 그리기
    :param args: input list
    :param code: 종목 번호
    :return: 차트 결과값 반환환
    """

    KOSPI = "1001"
    KOSDAQ = "2001"

    today = date.today()
    pre_date = today - relativedelta(months=args['search_duration'])

    # 차트 그리기 위한 시세조회
    if code == KOSPI or code == KOSDAQ:
        df = stock.get_index_ohlcv(pre_date.strftime("%Y%m%d"), args['base_date'].strftime("%Y%m%d"), code)
        tick_name = stock.get_index_ticker_name(code)
    else:
        df = stock.get_market_ohlcv(pre_date.strftime("%Y%m%d"), args['base_date'].strftime("%Y%m%d"), code)
        tick_name = stock.get_market_ticker_name(code)
    df = df.astype(int)

    # 캔들 차트 객체 생성
    candle = go.Candlestick(
        x=df.index,
        open=df['시가'],
        high=df['고가'],
        low=df['저가'],
        close=df['종가'],
        increasing_line_color='red',  # 상승봉 스타일링
        decreasing_line_color='blue'  # 하락봉 스타일링
    )

    # 바 차트(거래량) 객체 생성
    volume_bar = go.Bar(x=df.index, y=df['거래량'])

    fig = ms.make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02)

    fig.add_trace(candle, row=1, col=1)
    fig.add_trace(volume_bar, row=2, col=1)

    fig.update_layout(
        title=tick_name,
        yaxis1_title='가격',
        yaxis2_title='거래량',
        xaxis2_title='기간',
        xaxis1_rangeslider_visible=False,
        xaxis2_rangeslider_visible=True,
    )
    fig.show()
