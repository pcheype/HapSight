import io
import os
import sys

import folium
import pandas as pd  # Importation de Pandas pour gérer les données
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)


class MapWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- CHARGEMENT DES DONNÉES CSV ---
        self.data_happiness = None
        self.load_csv_data()

        layout = QHBoxLayout(self)

        # Partie Gauche : Carte
        self.cartegroupbox = QGroupBox("")
        cartegroupbox_layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        self.web_view.titleChanged.connect(self.on_country_clicked)
        cartegroupbox_layout.addWidget(self.web_view)
        self.cartegroupbox.setLayout(cartegroupbox_layout)
        layout.addWidget(self.cartegroupbox)

        # Partie Droite : Infos
        self.infogroupbox = QGroupBox("")
        infogroupbox_layout = QVBoxLayout()
        name_layout = QHBoxLayout()
        self.drapeau_label = QLabel()
        self.name_label = QLabel("Cliquez sur un pays pour voir les données.")
        self.info_groupbox = QGroupBox("Informations du Pays")

        name_layout.addWidget(self.drapeau_label)
        name_layout.addWidget(self.name_label)
        name_layout.setStretch(0, 1)
        name_layout.setStretch(1, 10)
        infogroupbox_layout.addLayout(name_layout)
        infogroupbox_layout.addWidget(self.info_groupbox)
        infogroupbox_layout.setStretch(0, 1)
        infogroupbox_layout.setStretch(1, 10)

        self.infogroupbox.setLayout(infogroupbox_layout)
        layout.addWidget(self.infogroupbox)
        layout.setStretch(0, 10)  # La carte prend plus de place
        layout.setStretch(1, 4)

        self.load_folium_map()

    def load_csv_data(self):
        """Charge le fichier CSV en mémoire avec Pandas"""
        csv_filename = (
            "dataset/happiness.csv"  # ASSUREZ-VOUS QUE VOTRE FICHIER A CE NOM
        )

        if os.path.exists(csv_filename):
            try:
                self.data_happiness = pd.read_csv(csv_filename)
                print("Données chargées avec succès !")
                # Nettoyage optionnel : enlever les espaces dans les noms de colonnes
                self.data_happiness.columns = self.data_happiness.columns.str.strip()
            except Exception as e:
                print(f"Erreur lors de la lecture du CSV : {e}")
        else:
            print(f"ATTENTION : Le fichier {csv_filename} est introuvable.")

    def on_country_clicked(self, title):
        """Réception du signal JS -> Python"""
        if not title or "qrc:/" in title or "http" in title:
            return

        # On appelle la logique métier
        self.afficher_donnees_pays(title)

    def afficher_donnees_pays(self, pays_map):
        """
        Cherche le pays dans le DataFrame Pandas et affiche les infos.
        """
        print(f"Recherche pour : {pays_map}")

        if self.data_happiness is None:
            self.info_label.setText(
                "Erreur : Base de données non chargée.\nVérifiez le fichier CSV."
            )
            return

        # --- GESTION DES NOMS DE PAYS ---
        # La carte envoie parfois des noms différents du CSV (ex: USA)
        # On peut faire un dictionnaire de mapping manuel pour les cas courants
        mapping_noms = {
            "United States of America": "United States",
            "Tanzania": "United Republic of Tanzania",
            "Congo": "Congo (Brazzaville)",
            "Democratic Republic of the Congo": "Congo (Kinshasa)",
        }

        # On utilise le nom mappé si il existe, sinon le nom d'origine
        nom_recherche = mapping_noms.get(pays_map, pays_map)

        # --- RECHERCHE PANDAS ---
        # On filtre le tableau où la colonne 'Country' correspond au nom
        # Note: Adaptez 'Country' si la colonne s'appelle 'Country name' dans votre CSV précis
        resultat = self.data_happiness[self.data_happiness["Country"] == nom_recherche]

        if not resultat.empty:
            # On prend la première ligne trouvée (souvent la plus récente ou l'unique)
            data = resultat.iloc[0]

            # Construction du texte d'affichage
            # Adaptez les clés ['Happiness Score'] etc selon les VRAIES colonnes de votre CSV
            infos = f"<b>PAYS : {pays_map.upper()}</b><br><br>"

            # Exemple basé sur les colonnes probables du dataset Kaggle
            try:
                infos += (
                    f"🏆 Happiness Rank : {data.get('Happiness Rank', 'Aucun')}<br>"
                )
                infos += (
                    f"😃 Happiness Score : {data.get('happiness_score', 'N/A')}<br>"
                )
                infos += f"💰 GDP per Capita : {data.get('gdp_per_capita', 'N/A')}<br>"
                infos += f"👪 Family : {data.get('family', 'N/A')}<br>"
                infos += f"heart Health (Life Expectancy) : {data.get('Health (Life Expectancy)', 'N/A')}<br>"
                infos += f"🗽 Freedom : {data.get('Freedom', 'N/A')}<br>"
            except Exception as e:
                infos += f"<br>Erreur d'affichage des colonnes : {e}"

            self.info_label.setText(infos)
        else:
            self.info_label.setText(
                f"<b>{pays_map}</b><br><br>Pas de données trouvées dans le CSV pour ce pays.<br>Essayez de vérifier l'orthographe dans le fichier."
            )

    def load_folium_map(self):
        # ... (Ce code reste IDENTIQUE à votre version précédente fonctionnelle) ...
        geo_data_url = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"

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
                    e.target.setStyle({
                        fillColor: '#2E86C1', color: '#154360', weight: 2, fillOpacity: 0.9
                    });
                    document.title = feature.properties.name;
                }
            });
        }
        """
        remove_focus_css = (
            "<style>.leaflet-interactive:focus { outline: none !important; }</style>"
        )
        m.get_root().header.add_child(folium.Element(remove_focus_css))

        m.get_root().script.add_child(
            folium.Element(f"""
            var geojsonLayer = L.geoJson(null, {{
                style: function(feature) {{
                    return {{ fillColor: '#D6EAF8', color: '#5DADE2', weight: 0.7, fillOpacity: 0.7 }};
                }},
                onEachFeature: onEachFeature
            }});

            fetch("{geo_data_url}")
                .then(function(response) {{ return response.json(); }})
                .then(function(data) {{
                    geojsonLayer.addData(data);
                    geojsonLayer.addTo({map_id});
                }});
            {click_js}
        """)
        )

        data = io.BytesIO()
        m.save(data, close_file=False)
        self.web_view.setHtml(data.getvalue().decode("utf-8"), baseUrl=QUrl("qrc:/"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.resize(1200, 800)
    window.setCentralWidget(MapWidget())
    window.show()
    sys.exit(app.exec())
