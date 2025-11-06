import numpy as np

from hapsight.mainwindow import MainWindow


def test_mainwindow():
    app = MainWindow()
    assert isinstance(app, MainWindow)