import sys
import pandas as pd

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,  # Import pour le système d'onglets
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from hapsight.mapwidget import MapWidget
from hapsight.statswidget import StatsWidget
from hapsight.countrieswidget import CountriesWidget
from hapsight.paolo_stats_widget import PaoloStatsWidget


def load_data() -> pd.DataFrame:
    # Chemin relatif depuis la racine du repo (là où tu lances `uv run hapsight`)
    return pd.read_csv("dataset/WorldHappiness_Corruption_2015_2020.csv")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HappySight")
        self.setGeometry(100, 100, 1200, 600)

        df = load_data()

        self.tab_manager = QTabWidget()
        
        # --- 2. Création des instances de nos widgets d'onglets ---
        self.map_tab = MapWidget()
        self.stats_tab = StatsWidget()

        # --- 3. Ajout des onglets au QTabWidget ---
        self.tab_manager.addTab(self.map_tab, "Carte du Monde")
        self.tab_manager.addTab(self.stats_tab, "Statistiques et Corrélations")
        self.tab_manager.addTab(self.countries_tab, "Pays")
        self.tab_manager.addTab(self.PaoloStats_tab, "Stats Paolo")


        self.setCentralWidget(self.tab_manager)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
