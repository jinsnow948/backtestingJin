import os
import sys

import logging.config
import json

from PyQt5.QtWidgets import *
from PyQt5 import uic

from backtestImpl import find_maxvol_mon

# log 폴더 만들기
if not os.path.exists('../log'):
    os.makedirs('../log')

# json load
with open('../config/logger.json') as f:
    config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger('logger-1')
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("PyQt5.uic").setLevel(logging.WARNING)

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
        self.max_vol_duration_edit.setText('10')
        self.max_vol_occur_edit.setText('3')
        self.lowest_duration_edit.setText('1')
        self.lowest_contrast_edit.setText('1.7')

        # 성장성
        self.per_edit.setText('40')
        self.dept_edit.setText('100')
        self.margin_edit.setText('15')

    def search_clicked(self):
        args = self.get_edit_text()
        max_list = find_maxvol_mon(args)

        try:
            if max_list:
                for item in max_list:
                    row = self.itemTable.rowCount()
                    self.itemTable.insertRow(row)
                    self.itemTable.setItem(row, 0, QTableWidgetItem(item['종목번호']))
                    self.itemTable.setItem(row, 1, QTableWidgetItem(item['종목명']))
        except Exception as e:
            logger.error(e)

    def get_edit_text(self):
        """
            text edit 값 가져오기
        :return: dict = {max_vol_duration, max_vol_occur, lowest_duration,
        lowest_contrast, per_rate, dept_rate, margin_rate}
        """
        max_vol_duration = self.max_vol_duration_edit.text()
        max_vol_occur = self.max_vol_occur_edit.text()
        lowest_duration = self.lowest_duration_edit.text()
        lowest_contrast = self.lowest_contrast_edit.text()

        per_rate = self.per_edit.text()
        dept_rate = self.dept_edit.text()
        margin_rate = self.margin_edit.text()

        edit_text_list = {"max_vol_duration": max_vol_duration, "max_vol_occur": max_vol_occur,
                          "lowest_duration": lowest_duration, "lowest_contrast": lowest_contrast,
                          "per_rate": per_rate, "dept_rate": dept_rate, "margin_rate": margin_rate}

        return edit_text_list


# 스크립트를 실행하려면 여백의 녹색 버튼을 누릅니다.
if __name__ == '__main__':
    # QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)

    # WindowClass의 인스턴스 생성
    myWindow = WindowClass()

    # 프로그램 화면을 보여주는 코드
    myWindow.show()

    # 프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
