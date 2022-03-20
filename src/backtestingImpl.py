import json
import logging.config
import math
from datetime import datetime, date

import holidays
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as ms
import requests
from PyQt5.QtWidgets import QTableWidgetItem
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from pykrx import stock

with open('../config/logger.json') as f:
    config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger('logger-1')


def backtest(window, args):
    """
        백테스트
    :param window: 윈도우 폼
    :param args: 입력값
    :return:
    """

    # 변수 정의
    buy_count = 0
    매입가 = 0
    수익률 = 0
    보유수량 = 0
    현재가 = 0
    매입금액 = 0
    # 평가금액 = ""
    실현손익 = 0
    실현수익률 = 0
    초기금 = int(args['초기금']) * 1000000
    추가금 = int(args['추가금']) * 100000

    today = date.today()
    code = window.code_hidden_label.text()
    max_list = window.max_list
    max_df = pd.DataFrame(max_list)
    max_df = max_df.loc[max_df['종목 번호'] == code]
    logger.debug("-------- 백테스트 종목 --------")
    logger.debug(max_df)

    # 기준일자 가져오기
    base_date = window.btest_sdate_label.text()
    # 한국 공휴일 가져오기
    kr_holidays = holidays.KR()

    logger.debug(f' -- 백테스트 기준일자 {base_date}')

    # 종목 시세표 가져오기
    df = stock.get_market_ohlcv(base_date, today.strftime("%Y%m%d"), code)
    if df.empty:
        raise Exception("백테스팅은 이전 기준일로 찾아진 종목으로 수행!!")

    logger.debug("-------- 백테스트 ticker --------")
    logger.debug(df)

    logger.info(f" ** 조건 확인 - 초기금액 {초기금:,}원, "
                f"추가 주기 {window.add_interval_box.itemText(args['추가 주기'])}, "
                f"매수 조건 {window.buy_cond_box.itemText(args['매수 조건'])}, "
                f"매도 조건 {window.sell_cond_box.itemText(args['매도 조건'])}, "
                f"최대 거래량 날짜 {max_df.iloc[0]['최대 거래 날짜']}, "
                f"최대 거래량 시가 {max_df.iloc[0]['최대 거래량 시가']}, "
                f"최대 거래량 종가 {max_df.iloc[0]['최대 거래량 종가']}")

    max_sprice = max_df.iloc[0]['최대 거래량 시가']
    max_eprice = max_df.iloc[0]['최대 거래량 종가']
    comp_date = ""

    for day in pd.bdate_range(datetime.strptime(base_date, "%Y%m%d"), today):
        # logger.debug(f' ** day {day}')
        if day not in kr_holidays:
            try:
                현재가 = df.loc[day]['종가']
            except Exception as e:
                # holiday 로 안걸러 주는 공휴일은 try 로 패스하자
                logger.error(e)
                continue

            logger.debug(f"[{code}] 매도 조건 확인 - 현재날짜 {day.strftime('%Y년%m월%d일')}, 현재가 {현재가:,}원, "
                         f"최대 거래량 종가 {max_df.iloc[0]['최대 거래량 종가']:,}원, "
                         f"최대 거래량 {max_df.iloc[0]['최대 거래량']}, "
                         f"현재 거래량 {df.loc[day]['거래량']}, ")
            # 첫 매수
            if buy_count == 0:
                comp_date = day
                buy_count += 1
                보유수량 = math.trunc(초기금 / 현재가)
                매입가 = 현재가
                매입금액 = 보유수량 * 매입가
                logger.info(f'[{code}] 첫 매수 - 매수일 {day.strftime("%Y%m%d")} 매수량 {보유수량}, 매입가 {매입가}, 매입 금액 {매입금액}')
            elif args['추가 주기'] == 1 and args['매수 조건'] == 0 and day >= (comp_date + relativedelta(months=1)) \
                    and 현재가 <= max_eprice:
                추가매수량 = math.trunc(추가금 / 현재가)
                추가매입금액 = 현재가 * 추가매수량
                보유수량 += 추가매수량
                매입가 = math.trunc((매입금액 + 추가매입금액) / 보유수량)
                매입금액 += 추가매입금액

                # 추가매수 횟수 증가 , 비교날짜 지금 날짜로 변경
                buy_count += 1
                comp_date = day
                logger.info(f'[{code}] 추가 매수 - 추가 매수 날짜 {day.strftime("%Y%m%d")}, 추가 매수량 {추가매수량}, '
                            f'추가 매수 횟수 {buy_count}, 보유 수량 {보유수량}, 매입가 {매입가:,}원, 총 매입 금액 {매입금액:,}원')
            elif args['추가 주기'] == 2 and args['매수 조건'] == 0 and day >= (comp_date + relativedelta(days=7)) and \
                    현재가 <= max_eprice:

                추가매수량 = math.trunc(추가금 / 현재가)
                추가매입금액 = 현재가 * 추가매수량
                보유수량 += 추가매수량
                매입가 = math.trunc((매입금액 + 추가매입금액) / 보유수량)
                매입금액 += 추가매입금액

                # 추가매수 횟수 증가 , 비교날짜 지금 날짜로 변경
                buy_count += 1
                comp_date = day
                logger.info(f'[{code}] 추가 매수 - 추가 매수 날짜 {day.strftime("%Y%m%d")}, 추가 매수량 {추가매수량}, '
                            f'추가 매수 횟수 {buy_count}, 보유 수량 {보유수량}, 매입가 {매입가:,}원, 총 매입 금액 {매입금액:,}원')
            elif args['매도 조건'] == 0 and max_df.iloc[0]['최대 거래량'] < df.loc[day]['거래량'] and \
                    max_df.iloc[0]['최대 거래량 종가'] < 현재가:
                매도금액 = 보유수량 * 현재가
                매도가 = 현재가
                실현손익 = (매도가 * 보유수량) - (매입가 * 보유수량)
                실현수익률 = math.trunc((실현손익 / (매입가 * 보유수량) * 100))
                보유수량 = 0
                # 수익률 = math.trunc(실현손익 / 매입금액 * 100)
                logger.info(f'[{code}] 매도 - 최초 매수일 {base_date}, 매도 날짜 {day.strftime("%Y%m%d")}, 매도가 {현재가:,}원, '
                            f'매도 수량 {보유수량}, 매도 금액 {매도금액:,}원, 실현 손익 {실현손익:,}원, 수익률 {수익률}, '
                            f'실현 수익률 {실현수익률}%')
                break

    if window.clear_checkBox.isChecked():
        window.result_itemtable.setRowCount(0)

    # 테이블위젯에 display
    평가손익 = (현재가 * 보유수량) - (매입가 * 보유수량)
    row = window.result_itemtable.rowCount()
    window.result_itemtable.insertRow(row)
    window.result_itemtable.setItem(row, 0, QTableWidgetItem(max_df.iloc[0]['종목명']))
    window.result_itemtable.setItem(row, 1, QTableWidgetItem(f'{매입가:,}원'))
    window.result_itemtable.setItem(row, 2, QTableWidgetItem(f'{평가손익:,}원'))

    수익률 = math.trunc(평가손익 / 매입금액 * 100)
    window.result_itemtable.setItem(row, 4, QTableWidgetItem(f'{수익률}%'))
    window.result_itemtable.setItem(row, 5, QTableWidgetItem(str(보유수량)))

    if 보유수량 == 0:
        window.result_itemtable.setItem(row, 3, QTableWidgetItem(f'0원'))
        window.result_itemtable.setItem(row, 6, QTableWidgetItem(f'0원'))
        window.result_itemtable.setItem(row, 7, QTableWidgetItem(f'{매도가:,}원'))
    else:
        평가금액 = 매입금액 + 평가손익
        window.result_itemtable.setItem(row, 3, QTableWidgetItem(f'{평가금액:,}원'))
        window.result_itemtable.setItem(row, 6, QTableWidgetItem(f'{현재가:,}원'))
        window.result_itemtable.setItem(row, 7, QTableWidgetItem(f'0원'))

    window.result_itemtable.setItem(row, 8, QTableWidgetItem(f'{매입금액:,}원'))
    window.result_itemtable.setItem(row, 9, QTableWidgetItem(f'{실현손익:,}원'))
    window.result_itemtable.setItem(row, 10, QTableWidgetItem(f'{실현수익률}%'))


def find_maxvol_mon(window, args):
    """

        최대 거래량 찾기

    :param window: 윈도우 클래스
    :param args: dict = {base_date, search_duration, max_vol_occur, lowest_duration, lowest_contrast, per_rate,
    dept_rate, margin_rate}
    :return: max_tick
    """

    # today = date.today()
    base_date = datetime.strptime(args['base_date'], "%Y%m%d").date()
    # 종목 찾기 시작 날짜
    search_start_date = base_date - relativedelta(months=int(args['search_duration']))

    # 6개월 이전에 종목 상장 여부 확인
    six_mon_ago = base_date - relativedelta(months=6)
    kospi_six_ago = stock.get_market_ticker_list(date=six_mon_ago, market="KOSPI")
    kosdaq_six_ago = stock.get_market_ticker_list(date=six_mon_ago, market="KOSDAQ")
    total_six_list = kospi_six_ago + kosdaq_six_ago

    # 최저가 시작 날짜
    start_low_dur = base_date - relativedelta(months=args['lowest_duration'])

    # 최대 거래 발생 시작일
    max_vol_within_date = (base_date - relativedelta(months=int(args['max_vol_within'])))

    logger.info(f"기준 일자 : {base_date.strftime('%Y%m%d')} 종목 찾기 시작 날짜 : {search_start_date.strftime('%Y%m%d')}, "
                f"기준일 6개월 전 날짜 : {six_mon_ago.strftime('%Y%m%d')}, 최저가 시작 날짜 : {start_low_dur.strftime('%Y%m%d')}, "
                f"최대 거래 발생 시작일 : {max_vol_within_date.strftime('%Y%m%d')}")

    # 전종목 조회하기
    kospi_market = stock.get_market_ticker_list(date=base_date, market="KOSPI")
    kosdaq_market = stock.get_market_ticker_list(date=base_date, market="KOSDAQ")
    total_market = kospi_market + kosdaq_market
    # total_market = ['367340']
    halt_list = trading_halt_list()
    mg_list = management_list()
    max_vol_code = []
    i = 0

    pre_progress_count = 0
    for code in total_market:
        i += 1
        total_count = len(total_market)
        stock_name = stock.get_market_ticker_name(code)
        progress_count = math.trunc(i / total_count * 100)
        logger.debug(f'======== total count : {len(total_market)}, count : {i}, '
                     f'progress : {progress_count} =======')
        if pre_progress_count < progress_count:
            pre_progress_count = progress_count
            window.progressBar.setValue(pre_progress_count)

        logger.info('[%s] ------ 시세 조회 ------ ', code)
        # 종목별 시세 조회
        df = stock.get_market_ohlcv(search_start_date.strftime("%Y%m%d"), base_date.strftime("%Y%m%d"), code)
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
        if base_day_price < 700 or (stock_name in halt_list) \
                or (stock_name in mg_list):
            logger.info(f"[{code}], 가격 {base_day_price} , 관리 , 거래정지 - PASS")
            continue

        # 최대거래 날짜, 가격
        max_vol_date = df['거래량'].idxmax()
        max_vol_last_price = df.loc[max_vol_date]['종가']
        max_vol_first_price = df.loc[max_vol_date]['시가']
        max_vol = df.loc[max_vol_date]['거래량']

        while True:
            if df.index.isin([start_low_dur.strftime("%Y%m%d")]).any():
                break
            else:
                start_low_dur = start_low_dur + relativedelta(days=1)
                logger.debug(f'-- 최저가 검색 시작 날짜 다시 조회(휴일) [{start_low_dur}]')

        subset_df = df.iloc[df.index.get_loc(start_low_dur.strftime("%Y%m%d")):]
        logger.debug('================== 최저가 기간의 dataframe =====================')
        logger.debug(subset_df)
        lowest_price_day = subset_df['종가'].idxmin()  # 최저가 날짜
        lowest_price = subset_df.loc[lowest_price_day]['종가']  # 최저가 가격

        subset_df_avg = subset_df['종가'].mean()
        logger.info(f'[{code}] ++ 주가 ++ ')
        logger.info(f'[{code}] - 최대 거래 날짜 {max_vol_date.strftime("%Y%m%d")}, 최대 거래량 종가 {max_vol_last_price:,}원')
        logger.info(f'[{code}] - 최저가 날짜 {lowest_price_day.strftime("%Y%m%d")}, 최저가 가격 {lowest_price:,}원,'
                    f' 최저가 기간 평균 가격 {math.trunc(subset_df_avg):,}원')

        logger.info('[%s] ------ 재무정보 조회 ------ ', code)
        annual_df = naver_financial_data(code)
        logger.debug(annual_df)

        # 재무정보 없는거 일단 거르자, '리츠' 이런 종목 인거 같음
        if annual_df.empty:
            logger.warning(f'[{code}] - 재무정보 없음')
            continue

        try:
            PER평균 = annual_df.loc['PER(배)'].iloc[:-1].astype(float).mean()
            부채비율 = annual_df.loc['부채비율'].iloc[:-1].astype(float).mean()
            영업이익률 = annual_df.loc['영업이익률'].iloc[:-1].astype(float).mean()
        except ValueError as ve:
            logger.error('[%s] - %s', code, ve)
            continue

        if math.isnan(PER평균) or math.isnan(부채비율) or math.isnan(영업이익률):
            logger.warning(f'[{code}] - PER평균 or 부채비율 or 영업이익률 is Nan')
            continue

        logger.info(f'[{code}] ++ 성장성 ++ ')

        logger.info(f'PER 평균: {math.trunc(PER평균)}%, 부채 비율 평균: {math.trunc(부채비율)}%, '
                    f'영업 이익률 평균: {math.trunc(영업이익률)}%')
        # 최대 거래 월이 현재로부터 N 개월 안에 터졌다면 종목 추가
        if max_vol_within_date <= max_vol_date.date() <= base_date and \
                lowest_price * float(args['lowest_contrast']) >= subset_df_avg and \
                PER평균 < int(args['per_rate']) and 부채비율 < int(args['dept_rate']) and \
                영업이익률 >= int(args['margin_rate']):
            max_vol_code.append({'종목 번호': str(code), '종목명': stock_name,
                                 '최대 거래량 시가': max_vol_first_price, '최대 거래량 종가': max_vol_last_price,
                                 '최대 거래량': max_vol, '최대 거래 날짜': max_vol_date.strftime("%Y%m%d"),
                                 '재무 정보': f'https://finance.naver.com/item/main.nhn?code={code}',
                                 '뉴스': f'https://finance.naver.com/item/news_news.nhn?code={code}'})
            logger.info('[%s] - %s년 역대 거래량, 최저가 대비 %s배 이하, %s', code, args['search_duration'],
                        args['lowest_contrast'], stock_name)

    logger.info('======== 최대 거래량 종목 ==========')
    logger.info(max_vol_code)
    return max_vol_code


def naver_financial_data(code):
    """
        네이버로 재무정보
    :param code: 종목번호
    :return:
    """
    url = f"https://finance.naver.com/item/main.nhn?code={code}"
    res = requests.get(url)
    try:
        financial_stmt = pd.read_html(res.text)[3]
    except ValueError as ve:
        logger.error(f'재무정보가 존재하지 않음 [{ve}]')
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
    """
        거래정지 리스트 by naver
    :return:
    """
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
    """
        관리종목 리스트 by naver
    :return:
    """
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
