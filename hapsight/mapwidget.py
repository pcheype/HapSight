import io
import requests
import pycountry
import pandas as pd
import folium

# --- MATPLOTLIB / QT ---
import matplotlib
matplotlib.use("QtAgg")  # Obligatoire pour PySide6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QGroupBox, QFrame, QComboBox
)


class MapWidget(QWidget):
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)

        # --- Etat ---
        self.pays_actuel = None

        # --- Données ---
        self.df = df
        self.data_happiness = None
        self.load_df_data()

        # --- Layout principal ---
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # =========================================================
        # GAUCHE : CARTE
        # =========================================================
        self.cartegroupbox = QGroupBox()
        self.cartegroupbox.setStyleSheet("QGroupBox { border: 1px solid #CCC; border-radius: 5px; }")
        carte_layout = QVBoxLayout()
        carte_layout.setContentsMargins(1, 1, 1, 1)

        self.web_view = QWebEngineView()
        # ✅ Le clic JS met document.title = "Country Name"
        # ✅ Qt reçoit via titleChanged
        self.web_view.titleChanged.connect(self.on_country_clicked)

        carte_layout.addWidget(self.web_view)
        self.cartegroupbox.setLayout(carte_layout)
        layout.addWidget(self.cartegroupbox)

        # =========================================================
        # DROITE : DASHBOARD
        # =========================================================
        self.infogroupbox = QFrame()
        self.infogroupbox.setStyleSheet("QFrame { background-color: #F8F9F9; border-radius: 8px; }")

        info_layout = QVBoxLayout()
        info_layout.setSpacing(15)

        # --- Sélecteur année ---
        year_layout = QHBoxLayout()
        lbl_annee = QLabel("📅 Année :")
        lbl_annee.setStyleSheet("font-weight: bold; color: #555;")

        self.combo_annee = QComboBox()
        self.combo_annee.addItems(["2015", "2016", "2017", "2018", "2019", "2020"])
        self.combo_annee.setCurrentIndex(5)
        self.combo_annee.setStyleSheet("QComboBox { background: white; padding: 4px; border: 1px solid #CCC; }")
        self.combo_annee.currentTextChanged.connect(self.on_year_changed)

        year_layout.addWidget(lbl_annee)
        year_layout.addWidget(self.combo_annee)
        year_layout.addStretch()
        info_layout.addLayout(year_layout)

        # --- Header drapeau + pays ---
        header_layout = QHBoxLayout()

        self.lbl_drapeau = QLabel("🏳️")
        self.lbl_drapeau.setFixedSize(90, 60)
        self.lbl_drapeau.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_drapeau.setStyleSheet("border: 1px solid #CCC; background-color: white; border-radius: 4px;")

        self.lbl_pays = QLabel("Sélectionnez un pays")
        self.lbl_pays.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50;")
        self.lbl_pays.setWordWrap(True)

        header_layout.addWidget(self.lbl_drapeau)
        header_layout.addWidget(self.lbl_pays, stretch=1)
        info_layout.addLayout(header_layout)

        # --- Hero score ---
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

        # --- Détails ---
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

        def place_stat(row, col, icon, label, widget):
            lbl_icon = QLabel(f"{icon} {label}")
            lbl_icon.setStyleSheet("color: #666; font-size: 12px; border: none;")
            widget.setAlignment(Qt.AlignmentFlag.AlignRight)
            widget.setStyleSheet("font-weight: bold; color: #333; font-size: 13px; border: none;")

            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(0, 0, 0, 0)
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

        # --- Graph ---
        self.figure = Figure(figsize=(4, 3), dpi=100)
        self.figure.patch.set_facecolor("none")
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        info_layout.addWidget(self.canvas)

        info_layout.addStretch()
        self.infogroupbox.setLayout(info_layout)
        layout.addWidget(self.infogroupbox)

        layout.setStretch(0, 7)
        layout.setStretch(1, 3)

        # --- Carte ---
        self.load_folium_map()

    # =========================================================
    # DONNEES
    # =========================================================
    def load_df_data(self):
        if self.df is None or getattr(self.df, "empty", True):
            print("ERREUR : DataFrame vide ou None")
            self.data_happiness = None
            return

        try:
            df = self.df.copy()
            df.columns = df.columns.str.strip()

            df["happiness_score"] = pd.to_numeric(df["happiness_score"], errors="coerce")
            df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)

            df = df.sort_values(by=["Year", "happiness_score"], ascending=[True, False])
            df["Calculated Rank"] = df.groupby("Year").cumcount() + 1

            self.data_happiness = df
            print("Données DF chargées, triées et classées.")
        except Exception as e:
            print(f"Erreur préparation DF : {e}")
            self.data_happiness = None

    # =========================================================
    # EVENTS
    # =========================================================
    def on_country_clicked(self, title):
        if not title or "qrc:/" in title or "http" in title:
            return

        self.pays_actuel = title
        self.afficher_donnees_pays()

    def on_year_changed(self, new_year):
        if self.pays_actuel:
            self.afficher_donnees_pays()

    # =========================================================
    # ✅ METHODE QUI MANQUAIT : AFFICHAGE PAYS
    # =========================================================
    def afficher_donnees_pays(self):
        if not self.pays_actuel or self.data_happiness is None:
            return

        mapping_noms = {
            "United States of America": "United States",
            "Tanzania": "United Republic of Tanzania",
            "Congo": "Congo (Brazzaville)",
            "Democratic Republic of the Congo": "Congo (Kinshasa)",
        }
        nom_recherche = mapping_noms.get(self.pays_actuel, self.pays_actuel)
        annee = int(self.combo_annee.currentText())

        resultat = self.data_happiness[
            (self.data_happiness["Country"] == nom_recherche) &
            (self.data_happiness["Year"] == annee)
        ]

        if resultat.empty:
            self.lbl_pays.setText(f"{self.pays_actuel} (Pas de données {annee})")
            self.lbl_score_valeur.setText("-")
            self.lbl_rank_valeur.setText("-")
            self.lbl_drapeau.setText("🏳️")
            for l in [self.val_gdp, self.val_health, self.val_cpi, self.val_family, self.val_freedom, self.val_generosity]:
                l.setText("-")
            self.figure.clear()
            self.canvas.draw()
            return

        data = resultat.iloc[0]

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
            score = float(data.get("happiness_score", 0))
            self.lbl_score_valeur.setText(f"{score:.2f}")
        except:
            self.lbl_score_valeur.setText("-")

        try:
            rank = int(data.get("Calculated Rank", 0))
            self.lbl_rank_valeur.setText(f"Rang mondial ({annee}) : #{rank}")
        except:
            self.lbl_rank_valeur.setText("Rang : -")

        # Indicateurs
        def set_val(lbl, col):
            try:
                lbl.setText(f"{float(data.get(col)):.2f}")
            except:
                lbl.setText("-")

        set_val(self.val_gdp, "gdp_per_capita")
        set_val(self.val_health, "health")
        set_val(self.val_cpi, "cpi_score")
        set_val(self.val_family, "family")
        set_val(self.val_freedom, "freedom")
        set_val(self.val_generosity, "generosity")

        self.update_graph(nom_recherche)

    # =========================================================
    # GRAPH
    # =========================================================
    def update_graph(self, nom_pays_csv):
        self.figure.clear()

        histo = self.data_happiness[self.data_happiness["Country"] == nom_pays_csv].sort_values("Year")
        if not histo.empty:
            ax = self.figure.add_subplot(111)

            ax.plot(
                histo["Year"], histo["happiness_score"],
                marker="o", linestyle="-", color="#2E86C1",
                linewidth=2, markersize=5
            )

            for _, row in histo.iterrows():
                try:
                    rank_val = int(row["Calculated Rank"])
                    ax.annotate(
                        f"#{rank_val}",
                        xy=(row["Year"], row["happiness_score"]),
                        xytext=(0, 8),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=7,
                        color="#333",
                        fontweight="bold"
                    )
                except:
                    continue

            ax.set_title("Évolution (2015-2020)", fontsize=6, color="#444")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.tick_params(labelsize=7, colors="#555")
            ax.set_xticks(histo["Year"].unique())
            ax.set_facecolor("#FAFAFA")
            self.figure.tight_layout()

        self.canvas.draw()

    # =========================================================
    # FLAGS
    # =========================================================
    def get_country_code(self, name):
        corrections = {
            "United States": "US", "Russia": "RU", "Tanzania": "TZ",
            "Congo (Kinshasa)": "CD", "Congo (Brazzaville)": "CG",
            "Iran": "IR", "Vietnam": "VN", "South Korea": "KR",
            "Laos": "LA", "Syria": "SY", "Moldova": "MD",
            "Bolivia": "BO", "Venezuela": "VE", "Taiwan": "TW"
        }
        if name in corrections:
            return corrections[name].lower()

        try:
            res = pycountry.countries.search_fuzzy(name)
            if res:
                return res[0].alpha_2.lower()
        except:
            pass
        return None

    # =========================================================
    # MAP FOLIUM
    # =========================================================
    def load_folium_map(self):
        geo_url = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"

        m = folium.Map(
            location=[20, 0],
            zoom_start=2,
            min_zoom=2,
            max_zoom=6,
            tiles="CartoDB positron",
            max_bounds=True,
        )
        map_id = m.get_name()

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

        m.get_root().header.add_child(
            folium.Element("<style>.leaflet-interactive:focus { outline: none !important; }</style>")
        )

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