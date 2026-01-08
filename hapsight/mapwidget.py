import sys
import os
import io
import requests
import pycountry

# --- 1. CONFIGURATION MATPLOTLIB ---
import matplotlib
matplotlib.use('QtAgg') # Obligatoire pour PySide6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import folium
import pandas as pd

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QGroupBox, QFrame, QComboBox
)

class MapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Mémorisation du pays sélectionné (pour quand on change d'année)
        self.pays_actuel = None 

        # --- CHARGEMENT DES DONNÉES ---
        self.data_happiness = None
        self.load_csv_data()

        # --- LAYOUT PRINCIPAL ---
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # =========================================================
        # PARTIE GAUCHE : CARTE (Folium)
        # =========================================================
        self.cartegroupbox = QGroupBox()
        self.cartegroupbox.setStyleSheet("QGroupBox { border: 1px solid #CCC; border-radius: 5px; }")
        carte_layout = QVBoxLayout()
        carte_layout.setContentsMargins(1, 1, 1, 1)
        
        self.web_view = QWebEngineView()
        self.web_view.titleChanged.connect(self.on_country_clicked)
        
        carte_layout.addWidget(self.web_view)
        self.cartegroupbox.setLayout(carte_layout)
        layout.addWidget(self.cartegroupbox)

        # =========================================================
        # PARTIE DROITE : INFOS (Dashboard)
        # =========================================================
        self.infogroupbox = QFrame()
        self.infogroupbox.setStyleSheet("QFrame { background-color: #F8F9F9; border-radius: 8px; }")
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(15)

        # --- A. SÉLECTEUR D'ANNÉE ---
        year_layout = QHBoxLayout()
        lbl_annee = QLabel("📅 Année :")
        lbl_annee.setStyleSheet("font-weight: bold; color: #555;")
        
        self.combo_annee = QComboBox()
        self.combo_annee.addItems(["2015", "2016", "2017", "2018", "2019", "2020"])
        self.combo_annee.setCurrentIndex(5) # 2020 par défaut
        self.combo_annee.setStyleSheet("QComboBox { background: white; padding: 4px; border: 1px solid #CCC; }")
        self.combo_annee.currentTextChanged.connect(self.on_year_changed)

        year_layout.addWidget(lbl_annee)
        year_layout.addWidget(self.combo_annee)
        year_layout.addStretch()
        info_layout.addLayout(year_layout)

        # --- B. EN-TÊTE (DRAPEAU + PAYS) ---
        header_layout = QHBoxLayout()
        
        # Drapeau : Taille FIXE (Lock)
        self.lbl_drapeau = QLabel("🏳️") 
        self.lbl_drapeau.setFixedSize(90, 60) # 90x60 pixels
        self.lbl_drapeau.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_drapeau.setStyleSheet("border: 1px solid #CCC; background-color: white; border-radius: 4px;")
        
        # Nom du pays
        self.lbl_pays = QLabel("Sélectionnez un pays")
        self.lbl_pays.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50;")
        self.lbl_pays.setWordWrap(True)

        header_layout.addWidget(self.lbl_drapeau)
        header_layout.addWidget(self.lbl_pays, stretch=1)
        info_layout.addLayout(header_layout)

        # --- C. HERO SCORE (Cadre Bleu) ---
        score_frame = QFrame()
        score_frame.setStyleSheet("QFrame { background-color: #D6EAF8; border: 1px solid #AED6F1; border-radius: 10px; }")
        score_layout = QVBoxLayout(score_frame)
        
        lbl_titre_score = QLabel("HAPPINESS SCORE")
        lbl_titre_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titre_score.setStyleSheet("color: #2471A3; font-weight: bold; font-size: 11px; border: none;")
        
        self.lbl_score_valeur = QLabel("-") 
        self.lbl_score_valeur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_score_valeur.setStyleSheet("color: #154360; font-weight: bold; font-size: 38px; border: none;")
        
        self.lbl_rank_valeur = QLabel("Rang mondial : -")
        self.lbl_rank_valeur.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_rank_valeur.setStyleSheet("color: #555; font-style: italic; font-size: 12px; border: none;")

        score_layout.addWidget(lbl_titre_score)
        score_layout.addWidget(self.lbl_score_valeur)
        score_layout.addWidget(self.lbl_rank_valeur)
        info_layout.addWidget(score_frame)

        # --- D. GRILLE DES DÉTAILS ---
        self.val_gdp = QLabel("-")
        self.val_health = QLabel("-")
        self.val_cpi = QLabel("-")
        self.val_family = QLabel("-")
        self.val_freedom = QLabel("-")
        self.val_generosity = QLabel("-")

        details_group = QGroupBox()
        details_group.setStyleSheet("QGroupBox { border: 1px solid #DDD; margin-top: 5px; }")
        grid_stats = QGridLayout()
        grid_stats.setVerticalSpacing(20)
        grid_stats.setHorizontalSpacing(10)

        # Fonction interne pour placer les widgets
        def place_stat(row, col, icon, label, widget):
            lbl_icon = QLabel(f"{icon} {label}")
            lbl_icon.setStyleSheet("color: #666; font-size: 12px; border: none;")
            widget.setAlignment(Qt.AlignmentFlag.AlignRight)
            widget.setStyleSheet("font-weight: bold; color: #333; font-size: 13px; border: none;")
            
            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(0,0,0,0)
            h.addWidget(lbl_icon)
            h.addStretch()
            h.addWidget(widget)
            grid_stats.addWidget(container, row, col)

        place_stat(0, 0, "💰", "PIB/Hab", self.val_gdp)
        place_stat(1, 0, "❤️", "Espérance", self.val_health)
        place_stat(2, 0, "⚖️", "Corruption", self.val_cpi)
        place_stat(0, 1, "👨‍👩‍👧", "Social", self.val_family)
        place_stat(1, 1, "🕊️", "Liberté", self.val_freedom)
        place_stat(2, 1, "🎁", "Générosité", self.val_generosity)

        details_group.setLayout(grid_stats)
        info_layout.addWidget(details_group)

        # --- E. GRAPHIQUE MATPLOTLIB (Historique) ---
        self.figure = Figure(figsize=(4, 3), dpi=100)
        self.figure.patch.set_facecolor('none')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        
        info_layout.addWidget(self.canvas)

        # Fin du layout droit
        info_layout.addStretch()
        self.infogroupbox.setLayout(info_layout)
        layout.addWidget(self.infogroupbox)

        # Ratios : 70% Carte, 30% Infos
        layout.setStretch(0, 7)
        layout.setStretch(1, 3)

        self.load_folium_map()

    # =========================================================
    # LOGIQUE MÉTIER
    # =========================================================

    def load_csv_data(self):
        # Utilisation de os.path pour trouver le fichier peu importe d'où on lance le script
        csv_filename = (
            "dataset/happiness.csv"  # ASSUREZ-VOUS QUE VOTRE FICHIER A CE NOM
        )

        
        if os.path.exists(csv_filename):
            try:
                self.data_happiness = pd.read_csv(csv_filename)
                self.data_happiness.columns = self.data_happiness.columns.str.strip()
                
                # Conversions numériques
                self.data_happiness['happiness_score'] = pd.to_numeric(self.data_happiness['happiness_score'], errors='coerce')
                self.data_happiness['Year'] = pd.to_numeric(self.data_happiness['Year'], errors='coerce').fillna(0).astype(int)
                
                # Tri : Par Année, puis par Score décroissant
                self.data_happiness = self.data_happiness.sort_values(by=['Year', 'happiness_score'], ascending=[True, False])
                
                # Calcul du Rang par Année
                self.data_happiness['Calculated Rank'] = self.data_happiness.groupby('Year').cumcount() + 1
                
                print("Données chargées, triées et classées.")
            except Exception as e:
                print(f"Erreur CSV : {e}")
        else:
            print(f"ERREUR : Fichier introuvable : {csv_filename}")

    def on_country_clicked(self, title):
        # Filtre les messages techniques
        if not title or "qrc:/" in title or "http" in title:
            return
        
        self.pays_actuel = title
        self.afficher_donnees_pays()

    def on_year_changed(self, new_year):
        if self.pays_actuel:
            self.afficher_donnees_pays()

    def afficher_donnees_pays(self):
        if not self.pays_actuel or self.data_happiness is None:
            return

        print(f"Affichage : {self.pays_actuel}")

        # Mapping noms Map -> CSV
        mapping_noms = {
            "United States of America": "United States",
            "Tanzania": "United Republic of Tanzania",
            "Congo": "Congo (Brazzaville)",
            "Democratic Republic of the Congo": "Congo (Kinshasa)",
            # Ajoute d'autres corrections ici si nécessaire
        }
        nom_recherche = mapping_noms.get(self.pays_actuel, self.pays_actuel)
        annee = int(self.combo_annee.currentText())

        # 1. Filtre DataFrame pour l'année spécifique
        resultat = self.data_happiness[
            (self.data_happiness["Country"] == nom_recherche) & 
            (self.data_happiness["Year"] == annee)
        ]

        if not resultat.empty:
            data = resultat.iloc[0]

            # --- Mise à jour Interface ---
            
            # Nom
            self.lbl_pays.setText(f"{self.pays_actuel.upper()} ({data.get('continent', '-')})")
            
            # Drapeau
            iso_code = self.get_country_code(nom_recherche)
            if iso_code:
                url = f"https://flagcdn.com/h80/{iso_code}.png"
                try:
                    r = requests.get(url, timeout=2)
                    if r.status_code == 200:
                        pix = QPixmap()
                        pix.loadFromData(r.content)
                        # Redimensionnement locké 90x60
                        pix = pix.scaled(self.lbl_drapeau.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.lbl_drapeau.setPixmap(pix)
                    else:
                        self.lbl_drapeau.setText("🏳️")
                except:
                    self.lbl_drapeau.setText("🏳️")
            else:
                self.lbl_drapeau.setText("🏳️")

            # Score & Rang
            try:
                score = float(data.get('happiness_score', 0))
                self.lbl_score_valeur.setText(f"{score:.2f}")
            except: self.lbl_score_valeur.setText("-")

            try:
                rank = int(data.get('Calculated Rank', 0))
                self.lbl_rank_valeur.setText(f"Rang mondial ({annee}) : #{rank}")
            except: self.lbl_rank_valeur.setText("Rang : -")

            # Indicateurs
            def set_val(lbl, col):
                try: lbl.setText(f"{float(data.get(col)):.2f}")
                except: lbl.setText("-")

            set_val(self.val_gdp, 'gdp_per_capita')
            set_val(self.val_health, 'health')
            set_val(self.val_cpi, 'cpi_score')
            set_val(self.val_family, 'family')
            set_val(self.val_freedom, 'freedom')
            set_val(self.val_generosity, 'generosity')

            # --- Mise à jour Graphique ---
            self.update_graph(nom_recherche)

        else:
            # Données introuvables pour cette année
            self.lbl_pays.setText(f"{self.pays_actuel} (Pas de données {annee})")
            self.lbl_score_valeur.setText("-")
            self.lbl_rank_valeur.setText("-")
            self.lbl_drapeau.setText("🏳️")
            for l in [self.val_gdp, self.val_health, self.val_cpi, self.val_family, self.val_freedom, self.val_generosity]:
                l.setText("-")
            self.figure.clear()
            self.canvas.draw()

    def update_graph(self, nom_pays_csv):
        """Dessine l'historique 2015-2020 avec les rangs"""
        self.figure.clear()
        
        # On récupère toutes les années pour ce pays, triées chronologiquement
        histo = self.data_happiness[self.data_happiness["Country"] == nom_pays_csv].sort_values("Year")
        
        if not histo.empty:
            ax = self.figure.add_subplot(111)
            
            # 1. Le Tracé de la courbe
            # J'ai légèrement augmenté la taille des marqueurs (markersize=6) pour qu'on voie mieux les points
            ax.plot(histo["Year"], histo["happiness_score"], marker='o', linestyle='-', color='#2E86C1', linewidth=2, markersize=5)
            
            # --- NOUVEAU : AJOUT DES ÉTIQUETTES DE RANG ---
            # On itère sur chaque ligne (chaque année) du dataframe historique
            # iterrows() renvoie (index, série de données pour la ligne)
            for _, row in histo.iterrows():
                try:
                    # On s'assure que c'est un entier
                    rank_val = int(row['Calculated Rank'])
                    rank_text = f"#{rank_val}"
                    
                    # ax.annotate permet de placer du texte avec un décalage précis
                    ax.annotate(
                        rank_text,                                # Le texte (ex: "#12")
                        xy=(row['Year'], row['happiness_score']), # Le point exact où attacher le texte (X, Y des données)
                        xytext=(0, 8),                            # Le décalage : 0 horizontal, 8 points vers le HAUT
                        textcoords='offset points',               # Indique que xytext est en "points" (pixels), pas en données
                        ha='center',                              # Alignement horizontal : centré au-dessus du point
                        va='bottom',                              # Alignement vertical : le bas du texte touche le décalage
                        fontsize=7,                               # Petite police pour ne pas surcharger
                        color='#333',                             # Couleur gris foncé
                        fontweight='bold'                         # Gras pour la lisibilité
                    )
                except Exception as e:
                    # Sécurité au cas où une valeur de rang serait manquante
                    print(f"Erreur annotation graphe pour une année : {e}")
                    continue
            # --- FIN NOUVEAU ---

            # Style général du graphe
            ax.set_title(f"Évolution (2015-2020)", fontsize=6, color='#444')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.tick_params(labelsize=7, colors='#555')
            # On force l'axe X à n'afficher que les années entières présentes dans les données
            ax.set_xticks(histo["Year"].unique())
            ax.set_facecolor('#FAFAFA')
            
            # Ajuste les marges pour que les nouvelles étiquettes ne sortent pas du cadre
            self.figure.tight_layout()
            
        self.canvas.draw()

    def get_country_code(self, name):
        # Corrections manuelles
        corrections = {
            "United States": "US", "Russia": "RU", "Tanzania": "TZ", 
            "Congo (Kinshasa)": "CD", "Congo (Brazzaville)": "CG",
            "Iran": "IR", "Vietnam": "VN", "South Korea": "KR", 
            "Laos": "LA", "Syria": "SY", "Moldova": "MD", 
            "Bolivia": "BO", "Venezuela": "VE", "Taiwan": "TW"
        }
        if name in corrections: return corrections[name].lower()
        
        try:
            res = pycountry.countries.search_fuzzy(name)
            if res: return res[0].alpha_2.lower()
        except: pass
        return None

    def load_folium_map(self):
        geo_url = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"
        
        m = folium.Map(location=[20, 0], zoom_start=2, min_zoom=2, max_zoom=6, tiles="CartoDB positron", max_bounds=True)
        map_id = m.get_name()

        # JS pour le clic
        click_js = """
        function onEachFeature(feature, layer) {
            layer.on({
                click: function (e) {
                    geojsonLayer.resetStyle();
                    e.target.setStyle({ fillColor: '#2E86C1', color: '#154360', weight: 2, fillOpacity: 0.9 });
                    document.title = feature.properties.name;
                }
            });
        }
        """
        # CSS (enlève le cadre orange)
        m.get_root().header.add_child(folium.Element("<style>.leaflet-interactive:focus { outline: none !important; }</style>"))
        
        # Injection GeoJSON
        m.get_root().script.add_child(folium.Element(f"""
            var geojsonLayer = L.geoJson(null, {{
                style: function(f) {{ return {{ fillColor: '#D6EAF8', color: '#5DADE2', weight: 0.7, fillOpacity: 0.7 }}; }},
                onEachFeature: onEachFeature
            }});
            fetch("{geo_url}").then(r => r.json()).then(d => {{ geojsonLayer.addData(d); geojsonLayer.addTo({map_id}); }});
            {click_js}
        """))

        data = io.BytesIO()
        m.save(data, close_file=False)
        self.web_view.setHtml(data.getvalue().decode("utf-8"), baseUrl=QUrl("qrc:/"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    
    # Titre
    window.setWindowTitle("HappySight - Analyse du Bonheur Mondial")
    
    # On définit le widget central
    window.setCentralWidget(MapWidget())
    
    # IMPORTANT : C'est cette ligne qui lance la fenêtre en plein écran
    # Elle REMPLACE window.show()
    window.showMaximized()
    
    sys.exit(app.exec())