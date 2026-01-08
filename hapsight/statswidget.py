import pandas as pd  # <-- AJOUT

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel
)
from PySide6.QtCore import Qt


class StatsWidget(QWidget):
    """
    Ce widget contiendra les graphiques, tableaux et analyses statistiques.
    """
    def __init__(self, df: pd.DataFrame, parent=None):  # <-- CHANGEMENT
        super().__init__(parent)
        self.df = df  # <-- AJOUT (on garde df pour les futurs graph)

        layout = QVBoxLayout(self)

        placeholder_label = QLabel("Conteneur pour les Statistiques (Graphiques et Tableaux)")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder_label)
