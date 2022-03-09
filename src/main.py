import os
import re
import sys

import logging.config
import json


from PyQt5.QtWidgets import *
from PyQt5 import uic


# log 폴더 만들기
if not os.path.exists('../log'):
    os.makedirs('../log')

# json load
config = json.load(open('../config/logger.json'))
logging.config.dictConfig(config)
logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("uiparser").setLevel(logging.WARNING)
logging.getLogger("properties").setLevel(logging.WARNING)

KOSPI = "1001"
KOSDAQ = "2001"

form_class = uic.loadUiType("backTest.ui")[0]


# 화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.search_button.clicked.connect(self.search_clicked)

        # default value
        # 주가
        self.max_vol_duration_edit.getText(10)
        self.max_vol_occur_edit.getText(3)
        self.lowest_duration_edit.getText(1)
        self.lowest_contrast_edit.getText(1.3)

        # 성장성
        self.per_edit(20)
        self.dept_edit(100)
        self.margin_edit(20)

    def search_clicked(self):
        print(111)

    def get_edit_text(self):
        max_vol_duration = self.max_vol_duration_edit.text()
        max_vol_occur = self.max_vol_occur_edit.text()
        lowest_duration = self.lowest_duration_edit.text()
        lowest_contrast = self.lowest_contrast_edit.text()

        per = self.per_edit.text()
        dept = self.dept_edit.text()
        margin = self.margin_edit.text()

        edit_text_list = [max_vol_duration,max_vol_occur,lowest_duration,lowest_contrast,per,dept,margin]

# 스크립트를 실행하려면 여백의 녹색 버튼을 누릅니다.
if __name__ == '__main__':
    # QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)

    # WindowClass의 인스턴스 생성
    myWindow = WindowClass()

    # 프로그램 화면을 보여주는 코드
    myWindow.show()

    # 프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    sys.exit(app.exec_())

    today = date.today()

    # 코스닥 차트 그릴 년도
    five_yrs = today - relativedelta(years=5)

    # 코스닥 차트그리기
    # fg = make_chart(five_yrs, '2001')
    # fg.show()

    # 전종목 조회하기
    kospi_tickers = stock.get_market_ticker_list(date=today, market="KOSPI")
    kosdaq_tickers = stock.get_market_ticker_list(date=today, market="KOSDAQ")
    tickers = kospi_tickers + kosdaq_tickers

    # logger.debug(f'전 종목번호 조회 {tickers}')
    n_year = ""

