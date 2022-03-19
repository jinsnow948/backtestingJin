import csv
import json
import logging.config
import os
import sys
import tkinter as tk
from datetime import datetime, date
from tkinter import filedialog, messagebox

import pandas
import pandas as pd
import xlsxwriter
import xlwt as xlwt
from PyQt5 import uic, QtCore
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from dateutil.relativedelta import relativedelta

from backtestingImpl import make_chart, backtest

form_class = uic.loadUiType("designingJin.ui")[0]


# 종목찾기 쓰레드
class Thread(QThread):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        try:
            # 상위 윈도우 위젯 기본값 설정
            self.parent.progressBar.show()
            self.parent.search_button.setDisabled(True)
            self.parent.excel_download_button.setDisabled(True)
            self.parent.itemTable.setRowCount(0)
            args = self.parent.get_edit_text()

            # 종목 찾기 결과 리스트
            # self.parent.max_list: list[dict[str, str]] = find_maxvol_mon(self.parent, args)
            self.parent.max_list = [
                {'종목 번호': '000995', '종목명': 'DB하이텍1우', '최대 거래량 시가': 44000, '최대 거래량 종가': 41000, '최대 거래량': 146233,
                 '최대 거래 날짜': '20170308', '재무 정보': 'https://finance.naver.com/item/main.nhn?code=000995',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=000995'},
                {'종목 번호': '005935', '종목명': '삼성전자우', '최대 거래량 시가': 30640, '최대 거래량 종가': 31640, '최대 거래량': 1587462,
                 '최대 거래 날짜': '20170125', '재무 정보': 'https://finance.naver.com/item/main.nhn?code=005935',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=005935'},
                {'종목 번호': '019550', '종목명': 'SBI인베스트먼트', '최대 거래량 시가': 871, '최대 거래량 종가': 885, '최대 거래량': 82571452,
                 '최대 거래 날짜': '20170315', '재무 정보': 'https://finance.naver.com/item/main.nhn?code=019550',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=019550'},
                {'종목 번호': '207760', '종목명': '미스터블루', '최대 거래량 시가': 3430, '최대 거래량 종가': 3695, '최대 거래량': 3815561,
                 '최대 거래 날짜': '20160928', '재무 정보': 'https://finance.naver.com/item/main.nhn?code=207760',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=207760'},
                {'종목 번호': '123570', '종목명': '이엠넷', '최대 거래량 시가': 2735, '최대 거래량 종가': 3520, '최대 거래량': 8270362,
                 '최대 거래 날짜': '20170105', '재무 정보': 'https://finance.naver.com/item/main.nhn?code=123570',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=123570'},
                {'종목 번호': '044060', '종목명': '조광ILI', '최대 거래량 시가': 7530, '최대 거래량 종가': 7680, '최대 거래량': 9082120,
                 '최대 거래 날짜': '20161115', '재무 정보': 'https://finance.naver.com/item/main.nhn?code=044060',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=044060'},
                {'종목 번호': '045340', '종목명': '토탈소프트', '최대 거래량 시가': 5950, '최대 거래량 종가': 5390, '최대 거래량': 12033508,
                 '최대 거래 날짜': '20161118', '재무 정보': 'https://finance.naver.com/item/main.nhn?code=045340',
                 '뉴스': 'https://finance.naver.com/item/news_news.nhn?code=045340'}]

            # 테이블뷰에 보여주기
            if self.parent.max_list:
                for item in self.parent.max_list:
                    row = self.parent.itemTable.rowCount()
                    self.parent.itemTable.insertRow(row)
                    self.parent.itemTable.setItem(row, 0, QTableWidgetItem(item['종목 번호']))
                    self.parent.itemTable.setItem(row, 1, QTableWidgetItem(item['종목명']))
            self.parent.search_button.setEnabled(True)
            self.parent.excel_download_button.setEnabled(True)
            self.parent.progressBar.hide()

        except Exception as e:
            logger.error(e)
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(title="오류", message=e)
            # w = Label(root, text=e, font="50")
            # w.pack()

            self.parent.search_button.setEnabled(True)
            self.parent.excel_download_button.setEnabled(True)
            self.parent.progressBar.hide()
            root.mainloop()


# 윈도우 클래스
class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 이벤트 연결
        self.search_button.clicked.connect(self.search_clicked)
        self.excel_download_button.clicked.connect(self.download_clicked)
        self.excel_download2_button.clicked.connect(self.download2_clicked)
        self.backTest_button.clicked.connect(self.backtest_clicked)
        self.today_radioButton.clicked.connect(self.radio_func)
        self.predate_radioButton.clicked.connect(self.radio_func)
        self.year_radioButton.clicked.connect(self.radio_func)
        self.month_radioButton.clicked.connect(self.radio_func)

        # 테이블위젯에서 메뉴 연결
        self.itemTable.setContextMenuPolicy(Qt.CustomContextMenu)  # +++
        self.itemTable.customContextMenuRequested.connect(self.generate_menu)  # +++
        self.itemTable.viewport().installEventFilter(self)

        # default value
        self.today_radioButton.setChecked(True)
        self.base_date_edit.setText(date.today().strftime("%Y%m%d"))
        self.code_hidden_label.hide()
        self.year_radioButton.hide()
        self.month_radioButton.hide()

        self.year_radioButton.setChecked(True)
        self.s_year_radioButton.setChecked(True)
        self.o_month_radioButton.setChecked(True)
        self.l_year_radioButton.setChecked(True)

        self.max_list = []
        self.base_date = ""

        # 주가
        self.search_duration_edit.setText('10')
        self.max_vol_within_edit.setText('6')
        self.lowest_duration_edit.setText('1')
        self.lowest_contrast_edit.setText('1.4')

        # 성장성
        self.per_edit.setText('40')
        self.dept_edit.setText('100')
        self.margin_edit.setText('15')

        self.progressBar.hide()

    def search_clicked(self):
        """
        종목 찾기
        :return:
        """
        x = Thread(self)
        x.start()

    def backtest_clicked(self):
        """
        백테스트
        :return:
        """
        try:
            args = self.get_backtest_edit_text()
            backtest(self, args)
        except Exception as e:
            logger.error(e)
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(title="오류", message=e)

            self.search_button.setEnabled(True)
            self.excel_download_button.setEnabled(True)
            self.progressBar.hide()
            root.mainloop()

    def download_clicked(self):
        """
            tab1 엑셀다운로드 버튼 클릭
        :return:
        """
        try:
            # 파일 브라우저 실행
            root = tk.Tk()
            root.withdraw()
            filename = filedialog.asksaveasfilename(initialdir="/", title="Select file", defaultextension=".xlsx",
                                                    filetypes=(("Excel 통합 문서", "*.xlsx"), ("all files", "*.*")))

            # XlsxWriter 엔진 으로 Pandas writer 객체 만들기
            writer = pd.ExcelWriter(filename, engine='xlsxwriter')

            # list to df
            df = pd.DataFrame(self.max_list)

            df2 = pd.DataFrame(data=self.get_edit_text(), index=['입력값'])

            # 컬럼명 변경경
            df2 = df2.rename(columns={"base_date": "기준일", "search_duration": "종목 검색 기간(개월)",
                                      "max_vol_within": "N개월 이내 최대 거래량", "lowest_duration": "N개월 최저가",
                                      "lowest_contrast": "최저가 기간 평균 대비 최저가 배수", "per_rate": "PER 평균",
                                      "dept_rate": "부채 비율", "margin_rate": "평균 영업 이익률"})
            # DF 행열 변경
            df2 = (df2.T)

            # DataFrame을 xlsx에 쓰기
            df.to_excel(writer, sheet_name='Summary')
            df2.style.set_properties(**{'text-align': 'right'}). \
                set_table_styles([dict(selector='th', props=[('text-align', 'left')])]). \
                to_excel(writer, sheet_name='Summary', startcol=10, startrow=0)

            # 엑셀 스타일
            pandas.io.formats.excel.ExcelFormatter.header_style = None

            workbook = writer.book
            worksheet = writer.sheets['Summary']
            header_fmt = workbook.add_format(
                {'font_name': 'Arial', 'font_size': 10, 'bold': True, 'font_color': 'white',
                 'bg_color': '#214567'})

            worksheet.write(0, 0, '번호', header_fmt)
            worksheet.write(0, 10, '항목', header_fmt)

            for columnnum, columnname in enumerate(list(df.columns)):
                worksheet.write(0, columnnum + 1, columnname, header_fmt)
            for columnnum, columnname in enumerate(list(df2.columns)):
                worksheet.write(0, columnnum + 11, columnname, header_fmt)

            # 엑셀 저장
            writer.save()
        except Exception as e:
            logger.error(e)
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(title="오류", message=e)

            root.mainloop()

    @staticmethod
    def write_qtable_to_df(table):
        """
            tablewidet to dataframe
        :param table: tablewidget
        :return:
        """
        col_count = table.columnCount()
        row_count = table.rowCount()
        headers = [str(table.horizontalHeaderItem(i).text()) for i in range(col_count)]

        # df indexing is slow, so use lists
        df_list = []
        for row in range(row_count):
            df_list2 = []
            for col in range(col_count):
                table_item = table.item(row, col)
                df_list2.append('' if table_item is None else str(table_item.text()))
            df_list.append(df_list2)

        df = pd.DataFrame(df_list, columns=headers)

        return df

    def download2_clicked(self):
        """
            tab2 엑셀저장
        :return:
        """
        try:
            root = tk.Tk()
            root.withdraw()
            filename = filedialog.asksaveasfilename(initialdir="/", title="Select file", defaultextension=".xlsx",
                                                    filetypes=(("Excel 통합 문서", "*.xlsx"), ("all files", "*.*")))

            # XlsxWriter 엔진 으로 Pandas writer 객체 만들기
            writer = pd.ExcelWriter(filename, engine='xlsxwriter')
            df = self.write_qtable_to_df(self.result_itemtable)
            df.to_excel(writer, sheet_name='Summary')

            # 엑셀 스타일
            pandas.io.formats.excel.ExcelFormatter.header_style = None

            workbook = writer.book
            worksheet = writer.sheets['Summary']
            header_fmt = workbook.add_format(
                {'font_name': 'Arial', 'font_size': 10, 'bold': True, 'font_color': 'white',
                 'bg_color': '#214567'})

            worksheet.write(0, 0, '번호', header_fmt)

            for columnnum, columnname in enumerate(list(df.columns)):
                worksheet.write(0, columnnum + 1, columnname, header_fmt)

            writer.save()
        except Exception as e:
            logger.error(e)
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(title="오류", message=e)

            root.mainloop()

    def eventFilter(self, source, event):
        """
            마우스 이벤트
        :param source:
        :param event:
        :return:
        """
        if (event.type() == QtCore.QEvent.MouseButtonPress and
                event.buttons() == QtCore.Qt.RightButton and
                source is self.itemTable.viewport()):
            menu = QMenu(self)
            item = self.itemTable.itemAt(event.pos())
            args = self.get_edit_text()
            if item is not None:
                chart_action = menu.addAction("차트 보기")  # (QAction('test'))
                action = menu.exec_(event.globalPos())
                logger.debug('Global Pos: %s', event.globalPos())
                if chart_action == action:
                    logger.debug('row: %d, column: %d', item.row(), item.column())
                    if item.column() == 1:
                        item = self.itemTable.item(item.row(), 0)
                        logger.debug('item : %s', item.text())
                        make_chart(args, item.text())
                    else:
                        logger.debug('item : %s', item.text())
                        make_chart(args, item.text())
                    # menu.exec_(event.globalPos())
        elif event.type() == QtCore.QEvent.MouseButtonDblClick and source is self.itemTable.viewport():
            item = self.itemTable.itemAt(event.pos())
            if item is not None:
                self.tabWidget.setCurrentIndex(1)
                item0 = self.itemTable.item(item.row(), 0)
                self.code_hidden_label.setText(item0.text())
                item1 = self.itemTable.item(item.row(), 1)
                self.btest_stock_label.setText(item1.text())
                args = self.get_edit_text()
                self.btest_sdate_label.setText(args['base_date'].strftime("%Y%m%d"))
                self.init_money_edit.setText('1')
                self.add_money_edit.setText('1')

        return super(QMainWindow, self).eventFilter(source, event)

    def generate_menu(self, pos):
        logger.debug("pos======", pos)
        self.menu.exec_(self.itemTable.mapToGlobal(pos))

    def get_edit_text(self):
        """
            text edit 값 가져오기
        :return: dict = {base_date, search_duration, max_vol_within, lowest_duration, lowest_contrast,
        per_rate, dept_rate, margin_rate}
        """

        if self.base_date_edit.text() == "":
            raise Exception("기준 일자 입력!!")

        # 기준일
        today = date.today()
        if self.today_radioButton.isChecked():
            base_date = datetime.strptime(self.base_date_edit.text(), "%Y%m%d")
        elif self.predate_radioButton.isChecked() and self.year_radioButton.isChecked():
            base_date = today - relativedelta(years=int(self.base_date_edit.text()))
        elif self.predate_radioButton.isChecked() and self.month_radioButton.isChecked():
            base_date = today - relativedelta(months=int(self.base_date_edit.text()))

        # 종목 검색 기간
        if self.s_year_radioButton.isChecked():
            search_duration = int(self.search_duration_edit.text()) * 12
        elif self.s_month_radioButton.isChecked():
            search_duration = int(self.search_duration_edit.text())

        if self.o_year_radioButton.isChecked():
            max_vol_within = int(self.max_vol_within_edit.text()) * 12
        elif self.o_month_radioButton.isChecked():
            max_vol_within = int(self.max_vol_within_edit.text())

        if self.l_year_radioButton.isChecked():
            lowest_duration = int(self.lowest_duration_edit.text()) * 12

        elif self.l_month_radioButton.isChecked():
            lowest_duration = int(self.lowest_duration_edit.text())
        lowest_contrast = self.lowest_contrast_edit.text()

        per_rate = self.per_edit.text()
        dept_rate = self.dept_edit.text()
        margin_rate = self.margin_edit.text()

        edit_text_list = {"base_date": base_date.strftime("%Y%m%d"), "search_duration": search_duration,
                          "max_vol_within": max_vol_within, "lowest_duration": lowest_duration,
                          "lowest_contrast": lowest_contrast, "per_rate": per_rate,
                          "dept_rate": dept_rate, "margin_rate": margin_rate}

        return edit_text_list

    def get_backtest_edit_text(self):
        """
            백테스팅 탭에서의 인풋값 받기
        :return: 기준일, 추가 주기, 매수 조건, 매도 조건, 초기금, 추가금
        """
        add_interval = self.add_interval_box.currentIndex()  # 1. 년 1회 2. 월 1회 3. 주 1회
        logger.debug(f'추가 주기 : 인덱스({self.add_interval_box.currentIndex()}), '
                     f'텍스트[{self.add_interval_box.currentText()}]')
        buy_cond = self.buy_cond_box.currentIndex()  # 1.최대 거래량 기준봉 가격 범위 2. 묻지마 추매
        logger.debug(f'매수 조건 : 인덱스({self.buy_cond_box.currentIndex()}), '
                     f'텍스트[{self.buy_cond_box.currentText()}]')
        sell_cond = self.sell_cond_box.currentIndex()  # 1.기준 거래량 초과 거래량 발생시 2. 존버
        logger.debug(f'매도 조건 : 인덱스({self.sell_cond_box.currentIndex()}), '
                     f'텍스트[{self.sell_cond_box.currentText()}]')
        base_date = self.btest_sdate_label.text()
        init_money = self.init_money_edit.text()
        add_money = self.add_money_edit.text()

        if init_money == "" or add_money == "":
            raise Exception("투자 금액 입력!!")

        args = {'기준일': base_date, '추가 주기': add_interval, '매수 조건': buy_cond, '매도 조건': sell_cond,
                '초기금': init_money, '추가금': add_money}

        return args

    def radio_func(self):
        if self.today_radioButton.isChecked():
            self.base_date_edit.setText(date.today().strftime("%Y%m%d"))
            self.year_radioButton.hide()
            self.month_radioButton.hide()

            self.day_label.setText("일")

        elif self.predate_radioButton.isChecked():
            self.base_date_edit.setText("")

            self.year_radioButton.show()
            self.month_radioButton.show()

            self.day_label.setText("이전")


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
