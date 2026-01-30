import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QFileDialog, QGroupBox,
    QSpinBox, QMessageBox
)

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class PaoloStatsWidget(QWidget):

    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.df = df.copy()
        self.df.columns = self.df.columns.str.strip()

        self._normalize_columns()
        self._ensure_types()


        self.selected_countries = set()

        root = QGridLayout(self)
        root.setSpacing(10)

        #vertical_layout = QVBoxLayout()
        controls_hist = QGroupBox("Histogrammes")
        controls_corr = QGroupBox("Corrélations")
        controls_autre = QGroupBox("Autres")

        root.addWidget(controls_hist,0,0)
        root.addWidget(controls_corr,0,1)
        root.addWidget(controls_autre,0,2)

        self.figurehist = Figure(figsize=(4, 4), dpi=110)
        self.canvashist = FigureCanvasQTAgg(self.figurehist)
        root.addWidget(self.canvashist,1,0)

        self.figurecorr = Figure(figsize=(4, 4), dpi=110)
        self.canvascorr = FigureCanvasQTAgg(self.figurecorr)
        root.addWidget(self.canvascorr,1,1)

        self.figureautre = Figure(figsize=(4, 4), dpi=110)
        self.canvasautre = FigureCanvasQTAgg(self.figureautre)
        root.addWidget(self.canvasautre,1,2)

        #CORRELATIONS

        #control
        controls2D = QGridLayout(controls_corr)

        #variables
        self.var2D_x = QComboBox()
        self.var2D_y = QComboBox()
        nums = self._numeric_columns_candidates()
        self.var2D_x.addItems(nums)
        self.var2D_y.addItems(nums)

        years = sorted(self.df["Year"].dropna().unique().tolist()) if "Year" in self.df.columns else [2015, 2020]
        y_min = int(min(years)) if years else 2015
        y_max = int(max(years)) if years else 2020

        self.spin_year_max = QSpinBox()
        self.spin_year_max.setRange(y_min, y_max)
        self.spin_year_max.setValue(y_max)
        #self.spin_year_max.setReadOnly(True)

        #bouttons
        self.var2Dplot = QPushButton("Generer")
        self.var2Dplot.clicked.connect(self.plot2D)
        self.var2Dclean = QPushButton("Clean")
        #self.var2Dclean.connect(self.clean2D)
        self.var2Dsave = QPushButton("Save")
        #self.var2Dsave.connect(self.save2D)

        #layout

        controls2D.addWidget(QLabel("Axe X :"), 0, 0)
        controls2D.addWidget(self.var2D_x, 0, 1)
        controls2D.addWidget(QLabel("Axe Y :"), 1, 0)
        controls2D.addWidget(self.var2D_y, 1, 1)

        controls2D.addWidget(QLabel("Années :"), 2, 0)
        controls2D.addWidget(self.spin_year_max,2,1)

        controls2D.addWidget(self.var2Dplot,3,0)

    def plot2D(self):
            self.figurecorr.clear()
            self._plot_2d_scatter()
            self.figurecorr.tight_layout()
            self.canvascorr.draw()

    def _plot_2d_scatter(self):
        x = self.var2D_x.currentText()
        y = self.var2D_y.currentText()

        for col in [x, y]:
            if col not in self.df.columns:
                raise ValueError(f"Colonne '{col}' absente du dataset.")

        dff = self.df.dropna(subset=[x, y]).copy()

        # Nettoyage de la figure (important si redraw)
        self.figurecorr.clear()
        ax = self.figurecorr.add_subplot(111)

        if dff.empty:
            ax.set_title("Aucune donnée pour ce nuage 2D")
            return

        ax.scatter(dff[x].values, dff[y].values, s=20)
        ax.set_title(f"Nuage 2D — {x} vs {y}")
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.grid(True)

        # Si tu es dans Qt
        self.canvascorr.draw()













        #self._update_controls_visibility(self.cmb_graph.currentText())
        #self.plot()
    

    def _normalize_columns(self):
        if "year" in self.df.columns and "Year" not in self.df.columns:
            self.df.rename(columns={"year": "Year"}, inplace=True)
        if "country" in self.df.columns and "Country" not in self.df.columns:
            self.df.rename(columns={"country": "Country"}, inplace=True)

    def _ensure_types(self):
        if "Year" in self.df.columns:
            self.df["Year"] = pd.to_numeric(self.df["Year"], errors="coerce").astype("Int64")
        for c in self._numeric_columns_candidates():
            self.df[c] = pd.to_numeric(self.df[c], errors="coerce")

    def _numeric_columns_candidates(self):
        candidates = [
            "happiness_score", "gdp_per_capita", "health", "family", "freedom",
            "generosity", "government_trust", "dystopia_residual", "social_support",
            "cpi_score"
        ]
        return [c for c in candidates if c in self.df.columns]





