import os
import sys

import logging.config
import json
from datetime import date

from PyQt5.QtGui import QIcon
from dateutil.relativedelta import relativedelta

from PyQt5.QtWidgets import *
from PyQt5 import uic

import tkinter as tk
from tkinter import filedialog
import pandas as pd

form_class = uic.loadUiType("backTest.ui")[0]


# 화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 이벤트 연결
        self.search_button.clicked.connect(self.search_clicked)
        self.excel_download_button.clicked.connect(self.download_clicked)

        self.today_radioButton.clicked.connect(self.radFunction)
        self.predate_radioButton.clicked.connect(self.radFunction)
        self.year_radioButton.clicked.connect(self.radFunction)
        self.month_radioButton.clicked.connect(self.radFunction)

        # default value
        self.today_radioButton.setChecked(True)
        self.base_date_edit.setText(date.today().strftime("%Y%m%d"))
        self.year_radioButton.hide()
        self.month_radioButton.hide()

        self.s_year_radioButton.setChecked(True)
        self.o_month_radioButton.setChecked(True)
        self.l_year_radioButton.setChecked(True)
        self.c_low_radioButton.setChecked(True)


        self.max_list = []
        self.base_date = ""

        # default value
        # 주가
        self.search_duration_edit.setText('10')
        self.max_vol_within_edit.setText('6')
        self.lowest_duration_edit.setText('1')
        self.lowest_contrast_edit.setText('1.4')

        # 성장성
        self.per_edit.setText('40')
        self.dept_edit.setText('100')
        self.margin_edit.setText('15')

    def search_clicked(self):
        """
            종목 찾기 버튼 클릭
        :return:
        """
        try:
            self.itemTable.setRowCount(0)

            args = self.get_edit_text()
            # self.max_list: list[dict[str, str]] = find_maxvol_mon(args)
            self.max_list = [
                {'종목번호': '003550', '종목명': 'LG', '재무정보': 'https://finance.naver.com/item/main.nhn?code=003550',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=003550'},
                {'종목번호': '051900', '종목명': 'LG생활건강', '재무정보': 'https://finance.naver.com/item/main.nhn?code=051900',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=051900'},
                {'종목번호': '037710', '종목명': '광주신세계', '재무정보': 'https://finance.naver.com/item/main.nhn?code=037710',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=037710'},
                {'종목번호': '192080', '종목명': '더블유게임즈', '재무정보': 'https://finance.naver.com/item/main.nhn?code=192080',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=192080'},
                {'종목번호': '284740', '종목명': '쿠쿠홈시스', '재무정보': 'https://finance.naver.com/item/main.nhn?code=284740',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=284740'},
                {'종목번호': '290380', '종목명': '대유', '재무정보': 'https://finance.naver.com/item/main.nhn?code=290380',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=290380'},
                {'종목번호': '041920', '종목명': '메디아나', '재무정보': 'https://finance.naver.com/item/main.nhn?code=041920',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=041920'},
                {'종목번호': '251630', '종목명': '브이원텍', '재무정보': 'https://finance.naver.com/item/main.nhn?code=251630',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=251630'},
                {'종목번호': '335890', '종목명': '비올', '재무정보': 'https://finance.naver.com/item/main.nhn?code=335890',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=335890'},
                {'종목번호': '094840', '종목명': '슈프리마에이치큐', '재무정보': 'https://finance.naver.com/item/main.nhn?code=094840',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=094840'},
                {'종목번호': '052790', '종목명': '액토즈소프트', '재무정보': 'https://finance.naver.com/item/main.nhn?code=052790',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=052790'},
                {'종목번호': '104830', '종목명': '원익머트리얼즈', '재무정보': 'https://finance.naver.com/item/main.nhn?code=104830',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=104830'},
                {'종목번호': '078340', '종목명': '컴투스', '재무정보': 'https://finance.naver.com/item/main.nhn?code=078340',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=078340'},
                {'종목번호': '030520', '종목명': '한글과컴퓨터', '재무정보': 'https://finance.naver.com/item/main.nhn?code=030520',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=030520'}]

            if self.max_list:
                for item in self.max_list:
                    row = self.itemTable.rowCount()
                    self.itemTable.insertRow(row)
                    self.itemTable.setItem(row, 0, QTableWidgetItem(item['종목번호']))
                    self.itemTable.setItem(row, 1, QTableWidgetItem(item['종목명']))
        except Exception as e:
            logger.error(e)

    def download_clicked(self):
        """
            엑셀다운로드 버튼 클릭
        :return:
        """
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.asksaveasfilename(initialdir="/", title="Select file", defaultextension=".xlsx",
                                                filetypes=(("Excel 통합문서", "*.xlsx"), ("all files", "*.*")))

        # XlsxWriter 엔진으로 Pandas writer 객체 만들기
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')

        df = pd.DataFrame(self.max_list)

        df2 = pd.DataFrame(data=self.get_edit_text(), index=['입력값'])
        df2 = df2.rename(columns={"search_duration": "종목 검색 기간", "max_vol_within": "N개월 이내 최대 거래량",
                                  "lowest_duration": "N년 최저가", "lowest_contrast": "최저가 기간 평균 대비 최저가 배수",
                                  "per_rate": "PER 평균", "dept_rate": "부채비율", "margin_rate": "평균 영업이익률"})

        try:
            df2 = (df2.T)
            # DataFrame을 xlsx에 쓰기
            df.to_excel(writer, sheet_name='Summary')
            df2.style.set_properties(**{'text-align': 'right'}). \
                set_table_styles([dict(selector='th', props=[('text-align', 'left')])]). \
                to_excel(writer, sheet_name='Summary', startcol=6, startrow=0)

        except Exception as e:
            logger.error(e)

        # Pandas writer 객체 닫기
        writer.close()

    def get_edit_text(self):
        """
            text edit 값 가져오기
        :return: dict = {search_duration, max_vol_within, lowest_duration, lowest_contrast,
        per_rate, dept_rate, margin_rate}
        """

        search_duration = self.search_duration_edit.text()
        lowest_duration = self.lowest_duration_edit.text()
        lowest_contrast = self.lowest_contrast_edit.text()
        max_vol_within = self.max_vol_within_edit.text()

        per_rate = self.per_edit.text()
        dept_rate = self.dept_edit.text()
        margin_rate = self.margin_edit.text()

        # button check
        if self.today_radioButton.isChecked():
            base_date = self.base_date_edit.text()

        if self.s_year_radioButton.isChecked():
            s_year = True
        elif self.s_month_radioButton.isChecked():
            s_year = False

        if self.o_year_radioButton.isChecked():
            o_year = True
        elif self.o_month_radioButton.isChecked():
            o_year = False

        if self.l_year_radioButton.isChecked():
            l_year = True
        elif self.l_month_radioButton.isChecked():
            l_year = False

        if self.c_gra_radioButton.isChecked():
            c_gra = True
        elif self.c_low_radioButton.isChecked():
            c_gra = False

        edit_text_list = {"base_date": base_date, "search_duration": search_duration,
                          "max_vol_within": max_vol_within, "lowest_duration": lowest_duration,
                          "lowest_contrast": lowest_contrast, "per_rate": per_rate,
                          "dept_rate": dept_rate, "margin_rate": margin_rate}

        return edit_text_list

    def radFunction(self):
        if self.today_radioButton.isChecked():
            self.base_date_edit.setText(date.today().strftime("%Y%m%d"))
            self.year_radioButton.hide()
            self.month_radioButton.hide()
            # self.base_date = date.today().strftime("%Y%m%d")
        elif self.predate_radioButton.isChecked():
            self.base_date_edit.setText("")

            self.year_radioButton.show()
            self.month_radioButton.show()

            self.year_radioButton.setChecked(True)

            # if self.year_radioButton.isChecked():
            #     self.base_date = date.today() - relativedelta(years=int(self.base_date_edit.text()))
            # elif self.month_radioButton.isChecked():
            #     self.base_date = date.today() - relativedelta(years=int(self.base_date_edit.text()))


# 스크립트를 실행하려면 여백의 녹색 버튼을 누릅니다.
if __name__ == '__main__':
    # log 폴더 만들기
    if not os.path.exists('../log'):
        os.makedirs('../log')

    # json load
    with open('../config/logger.json') as f:
        config = json.load(f)

    # logging config
    logging.config.dictConfig(config)
    logger = logging.getLogger('logger-1')
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PyQt5.uic").setLevel(logging.WARNING)
    # KOSPI = "1001"
    # KOSDAQ = "2001"

    # QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('../icons/rich-man.ico'))
    # app.setStyle("Fusion")

    # WindowClass의 인스턴스 생성
    myWindow = WindowClass()

    # 프로그램 화면을 보여주는 코드
    myWindow.show()

    # 프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
