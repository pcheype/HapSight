import sys

import pandas as pd
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from hapsight.countrieswidget import CountriesWidget
from hapsight.mapwidget import MapWidget
from hapsight.stats_widget import StatsWidget


def load_data() -> pd.DataFrame:
    return pd.read_csv("dataset/happiness.csv")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HappySight")
        self.setGeometry(100, 100, 1200, 600)

        df = load_data()

        self.tab_manager = QTabWidget()
        self.map_tab = MapWidget(df)
        self.countries_tab = CountriesWidget(df)
        self.PaoloStats_tab = StatsWidget(df)

        self.tab_manager.addTab(self.map_tab, "Carte du Monde")
        self.tab_manager.addTab(self.PaoloStats_tab, "Stats et Corrélations")
        self.tab_manager.addTab(self.countries_tab, "Pays")

        self.setCentralWidget(self.tab_manager)


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("dataset/iconapp.png"))
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
