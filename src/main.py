import os
import sys

import logging.config
import json
from datetime import date
from dateutil.relativedelta import relativedelta

from PyQt5.QtWidgets import *
from PyQt5 import uic

from backtestImpl import find_maxvol_mon

import tkinter as tk
from tkinter import filedialog
import pandas as pd

form_class = uic.loadUiType("backTest.ui")[0]


# 화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.search_button.clicked.connect(self.search_clicked)
        self.excel_download_button.clicked.connect(self.download_clicked)

        self.today_radioButton.clicked.connect(self.radFunction)
        self.predate_radioButton.clicked.connect(self.radFunction)
        self.year_radioButton.clicked.connect(self.radFunction)
        self.month_radioButton.clicked.connect(self.radFunction)

        self.year_radioButton.hide()
        self.month_radioButton.hide()

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
            self.max_list: list[dict[str, str]] = find_maxvol_mon(args)

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

        edit_text_list = {"search_duration": search_duration, "max_vol_within": max_vol_within,
                          "lowest_duration": lowest_duration, "lowest_contrast": lowest_contrast,
                          "per_rate": per_rate, "dept_rate": dept_rate, "margin_rate": margin_rate}

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

    # WindowClass의 인스턴스 생성
    myWindow = WindowClass()

    # 프로그램 화면을 보여주는 코드
    myWindow.show()

    # 프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
