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


class StatsWidget(QWidget):
    """
    E5 : histogrammes / évolutions / 3D
    E6 : sauvegarde PNG
    + Comparatif multi-pays via menu déroulant multi-sélection (cases à cocher)
    """
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.df = df.copy()
        self.df.columns = self.df.columns.str.strip()

        self._normalize_columns()
        self._ensure_types()

        # ✅ Set des pays sélectionnés (via menu déroulant checkable)
        self.selected_countries = set()

        root = QVBoxLayout(self)
        root.setSpacing(10)

        # =========================
        # Controls
        # =========================
        controls_box = QGroupBox("Contrôles de graphiques")
        controls = QGridLayout(controls_box)
        controls.setHorizontalSpacing(10)
        controls.setVerticalSpacing(8)

        # Type de graphe
        self.cmb_graph = QComboBox()
        self.cmb_graph.addItems([
            "Histogramme par continent",
            "Évolution (bonheur + corruption) par pays",
            "Comparatif multi-pays (menu déroulant)",
            "Nuage de points 3D (corrélations)",
            "Nuage de points 2D"
        ])
        self.cmb_graph.currentTextChanged.connect(self._update_controls_visibility)

        # Variable (histo/3D)
        self.cmb_metric = QComboBox()
        self.cmb_metric.addItems(self._numeric_columns_candidates())




        # Continent (histo)
        self.cmb_continent = QComboBox()
        self.cmb_continent.addItem("Tous")
        if "continent" in self.df.columns:
            for c in sorted(self.df["continent"].dropna().unique().tolist()):
                self.cmb_continent.addItem(str(c))

        # Pays (évolution 1 pays)
        self.cmb_country = QComboBox()
        self.cmb_country.setEditable(True)
        countries = sorted(self.df["Country"].dropna().unique().tolist()) if "Country" in self.df.columns else []
        for c in countries:
            self.cmb_country.addItem(str(c))

        # ✅ Menu déroulant multi-sélection (cases)
        self.cmb_multi = QComboBox()
        self.cmb_multi.setEditable(False)
        self._multi_model = QStandardItemModel(self.cmb_multi)
        self.cmb_multi.setModel(self._multi_model)
        self._build_checkable_country_list(countries)

        # ✅ Fix toggle fiable : écouter itemChanged au lieu de pressed
        self._multi_model.itemChanged.connect(self._on_multi_item_changed)

        self.lbl_selected = QLabel("Sélection : (aucun)")
        self.lbl_selected.setStyleSheet("color:#555;")

        # Bouton clear
        self.btn_clear = QPushButton("Vider la sélection")
        self.btn_clear.clicked.connect(self.clear_selection)

        # Période
        years = sorted(self.df["Year"].dropna().unique().tolist()) if "Year" in self.df.columns else [2015, 2020]
        y_min = int(min(years)) if years else 2015
        y_max = int(max(years)) if years else 2020

        self.spin_year_min = QSpinBox()
        self.spin_year_max = QSpinBox()
        self.spin_year_min.setRange(y_min, y_max)
        self.spin_year_max.setRange(y_min, y_max)
        self.spin_year_min.setValue(y_min)
        self.spin_year_max.setValue(y_max)

        # 3D
        self.cmb_x = QComboBox()
        self.cmb_y = QComboBox()
        self.cmb_z = QComboBox()
        nums = self._numeric_columns_candidates()
        self.cmb_x.addItems(nums)
        self.cmb_y.addItems(nums)
        self.cmb_z.addItems(nums)

        
        #Variables (2D)
        self.var2D_x = QComboBox()
        self.var2D_x.addItems(self._numeric_columns_candidates())
        self.var2D_y = QComboBox()
        self.var2D_y.addItems(self._numeric_columns_candidates())

        # Boutons
        self.btn_plot = QPushButton("Générer")
        self.btn_plot.clicked.connect(self.plot)

        self.btn_save = QPushButton("Sauvegarder PNG")
        self.btn_save.clicked.connect(self.save_png)

        # Layout
        r = 0
        controls.addWidget(QLabel("Type :"), r, 0)
        controls.addWidget(self.cmb_graph, r, 1, 1, 3)
        r += 1

        controls.addWidget(QLabel("Variable (histo/3D) :"), r, 0)
        controls.addWidget(self.cmb_metric, r, 1)
        controls.addWidget(QLabel("Continent :"), r, 2)
        controls.addWidget(self.cmb_continent, r, 3)
        r += 1

        controls.addWidget(QLabel("Pays (évolution) :"), r, 0)
        controls.addWidget(self.cmb_country, r, 1)
        controls.addWidget(QLabel("Années :"), r, 2)
        years_box = QHBoxLayout()
        years_box.setContentsMargins(0, 0, 0, 0)
        years_box.addWidget(self.spin_year_min)
        years_box.addWidget(QLabel("→"))
        years_box.addWidget(self.spin_year_max)
        years_wrap = QWidget()
        years_wrap.setLayout(years_box)
        controls.addWidget(years_wrap, r, 3)
        r += 1

        controls.addWidget(QLabel("Comparatif (multi) :"), r, 0)
        controls.addWidget(self.cmb_multi, r, 1)
        controls.addWidget(self.btn_clear, r, 2)
        controls.addWidget(self.btn_plot, r, 3)
        r += 1

        controls.addWidget(self.lbl_selected, r, 0, 1, 4)
        r += 1

        controls.addWidget(QLabel("3D X :"), r, 0)
        controls.addWidget(self.cmb_x, r, 1)
        controls.addWidget(QLabel("3D Y :"), r, 2)
        controls.addWidget(self.cmb_y, r, 3)
        r += 1

        controls.addWidget(QLabel("3D Z :"), r, 0)
        controls.addWidget(self.cmb_z, r, 1)
        controls.addWidget(self.btn_save, r, 3)

        r += 1
        controls.addWidget(QLabel("2D X :"), r, 0)
        controls.addWidget(self.var2D_x, r, 1)
        controls.addWidget(QLabel("2D Y :"), r, 2)
        controls.addWidget(self.var2D_y, r, 3)

        root.addWidget(controls_box)

        # =========================
        # Figure
        # =========================
        self.figure = Figure(figsize=(7, 4), dpi=110)
        self.canvas = FigureCanvasQTAgg(self.figure)
        root.addWidget(self.canvas)

        self._update_controls_visibility(self.cmb_graph.currentText())
        self.plot()

    # -------------------------
    # Checkable combo helpers (FIX)
    # -------------------------
    def _build_checkable_country_list(self, countries):
        self._multi_model.blockSignals(True)
        self._multi_model.clear()

        ph = QStandardItem("Clique pour cocher plusieurs pays")
        ph.setFlags(Qt.ItemFlag.NoItemFlags)
        self._multi_model.appendRow(ph)

        for c in countries:
            it = QStandardItem(str(c))
            it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            it.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
            self._multi_model.appendRow(it)

        self._multi_model.blockSignals(False)
        self.cmb_multi.setCurrentIndex(0)

    def _on_multi_item_changed(self, item: QStandardItem):
        # ignore placeholder
        if item is None or item.flags() == Qt.ItemFlag.NoItemFlags:
            return

        country = item.text()
        checked = item.checkState() == Qt.CheckState.Checked

        if checked:
            self.selected_countries.add(country)
        else:
            self.selected_countries.discard(country)

        self._update_selected_label()

        if self.cmb_graph.currentText().startswith("Comparatif"):
            self.plot()

    def clear_selection(self):
        self.selected_countries.clear()

        self._multi_model.blockSignals(True)
        for r in range(1, self._multi_model.rowCount()):
            it = self._multi_model.item(r)
            if it:
                it.setCheckState(Qt.CheckState.Unchecked)
        self._multi_model.blockSignals(False)

        self._update_selected_label()
        if self.cmb_graph.currentText().startswith("Comparatif"):
            self.plot()

    def _update_selected_label(self):
        if not self.selected_countries:
            self.lbl_selected.setText("Sélection : (aucun)")
            return
        names = sorted(self.selected_countries)
        shown = ", ".join(names[:6])
        if len(names) > 6:
            shown += f" … (+{len(names)-6})"
        self.lbl_selected.setText(f"Sélection : {shown}")

    # -------------------------
    # Data prep
    # -------------------------
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

    # -------------------------
    # UI visibility
    # -------------------------
    def _update_controls_visibility(self, graph_type: str):
        is_histo = graph_type.startswith("Histogramme")
        is_evol = graph_type.startswith("Évolution")
        is_multi = graph_type.startswith("Comparatif")
        is_3d = graph_type.startswith("Nuage de points 3D")
        is_2d = graph_type.startswith("Nuage de points 2D")

        self.cmb_metric.setEnabled(is_histo or is_3d)
        self.cmb_continent.setEnabled(is_histo)

        self.var2D_y.setEnabled(is_2d)
        self.var2D_x.setEnabled(is_2d)


        self.cmb_country.setEnabled(is_evol)
        self.cmb_multi.setEnabled(is_multi)
        self.btn_clear.setEnabled(is_multi)

        self.spin_year_min.setEnabled(is_evol or is_multi)
        self.spin_year_max.setEnabled(is_evol or is_multi)

        self.cmb_x.setEnabled(is_3d)
        self.cmb_y.setEnabled(is_3d)
        self.cmb_z.setEnabled(is_3d)

    # -------------------------
    # Plot dispatcher
    # -------------------------
    def plot(self):
        graph_type = self.cmb_graph.currentText()
        self.figure.clear()

        try:
            if graph_type.startswith("Histogramme"):
                self._plot_hist_by_continent()
            elif graph_type.startswith("Évolution"):
                self._plot_evolution_country()
            elif graph_type.startswith("Comparatif"):
                self._plot_compare_multi()
            else:
                self._plot_3d_scatter()

            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            QMessageBox.critical(self, "Erreur graphique", f"Impossible de générer le graphique.\n\n{e}")

    # -------------------------
    # E5: Histogrammes
    # -------------------------
    def _plot_hist_by_continent(self):
        if "continent" not in self.df.columns:
            raise ValueError("Colonne 'continent' absente du dataset.")
        metric = self.cmb_metric.currentText()
        if metric not in self.df.columns:
            raise ValueError(f"Colonne '{metric}' absente du dataset.")

        continent_filter = self.cmb_continent.currentText()
        dff = self.df.dropna(subset=[metric, "continent"]).copy()
        if continent_filter != "Tous":
            dff = dff[dff["continent"] == continent_filter]

        ax = self.figure.add_subplot(111)
        if dff.empty:
            ax.set_title("Aucune donnée pour ces filtres")
            return

        if continent_filter == "Tous":
            for cont in sorted(dff["continent"].unique().tolist()):
                vals = dff.loc[dff["continent"] == cont, metric].dropna().values
                if len(vals) > 0:
                    ax.hist(vals, bins=15, alpha=0.5, label=str(cont))
            ax.legend(fontsize=8)
            ax.set_title(f"Distribution de {metric} par continent")
        else:
            ax.hist(dff[metric].dropna().values, bins=20)
            ax.set_title(f"Distribution de {metric} — {continent_filter}")

        ax.set_xlabel(metric)
        ax.set_ylabel("Nombre de pays (lignes)")

    # -------------------------
    # E5: Evolution 1 pays
    # -------------------------
    def _plot_evolution_country(self):
        if "Country" not in self.df.columns or "Year" not in self.df.columns:
            raise ValueError("Colonnes 'Country' et/ou 'Year' absentes du dataset.")
        if "happiness_score" not in self.df.columns or "cpi_score" not in self.df.columns:
            raise ValueError("Colonnes 'happiness_score' et/ou 'cpi_score' absentes du dataset.")

        country = self.cmb_country.currentText().strip()
        if not country:
            raise ValueError("Choisis un pays.")

        y1, y2 = int(self.spin_year_min.value()), int(self.spin_year_max.value())
        if y1 > y2:
            y1, y2 = y2, y1

        dff = self.df[(self.df["Country"] == country) & (self.df["Year"].between(y1, y2))].copy()
        dff = dff.dropna(subset=["Year"]).sort_values("Year")

        ax = self.figure.add_subplot(111)
        if dff.empty:
            ax.set_title(f"Aucune donnée pour {country} ({y1}-{y2})")
            return

        ax.plot(dff["Year"].astype(int).values, dff["happiness_score"].values, marker="o", label="happiness_score")
        ax.plot(dff["Year"].astype(int).values, dff["cpi_score"].values, marker="o", label="cpi_score")
        ax.set_title(f"Évolution — {country} ({y1}-{y2})")
        ax.set_xlabel("Année")
        ax.set_xticks(list(range(y1, y2 + 1)))
        ax.legend()

    # -------------------------
    # Comparatif multi-pays
    # -------------------------
    def _plot_compare_multi(self):
        if "Country" not in self.df.columns or "Year" not in self.df.columns:
            raise ValueError("Colonnes 'Country' et/ou 'Year' absentes du dataset.")
        if "happiness_score" not in self.df.columns or "cpi_score" not in self.df.columns:
            raise ValueError("Colonnes 'happiness_score' et/ou 'cpi_score' absentes du dataset.")

        y1, y2 = int(self.spin_year_min.value()), int(self.spin_year_max.value())
        if y1 > y2:
            y1, y2 = y2, y1

        countries = sorted(self.selected_countries)

        ax1 = self.figure.add_subplot(1, 2, 1)
        ax2 = self.figure.add_subplot(1, 2, 2)

        if not countries:
            ax1.set_title("Aucun pays sélectionné")
            ax2.set_title("Coche des pays dans le menu déroulant")
            ax1.set_xticks(list(range(y1, y2 + 1)))
            ax2.set_xticks(list(range(y1, y2 + 1)))
            return

        for c in countries:
            dff = self.df[(self.df["Country"] == c) & (self.df["Year"].between(y1, y2))].copy()
            dff = dff.dropna(subset=["Year"]).sort_values("Year")
            if dff.empty:
                continue
            years = dff["Year"].astype(int).values
            ax1.plot(years, dff["happiness_score"].values, marker="o", label=c)
            ax2.plot(years, dff["cpi_score"].values, marker="o", label=c)

        ax1.set_title("Évolution du bonheur")
        ax1.set_xlabel("Année")
        ax1.set_ylabel("happiness_score")
        ax1.set_xticks(list(range(y1, y2 + 1)))
        ax1.legend(fontsize=7)

        ax2.set_title("Évolution de la corruption (CPI)")
        ax2.set_xlabel("Année")
        ax2.set_ylabel("cpi_score")
        ax2.set_xticks(list(range(y1, y2 + 1)))
        ax2.legend(fontsize=7)

        self.figure.suptitle(f"Comparatif multi-pays ({y1}-{y2})")

    # -------------------------
    # E5: 3D
    # -------------------------
    def _plot_3d_scatter(self):
        x = self.cmb_x.currentText()
        y = self.cmb_y.currentText()
        z = self.cmb_z.currentText()

        for col in [x, y, z]:
            if col not in self.df.columns:
                raise ValueError(f"Colonne '{col}' absente du dataset.")

        dff = self.df.dropna(subset=[x, y, z]).copy()
        ax = self.figure.add_subplot(111, projection="3d")

        if dff.empty:
            ax.set_title("Aucune donnée pour ce nuage 3D")
            return

        ax.scatter(dff[x].values, dff[y].values, dff[z].values, s=20)
        ax.set_title(f"Nuage 3D — {x} vs {y} vs {z}")
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_zlabel(z)

    # -------------------------
    # E6: Save PNG
    # -------------------------
    def save_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder le graphique",
            "graph.png",
            "Images PNG (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"

        try:
            self.figure.savefig(path, format="png", dpi=200)
            QMessageBox.information(self, "OK", f"Graphique sauvegardé :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder.\n\n{e}")