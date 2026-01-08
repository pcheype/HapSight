import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,  # Import pour le système d'onglets
)

from hapsight.mapwidget import MapWidget
from hapsight.statswidget import StatsWidget


# --- Fenêtre Principale (Conteneur des onglets) ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Paramètres de la fenêtre principale ---
        self.setWindowTitle("HappySight")
        self.setGeometry(100, 100, 1200, 600)

        # --- 1. Création du QTabWidget ---
        self.tab_manager = QTabWidget()

        # --- 2. Création des instances de nos widgets d'onglets ---
        self.map_tab = MapWidget()
        self.stats_tab = StatsWidget()

        # --- 3. Ajout des onglets au QTabWidget ---
        self.tab_manager.addTab(self.map_tab, "Carte du Monde")
        self.tab_manager.addTab(self.stats_tab, "Statistiques et Corrélations")

        # --- 4. Définir le QTabWidget comme widget central ---
        # Le widget central remplit la MainWindow
        self.setCentralWidget(self.tab_manager)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
