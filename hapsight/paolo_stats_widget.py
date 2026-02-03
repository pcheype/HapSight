import pandas as pd
from scipy import stats
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

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np

from scipy.stats import gaussian_kde

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
        controls_autre = QGroupBox("Comparaisons")

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
        self.var2Dsave = QPushButton("Save")
        self.var2Dsave.clicked.connect(self.save_png)

        self.var2Danalyse = QPushButton("Analyse")
        self.var2Danalyse.clicked.connect(self._apply_clustering)

        self.nbcluster = QSpinBox()
        self.nbcluster.setRange(1,5)
        self.nbcluster.setValue(3)

        #layout

        controls2D.addWidget(QLabel("Axe X :"), 0, 0)
        controls2D.addWidget(self.var2D_x, 0, 1)
        controls2D.addWidget(QLabel("Axe Y :"), 1, 0)
        controls2D.addWidget(self.var2D_y, 1, 1)

        controls2D.addWidget(QLabel("Années :"), 2, 0)
        controls2D.addWidget(self.spin_year_max,2,1)

        controls2D.addWidget(self.var2Dplot,3,0)
        controls2D.addWidget(self.var2Dsave,3,1)

        controls2D.addWidget(QLabel("Nombre de clusters :"), 4, 0)
        controls2D.addWidget(self.nbcluster,4,1)

        controls2D.addWidget(self.var2Danalyse,5,0,1,2)




        #HISTOGRAMMES
        #control
        controlshist = QGridLayout(controls_hist)

        #variables
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

        #bouttons
        self.varhistplot = QPushButton("Generer")
        self.varhistplot.clicked.connect(self.plothist)
        self.varhistsave = QPushButton("Save")
        self.varhistsave.clicked.connect(self.savehist_png)

        self.varhistanalyse = QPushButton("Analyse")
        self.varhistanalyse.clicked.connect(self._analyze_histogram)
        #layout

        controlshist.addWidget(QLabel("Variable :"), 0, 0)
        controlshist.addWidget(self.varhist, 0, 1)
        controlshist.addWidget(QLabel("Continent :"), 1, 0)
        controlshist.addWidget(self.varcontinent, 1, 1)

        controlshist.addWidget(QLabel("Années :"), 2, 0)
        controlshist.addWidget(self.spinhist_year_max,2,1)

        controlshist.addWidget(self.varhistplot,3,0)
        controlshist.addWidget(self.varhistsave,3,1)
        controlshist.addWidget(self.varhistanalyse,4,0,1,2)

        #COMPARATIF MULTIPAYS
        #control
        controlscomp = QGridLayout(controls_autre)

        self.cmb_multi = QComboBox()
        self.cmb_multi.setEditable(False)
        self._multi_model = QStandardItemModel(self.cmb_multi)
        self.cmb_multi.setModel(self._multi_model)
        countries = sorted(self.df["Country"].dropna().unique().tolist()) if "Country" in self.df.columns else []
        self._build_checkable_country_list(countries)

        #variables
        self.varcomp = QComboBox()
        nums = self._numeric_columns_candidates()
        self.varcomp.addItems(nums)

        #bouttons
        self.varcompclear = QPushButton("Clear")
        #self.varcompclear.clicked.connect(self.varcompclear)
        self.varcompsave = QPushButton("Save")
        #self.varcompsave.clicked.connect(self.savecomp_png)

        #layout

        controlscomp.addWidget(QLabel("Variable :"), 0, 0)
        controlscomp.addWidget(self.varcomp, 0, 1)
        controlscomp.addWidget(QLabel("Pays :"), 1, 0)
        controlscomp.addWidget(self.cmb_multi, 1, 1)

        controlscomp.addWidget(self.varcompclear,2,0)
        controlscomp.addWidget(self.varcompsave,2,1)


    def plot2D(self):
            self.figurecorr.clear()
            self._plot_2d_scatter()
            self.figurecorr.tight_layout()
            self.canvascorr.draw()
    
    def plothist(self):
            self.figurehist.clear()
            self._plot_hist_scatter()
            self.figurecorr.tight_layout()
            self.canvascorr.draw()

    def _plot_hist_scatter(self):
        var = self.varhist.currentText()
        continent_filter = self.varcontinent.currentText()
        year = self.spinhist_year_max.value()
        
        # Nom de la colonne continent
        col_cont = "Continent" 

        # 1. Vérification des colonnes
        if col_cont not in self.df.columns:
            if "continent" in self.df.columns:
                col_cont = "continent"
            else:
                self.figurehist.clear()
                self.ax = self.figurehist.add_subplot(111)
                self.ax.text(0.5, 0.5, "Colonne Continent introuvable", ha='center')
                self.canvashist.draw()
                return

        # 2. Filtrage de base (Année + Variable numérique)
        dff = self.df[self.df["Year"] == year].dropna(subset=[var]).copy()

        # Nettoyage de la figure
        self.figurehist.clear()
        self.ax = self.figurehist.add_subplot(111)

        # 3. Logique selon le filtre "Tous" ou spécifique
        if continent_filter == "Tous":
            # --- IMPORTANT : On sauvegarde les données visibles pour l'analyse ---
            self.dff_currenthist = dff 
            
            if dff.empty:
                self.ax.set_title(f"Aucune donnée pour {year}")
            else:
                continents_disponibles = sorted(dff[col_cont].dropna().unique().tolist())
                
                for cont in continents_disponibles:
                    vals = dff.loc[dff[col_cont] == cont, var].values
                    if len(vals) > 0:
                        self.ax.hist(vals, bins='auto', alpha=0.5, label=str(cont))
                
                self.ax.set_title(f"Distribution de '{var}' par Continent ({year})")
                self.ax.legend(title="Continent", fontsize='small')

        else:
            # Cas d'un continent spécifique
            dff_single = dff[dff[col_cont] == continent_filter]
            
            # --- IMPORTANT : On sauvegarde UNIQUEMENT ce continent pour l'analyse ---
            self.dff_currenthist = dff_single

            if dff_single.empty:
                self.ax.text(0.5, 0.5, f"Pas de données pour\n{continent_filter} en {year}", 
                            ha='center', va='center')
            else:
                self.ax.hist(dff_single[var].values, bins='auto', color="#0077c1", 
                            edgecolor='black', alpha=0.7)
                
                mean_val = dff_single[var].mean()
                self.ax.axvline(mean_val, color='red', linestyle='dashed', 
                                linewidth=1.5, label=f'Moyenne: {mean_val:.2f}')
                self.ax.legend()
                self.ax.set_title(f"Distribution de '{var}'\n{continent_filter} ({year})")

        # 4. Finalisation
        self.ax.set_xlabel(var)
        self.ax.set_ylabel("Nombre de pays")
        self.ax.grid(axis='y', linestyle='--', alpha=0.5)

        self.canvashist.draw()

    def _plot_2d_scatter(self):
        x_col = self.var2D_x.currentText()
        y_col = self.var2D_y.currentText()
        year = self.spin_year_max.value()

        # Détection de la colonne pays
        country_col = "Entity" if "Entity" in self.df.columns else "Country"
        
        self.dff_current = self.df[self.df["Year"] == year].dropna(subset=[x_col, y_col]).copy()

        self.figurecorr.clear()
        self.ax = self.figurecorr.add_subplot(111)

        if self.dff_current.empty:
            self.ax.set_title(f"Aucune donnée pour l'année {year}")
            self.canvascorr.draw()
            return

        # On augmente picker à 10 pour faciliter le clic
        self.scatter = self.ax.scatter(
            self.dff_current[x_col].values, 
            self.dff_current[y_col].values, 
            s=30, 
            picker=10, 
            alpha=0.7
        )

        self.ax.set_title(f"{x_col} vs {y_col}\n(année {year})", fontsize=12)
        self.ax.set_xlabel(x_col)
        self.ax.set_ylabel(y_col)
        self.ax.grid(True)

        # Création de l'annotation
        self.annot = self.ax.annotate(
            "", xy=(0,0), xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="white", ec="black", alpha=0.8),
            arrowprops=dict(arrowstyle="->")
        )
        self.annot.set_visible(False)

        # IMPORTANCE : On ne connecte l'événement qu'une seule fois si possible
        # Pour éviter d'empiler les connexions, on peut déconnecter l'ancienne
        if hasattr(self, '_cid'):
            self.canvascorr.mpl_disconnect(self._cid)
        
        self._cid = self.canvascorr.mpl_connect('pick_event', self._on_pick)
        
        self.canvascorr.draw()
    
    def _apply_clustering(self):
        # 1. Vérifications d'usage
        if not hasattr(self, 'dff_current') or self.dff_current.empty:
            return

        x_col = self.var2D_x.currentText()
        y_col = self.var2D_y.currentText()
        
        # Préparation des données
        X = self.dff_current[[x_col, y_col]].values
        
        # Import local pour éviter les soucis si pas en haut du fichier
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 2. Clustering
        n_clusters = self.nbcluster.value()
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.dff_current["Cluster"] = kmeans.fit_predict(X_scaled)

        # 3. Nettoyage et préparation graphique
        self.figurecorr.clear()
        self.ax = self.figurecorr.add_subplot(111)

        colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#1A535C', '#556270']
        
        # --- ASTUCE POUR LE CLIC ---
        # On va stocker ici le lien entre "l'objet graphique" et "les données de ce groupe"
        self.cluster_map = {} 
        # On vide self.scatter pour éviter que _on_pick ne s'embrouille
        self.scatter = None 

        for i in range(n_clusters):
            # On filtre les données de ce groupe spécifique
            sub_df = self.dff_current[self.dff_current["Cluster"] == i]
            
            # On trace ce groupe
            sc = self.ax.scatter(
                sub_df[x_col], 
                sub_df[y_col], 
                s=30, 
                c=colors[i % len(colors)],
                label=f'Grp {i+1}', # Légende courte
                picker=5, # INDISPENSABLE pour le clic
                alpha=0.8,
                edgecolors='white',
                linewidth=0.5
            )
            
            # On enregistre le lien : Cet objet 'sc' -> Ce dataframe 'sub_df'
            self.cluster_map[sc] = sub_df

        # 4. Gestion de la Légende (Plus petite et draggable)
        leg = self.ax.legend(
            title="Clusters", 
            fontsize='8',           # Police petite
            title_fontsize='9', 
            loc='best',             # Matplotlib cherche la place libre
            framealpha=0.7          # Un peu transparent
        )
        leg.set_draggable(True)     # <--- SUPER UTILE : Tu peux bouger la légende à la souris !

        # Esthétique globale
        self.ax.set_title(f"Clustering : {x_col} vs {y_col}", fontsize=10)
        self.ax.set_xlabel(x_col)
        self.ax.set_ylabel(y_col)
        self.ax.grid(True, linestyle='--', alpha=0.3)

        # Réinitialisation de l'annotation (bulle d'info)
        self.annot = self.ax.annotate(
            "", xy=(0,0), xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="white", ec="gray", alpha=0.9),
            arrowprops=dict(arrowstyle="->")
        )
        self.annot.set_visible(False)
        
        self.canvascorr.draw()

    def _analyze_histogram(self):
        # 1. Vérification
        if not hasattr(self, 'dff_currenthist') or self.dff_currenthist.empty:
            return

        var = self.varhist.currentText()
        data = self.dff_currenthist[var].dropna().values
        
        # Si trop peu de données, l'analyse ne vaut rien
        if len(data) < 5:
            return

        # --- PARTIE 1 : Courbe de Densité (KDE) ---
        # On crée une fonction de densité basée sur les données
        density = gaussian_kde(data)
        
        # On génère des points x pour tracer la courbe (du min au max)
        xs = np.linspace(data.min(), data.max(), 200)
        
        # On calcule density(xs). Attention: l'aire sous la courbe = 1.
        # L'histogramme a une aire = nombre de pays * largeur de barre.
        # Pour superposer, le plus simple est de tracer la courbe sur un axe jumeau (twinx)
        # ou de simplement normaliser l'affichage. 
        # Ici, solution simple : Axe secondaire pour la courbe (esthétique)
        
        ax2 = self.ax.twinx() # Crée un axe Y à droite
        ax2.plot(xs, density(xs), color='#FF6B6B', linewidth=1.5, linestyle='-', label='Densité (KDE)')
        ax2.set_yticks([]) # On cache les chiffres de l'axe de droite (peu utiles)
        
        # --- PARTIE 2 : Détection des Outliers (Z-Score) ---
        mean = np.mean(data)
        std = np.std(data)
        
        # Seuil : Est considéré comme outlier ce qui est à > 2 écarts-types
        threshold = 2 * std
        outliers_df = self.dff_currenthist[np.abs(self.dff_currenthist[var] - mean) > threshold]
        
        # On trace les lignes verticales pour montrer la zone "normale"
        self.ax.axvline(mean - threshold, color='orange', linestyle=':', alpha=0.8)
        self.ax.axvline(mean + threshold, color='orange', linestyle=':', alpha=0.8)

        # --- PARTIE 3 : Affichage des pays "Spéciaux" ---
        if not outliers_df.empty:
            # On récupère les noms (Top 3 min et Top 3 max pour ne pas surcharger)
            lows = outliers_df[outliers_df[var] < mean].sort_values(var).head(3)
            highs = outliers_df[outliers_df[var] > mean].sort_values(var, ascending=False).head(3)
            
            txt_list = []
            if not highs.empty:
                names = [row.get("Entity", row.get("Country", "?")) for _, row in highs.iterrows()]
                txt_list.append(f"↑ Hauts : {', '.join(names)}")
            
            if not lows.empty:
                names = [row.get("Entity", row.get("Country", "?")) for _, row in lows.iterrows()]
                txt_list.append(f"↓ Bas : {', '.join(names)}")
                
            full_txt = "Outliers :\n" + "\n".join(txt_list)
            
            # Affichage dans une boite
            self.ax.text(
                0.02, 0.95, full_txt, 
                transform=self.ax.transAxes, 
                fontsize=9, 
                verticalalignment='top',
                bbox=dict(boxstyle="round", facecolor='#FFF8E1', edgecolor='orange', alpha=0.9)
            )
        else:
            # Si aucun outlier
            self.ax.text(
                0.02, 0.95, "Distribution très homogène\n(Pas d'anomalies détectées)", 
                transform=self.ax.transAxes,
                bbox=dict(boxstyle="round", facecolor='#E8F5E9', alpha=0.9)
            )

        # Ajout de la légende pour la courbe
        ax2.legend(loc='upper right')
        
        self.ax.set_title(f"Analyse de Distribution : {var}", fontsize=11)
        self.canvashist.draw()

    def _on_pick(self, event):
        # Cas 1 : Clic sur un clustering (via cluster_map)
        if hasattr(self, 'cluster_map') and event.artist in self.cluster_map:
            # On récupère le bon sous-dataframe associé à ce groupe de points
            target_df = self.cluster_map[event.artist]
        
        # Cas 2 : Clic sur un nuage de points simple (sans clustering)
        elif hasattr(self, 'scatter') and event.artist == self.scatter:
            target_df = self.dff_current
            
        else:
            return # Ce n'est pas un événement qui nous intéresse

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
            self.figurecorr.savefig(path, format="png", dpi=200)
            QMessageBox.information(self, "OK", f"Graphique sauvegardé :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder.\n\n{e}")

    def savehist_png(self):
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
            self.figurehist.savefig(path, format="png", dpi=200)
            QMessageBox.information(self, "OK", f"Graphique sauvegardé :\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder.\n\n{e}")













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


