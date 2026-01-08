import pandas as pd
from PySide6.QtWidgets import QApplication

from hapsight.mainwindow import MainWindow


def test_mainwindow():
    _ = QApplication()
    window = MainWindow()
    assert isinstance(window, MainWindow)

    assert isinstance(window.map_tab.data_happiness, pd.DataFrame)
