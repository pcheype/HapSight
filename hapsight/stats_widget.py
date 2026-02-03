import matplotlib
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QWidget,
)

matplotlib.use("QtAgg")
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from scipy.stats import gaussian_kde
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class StatsWidget(QWidget):
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.df = df.copy()
        self.df.columns = self.df.columns.str.strip()

        self._normalize_columns()
        self._ensure_types()

        self.selected_countries = set()

        root = QGridLayout(self)
        root.setSpacing(10)

        controls_hist = QGroupBox("Histogrammes")
        controls_corr = QGroupBox("Corrélations")
        controls_autre = QGroupBox("Comparaisons")

        root.addWidget(controls_hist, 0, 0)
        root.addWidget(controls_corr, 0, 1)
        root.addWidget(controls_autre, 0, 2)

        self.figurehist = Figure(figsize=(4, 4), dpi=110)
        self.canvashist = FigureCanvasQTAgg(self.figurehist)
        root.addWidget(self.canvashist, 1, 0)

        self.figurecorr = Figure(figsize=(4, 4), dpi=110)
        self.canvascorr = FigureCanvasQTAgg(self.figurecorr)
        root.addWidget(self.canvascorr, 1, 1)

        self.figureautre = Figure(figsize=(4, 4), dpi=110)
        self.canvasautre = FigureCanvasQTAgg(self.figureautre)
        root.addWidget(self.canvasautre, 1, 2)

        # CORRELATIONS

        # control
        controls2D = QGridLayout(controls_corr)

        # variables
        self.var2D_x = QComboBox()
        self.var2D_y = QComboBox()
        nums = self._numeric_columns_candidates()
        self.var2D_x.addItems(nums)
        self.var2D_y.addItems(nums)

        years = (
            sorted(self.df["Year"].dropna().unique().tolist())
            if "Year" in self.df.columns
            else [2015, 2020]
        )
        y_min = int(min(years)) if years else 2015
        y_max = int(max(years)) if years else 2020

        self.spin_year_max = QSpinBox()
        self.spin_year_max.setRange(y_min, y_max)
        self.spin_year_max.setValue(y_max)
        # self.spin_year_max.setReadOnly(True)

        # bouttons
        self.var2Dplot = QPushButton("Generer")
        self.var2Dplot.clicked.connect(self.plot2D)
        self.var2Dsave = QPushButton("Save")
        self.var2Dsave.clicked.connect(self.save_png)

        self.var2Danalyse = QPushButton("Analyse")
        self.var2Danalyse.clicked.connect(self._apply_clustering)

        self.nbcluster = QSpinBox()
        self.nbcluster.setRange(1, 5)
        self.nbcluster.setValue(3)

        # layout

        controls2D.addWidget(QLabel("Axe X :"), 0, 0)
        controls2D.addWidget(self.var2D_x, 0, 1)
        controls2D.addWidget(QLabel("Axe Y :"), 1, 0)
        controls2D.addWidget(self.var2D_y, 1, 1)

        controls2D.addWidget(QLabel("Années :"), 2, 0)
        controls2D.addWidget(self.spin_year_max, 2, 1)

        controls2D.addWidget(self.var2Dplot, 3, 0)
        controls2D.addWidget(self.var2Dsave, 3, 1)

        controls2D.addWidget(QLabel("Nombre de clusters :"), 4, 0)
        controls2D.addWidget(self.nbcluster, 4, 1)

        controls2D.addWidget(self.var2Danalyse, 5, 0, 1, 2)

        # HISTOGRAMMES
        # control
        controlshist = QGridLayout(controls_hist)

        # variables
        self.varhist = QComboBox()
        self.varcontinent = QComboBox()
        self.varcontinent.addItem("Tous")
        if "continent" in self.df.columns:
            for c in sorted(self.df["continent"].dropna().unique().tolist()):
                self.varcontinent.addItem(str(c))

        nums = self._numeric_columns_candidates()
        self.varhist.addItems(nums)

        self.spinhist_year_max = QSpinBox()
        self.spinhist_year_max.setRange(y_min, y_max)
        self.spinhist_year_max.setValue(y_max)

        # bouttons
        self.varhistplot = QPushButton("Generer")
        self.varhistplot.clicked.connect(self.plothist)
        self.varhistsave = QPushButton("Save")
        self.varhistsave.clicked.connect(self.savehist_png)

        self.varhistanalyse = QPushButton("Analyse")
        self.varhistanalyse.clicked.connect(self._analyze_histogram)
        # layout

        controlshist.addWidget(QLabel("Variable :"), 0, 0)
        controlshist.addWidget(self.varhist, 0, 1)
        controlshist.addWidget(QLabel("Continent :"), 1, 0)
        controlshist.addWidget(self.varcontinent, 1, 1)

        controlshist.addWidget(QLabel("Années :"), 2, 0)
        controlshist.addWidget(self.spinhist_year_max, 2, 1)

        controlshist.addWidget(self.varhistplot, 3, 0)
        controlshist.addWidget(self.varhistsave, 3, 1)
        controlshist.addWidget(self.varhistanalyse, 4, 0, 1, 2)

        # COMPARATIF MULTIPAYS
        # control
        controlscomp = QGridLayout(controls_autre)

        self.cmb_multi = QComboBox()
        self.cmb_multi.setEditable(False)
        self._multi_model = QStandardItemModel(self.cmb_multi)
        self.cmb_multi.setModel(self._multi_model)
        countries = (
            sorted(self.df["Country"].dropna().unique().tolist())
            if "Country" in self.df.columns
            else []
        )
        self._build_checkable_country_list(countries)

        self._multi_model.itemChanged.connect(self.update_multi_plot)

        # variables
        self.varcomp = QComboBox()
        nums = self._numeric_columns_candidates()
        self.varcomp.addItems(nums)

        # bouttons
        self.varcompclear = QPushButton("Clear")
        self.varcompclear.clicked.connect(self.clear_multi_selection)
        self.varcompsave = QPushButton("Save")
        self.varcompsave.clicked.connect(self.savecomp_png)

        # layout

        controlscomp.addWidget(QLabel("Variable :"), 0, 0)
        controlscomp.addWidget(self.varcomp, 0, 1)
        controlscomp.addWidget(QLabel("Pays :"), 1, 0)
        controlscomp.addWidget(self.cmb_multi, 1, 1)

        controlscomp.addWidget(self.varcompclear, 2, 0)
        controlscomp.addWidget(self.varcompsave, 2, 1)

    def update_multi_plot(self, item=None):
        "Update le plot lorsque l'on coche une nouvelle case"

        checked_countries = []
        for index in range(self._multi_model.rowCount()):
            item = self._multi_model.item(index)
            if item.checkState() == Qt.Checked:  # type: ignore
                checked_countries.append(item.text())

        variable = self.varcomp.currentText()
        if not variable or not checked_countries:
            self.canvasautre.figure.clear()
            self.canvasautre.draw()
            return

        self.canvasautre.figure.clear()
        ax = self.canvasautre.figure.add_subplot(111)

        for country in checked_countries:
            df_subset = self.df[self.df["Country"] == country]
            if "Year" in df_subset.columns:
                df_subset = df_subset.sort_values("Year")
                x_data = df_subset["Year"]
            else:
                x_data = range(len(df_subset))

            y_data = df_subset[variable]

            ax.plot(x_data, y_data, label=country, marker="o")

        ax.set_title(f"Évolution de {variable}")
        ax.set_xlabel("Année")
        ax.set_ylabel(variable)
        ax.legend()
        ax.grid(True)
        self.canvasautre.draw()

    def clear_multi_selection(self):
        "Décoche tous les pays + nettoie le canvas"
        for index in range(self._multi_model.rowCount()):
            item = self._multi_model.item(index)
            item.setCheckState(Qt.Unchecked)  # type: ignore
        self.update_multi_plot()

    def plot2D(self):
        "Permet le plot 2D"
        self.figurecorr.clear()
        self._plot_2d_scatter()
        self.figurecorr.tight_layout()
        self.canvascorr.draw()

    def plothist(self):
        "Permet le plot des hists"
        self.figurehist.clear()
        self._plot_hist_scatter()
        self.figurecorr.tight_layout()
        self.canvascorr.draw()

    def _plot_hist_scatter(self):
        "Fonction du plot des hists"
        var = self.varhist.currentText()
        continent_filter = self.varcontinent.currentText()
        year = self.spinhist_year_max.value()

        col_cont = "Continent"

        if col_cont not in self.df.columns:
            if "continent" in self.df.columns:
                col_cont = "continent"
            else:
                self.figurehist.clear()
                self.ax = self.figurehist.add_subplot(111)
                self.ax.text(0.5, 0.5, "Colonne Continent introuvable", ha="center")
                self.canvashist.draw()
                return

        dff = self.df[self.df["Year"] == year].dropna(subset=[var]).copy()
        self.figurehist.clear()
        self.ax = self.figurehist.add_subplot(111)

        if continent_filter == "Tous":
            self.dff_currenthist = dff

            if dff.empty:
                self.ax.set_title(f"Aucune donnée pour {year}")
            else:
                continents_disponibles = sorted(
                    dff[col_cont].dropna().unique().tolist()
                )

                for cont in continents_disponibles:
                    vals = dff.loc[dff[col_cont] == cont, var].values  # type: ignore
                    if len(vals) > 0:
                        self.ax.hist(vals, bins="auto", alpha=0.5, label=str(cont))

                self.ax.set_title(f"Distribution de '{var}'\npar Continent ({year})")
                self.ax.legend(title="Continent", fontsize="small")

        else:
            dff_single = dff[dff[col_cont] == continent_filter]
            self.dff_currenthist = dff_single

            if dff_single.empty:
                self.ax.text(
                    0.5,
                    0.5,
                    f"Pas de données pour\n{continent_filter} en {year}",
                    ha="center",
                    va="center",
                )
            else:
                self.ax.hist(
                    dff_single[var].values.astype(float),
                    bins="auto",
                    color="#0077c1",  # type: ignore
                    edgecolor="black",
                    alpha=0.7,
                )

                mean_val = dff_single[var].mean()
                self.ax.axvline(
                    mean_val,
                    color="red",
                    linestyle="dashed",
                    linewidth=1.5,
                    label=f"Moyenne: {mean_val:.2f}",
                )
                self.ax.legend()
                self.ax.set_title(
                    f"Distribution de '{var}'\n{continent_filter} ({year})"
                )

        self.ax.set_xlabel(var)
        self.ax.set_ylabel("Nombre de pays")
        self.ax.grid(axis="y", linestyle="--", alpha=0.5)

        self.canvashist.draw()

    def _plot_2d_scatter(self):
        "Fonction qui effectue le plot 2D"
        x_col = self.var2D_x.currentText()
        y_col = self.var2D_y.currentText()
        year = self.spin_year_max.value()

        self.dff_current = (
            self.df[self.df["Year"] == year].dropna(subset=[x_col, y_col]).copy()
        )

        self.figurecorr.clear()
        self.ax = self.figurecorr.add_subplot(111)

        if self.dff_current.empty:
            self.ax.set_title(f"Aucune donnée pour l'année {year}")
            self.canvascorr.draw()
            return

        self.scatter = self.ax.scatter(
            self.dff_current[x_col].values,  # type: ignore
            self.dff_current[y_col].values,  # type: ignore
            s=30,
            picker=10,
            alpha=0.7,
        )

        self.ax.set_title(f"{x_col} vs {y_col}\n(année {year})", fontsize=12)
        self.ax.set_xlabel(x_col)
        self.ax.set_ylabel(y_col)
        self.ax.grid(True)

        self.annot = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
            arrowprops=dict(arrowstyle="->"),
        )
        self.annot.set_visible(False)

        if hasattr(self, "_cid"):
            self.canvascorr.mpl_disconnect(self._cid)

        self._cid = self.canvascorr.mpl_connect("pick_event", self._on_pick)

        self.canvascorr.draw()

    def _apply_clustering(self):
        "Permet le clustering sur le plot 2D"
        if not hasattr(self, "dff_current") or self.dff_current.empty:
            return

        x_col = self.var2D_x.currentText()
        y_col = self.var2D_y.currentText()

        X = self.dff_current[[x_col, y_col]].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        n_clusters = self.nbcluster.value()
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        self.dff_current["Cluster"] = kmeans.fit_predict(X_scaled)

        self.figurecorr.clear()
        self.ax = self.figurecorr.add_subplot(111)

        colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#1A535C", "#556270"]

        self.cluster_map = {}
        self.scatter = None

        for i in range(n_clusters):
            sub_df = self.dff_current[self.dff_current["Cluster"] == i]

            sc = self.ax.scatter(
                sub_df[x_col],
                sub_df[y_col],
                s=30,
                c=colors[i % len(colors)],
                label=f"Grp {i + 1}",
                picker=5,
                alpha=0.8,
                edgecolors="white",
                linewidth=0.5,
            )
            self.cluster_map[sc] = sub_df

        leg = self.ax.legend(
            title="Clusters",
            fontsize="8",
            title_fontsize="9",
            loc="best",
            framealpha=0.7,
        )
        leg.set_draggable(True)

        self.ax.set_title(f"Clustering : {x_col} vs {y_col}", fontsize=10)
        self.ax.set_xlabel(x_col)
        self.ax.set_ylabel(y_col)
        self.ax.grid(True, linestyle="--", alpha=0.3)

        self.annot = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="white", ec="gray", alpha=0.9),
            arrowprops=dict(arrowstyle="->"),
        )
        self.annot.set_visible(False)

        self.canvascorr.draw()

    def _analyze_histogram(self):
        "Outil d'analyse de l'histogramme"
        if not hasattr(self, "dff_currenthist") or self.dff_currenthist.empty:
            return

        var = self.varhist.currentText()
        data = self.dff_currenthist[var].dropna().values

        density = gaussian_kde(data)
        xs = np.linspace(data.min(), data.max(), 200)  # type: ignore

        ax2 = self.ax.twinx()
        ax2.plot(
            xs,
            density(xs),
            color="#D2A7FE",
            linewidth=1.5,
            linestyle="-",
            label="Densité",
        )  # type: ignore
        ax2.set_yticks([])

        mean = np.mean(data)  # type: ignore
        std = np.std(data)  # type: ignore

        threshold = 2 * std
        outliers_df = self.dff_currenthist[
            np.abs(self.dff_currenthist[var] - mean) > threshold
        ]

        self.ax.axvline(mean - threshold, color="orange", linestyle=":", alpha=0.2)
        self.ax.axvline(mean + threshold, color="orange", linestyle=":", alpha=0.2)

        if not outliers_df.empty:
            lows = outliers_df[outliers_df[var] < mean].sort_values(var).head(3)
            highs = (
                outliers_df[outliers_df[var] > mean]
                .sort_values(var, ascending=False)
                .head(3)
            )

            txt_list = []
            if not highs.empty:
                names = [
                    row.get("Entity", row.get("Country", "?"))
                    for _, row in highs.iterrows()
                ]
                txt_list.append(f"positif : {', '.join(names)}")

            if not lows.empty:
                names = [
                    row.get("Entity", row.get("Country", "?"))
                    for _, row in lows.iterrows()
                ]
                txt_list.append(f"négatif: {', '.join(names)}")

            full_txt = "Outliers :\n" + "\n".join(txt_list)

            self.ax.text(
                0.02,
                0.95,
                full_txt,
                transform=self.ax.transAxes,
                fontsize=9,
                verticalalignment="top",
                bbox=dict(
                    boxstyle="square", facecolor="#FAFAFA", edgecolor="black", alpha=0.5
                ),
            )
        else:
            self.ax.text(
                0.02,
                0.95,
                "Distribution très homogène\n(Pas d'anomalies détectées)",
                transform=self.ax.transAxes,
                bbox=dict(boxstyle="square", facecolor="#E8F5E9", alpha=0.9),
            )

        ax2.legend(loc="upper right")  # type: ignore

        self.ax.set_title(f"Analyse de Distribution : {var}", fontsize=11)
        self.canvashist.draw()

    def _on_pick(self, event):
        "Permet de pick un point du nuage 2D"
        if hasattr(self, "cluster_map") and event.artist in self.cluster_map:
            target_df = self.cluster_map[event.artist]

        elif hasattr(self, "scatter") and event.artist == self.scatter:
            target_df = self.dff_current

        else:
            return

        # --- Récupération des infos ---
        ind = event.ind[0]

        # On utilise target_df (le bon morceau de données) et non dff_current entier
        row = target_df.iloc[ind]

        country = row.get("Entity", row.get("Country", "Inconnu"))
        x_val = row[self.var2D_x.currentText()]
        y_val = row[self.var2D_y.currentText()]

        # Affichage de la bulle
        pos = event.artist.get_offsets()[ind]
        self.annot.xy = pos

        # Logique pour éviter que la bulle sorte du cadre
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        x_offset = -80 if pos[0] > (xlim[0] + xlim[1]) / 2 else 15
        y_offset = -40 if pos[1] > (ylim[0] + ylim[1]) / 2 else 15
        self.annot.set_position((x_offset, y_offset))

        # Texte de l'annotation
        cluster_txt = ""
        if "Cluster" in row:
            cluster_txt = f"\nGroupe: {row['Cluster'] + 1}"

        self.annot.set_text(f"{country}\n({x_val:.2f}, {y_val:.2f}){cluster_txt}")
        self.annot.set_visible(True)

        self.canvascorr.draw_idle()

    def save_png(self):
        "Peremt de save le canvas 2D"
        path, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder le graphique", "graph.png", "Images PNG (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"

        try:
            self.figurecorr.savefig(path, format="png", dpi=200)
            QMessageBox.information(self, "OK", f"Graphique sauvegardé :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder.\n\n{e}")

    def savehist_png(self):
        "Permet de save le canvas des hist"
        path, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder le graphique", "graph.png", "Images PNG (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"

        try:
            self.figurehist.savefig(path, format="png", dpi=200)
            QMessageBox.information(self, "OK", f"Graphique sauvegardé :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder.\n\n{e}")

    def savecomp_png(self):
        "Permet de save le canvas des comparaisons"
        path, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder le graphique", "graph.png", "Images PNG (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"

        try:
            self.figureautre.savefig(path, format="png", dpi=200)
            QMessageBox.information(self, "OK", f"Graphique sauvegardé :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder.\n\n{e}")

    def _normalize_columns(self):
        "Permet de normaliser les colonnes"
        if "year" in self.df.columns and "Year" not in self.df.columns:
            self.df.rename(columns={"year": "Year"}, inplace=True)
        if "country" in self.df.columns and "Country" not in self.df.columns:
            self.df.rename(columns={"country": "Country"}, inplace=True)

    def _ensure_types(self):
        if "Year" in self.df.columns:
            self.df["Year"] = pd.to_numeric(self.df["Year"], errors="coerce").astype(
                "Int64"
            )
        for c in self._numeric_columns_candidates():
            self.df[c] = pd.to_numeric(self.df[c], errors="coerce")

    def _numeric_columns_candidates(self):
        candidates = [
            "happiness_score",
            "gdp_per_capita",
            "health",
            "family",
            "freedom",
            "generosity",
            "government_trust",
            "dystopia_residual",
            "social_support",
            "cpi_score",
        ]
        return [c for c in candidates if c in self.df.columns]

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
