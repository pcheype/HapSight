from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTabWidget, 
    QVBoxLayout,
    QHBoxLayout, 
    QLabel,
    QGroupBox    
)
from PySide6.QtCore import Qt,QUrl, Signal
import folium 
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
import io  

class MapWidget(QWidget):
    """
    Ce widget contiendra la visualisation de la carte du monde.
    (Probablement un QWebEngineView pour afficher Folium, ou un QMapViewer).
    """
    country_clicked = Signal(str)  # Signal émis lorsqu'un pays est cliqué
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Définir une mise en page (layout)
        layout = QHBoxLayout(self)
        
        # Vous initialiserez vos composants de carte ici
        self.cartegroupbox = QGroupBox("")
        cartegroupbox_layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        cartegroupbox_layout.addWidget(self.web_view)
        self.cartegroupbox.setLayout(cartegroupbox_layout)
        layout.addWidget(self.cartegroupbox)
        self.load_folium_map()
        
        self.infogroupbox = QGroupBox("")
        infogroupbox_layout = QVBoxLayout()
        info_placeholder_label = QLabel("Infos ici")
        info_placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        infogroupbox_layout.addWidget(info_placeholder_label)
        self.infogroupbox.setLayout(infogroupbox_layout)
        layout.addWidget(self.infogroupbox)

        layout.setStretch(0,10)
        layout.setStretch(1,4)

    def load_folium_map(self):
        """
        Génère une carte Folium interactive :
        - Impossible de se déplacer hors du monde.
        - Le pays cliqué se colore d'une teinte plus foncée.
        """

        # --- URL GeoJSON des pays ---
        geo_data_url = (
            "https://raw.githubusercontent.com/python-visualization/folium/main/"
            "examples/data/world-countries.json"
        )

        # Coordonnées centrées
        coords = [20, 0]

        # --- Création de la carte ---
        m = folium.Map(
            location=coords,
            tiles="CartoDB positron",
            zoom_start=2,
            min_zoom=2,
            max_zoom=6,
            max_bounds=True,  # Empêche de sortir de la zone du monde
        )

        # --- Couche GeoJSON cliquable ---
        geojson = folium.GeoJson(
            geo_data_url,
            name="Pays",
            style_function=lambda feature: {
                "fillColor": "#D6EAF8",
                "color": "#5DADE2",
                "weight": 0.7,
                "fillOpacity": 0.7,
            },
            highlight_function=lambda feature: {
                # Lorsqu'on clique ou survole : couleur plus foncée
                "fillColor": "#3498DB",
                "color": "#1F618D",
                "weight": 1.5,
                "fillOpacity": 0.9,
            },
            tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Pays :"]),
        )
        geojson.add_to(m)

        # --- Script JS pour gérer le clic sur un pays ---
        # Lorsqu'on clique, on applique le style "highlight_function"
        click_js = """
        function onEachFeature(feature, layer) {
            layer.on({
                click: function (e) {
                    // Réinitialise tous les styles
                    geojsonLayer.resetStyle();
                    // Applique le style de surbrillance au pays cliqué
                    e.target.setStyle({
                        fillColor: '#2E86C1',
                        color: '#154360',
                        weight: 2,
                        fillOpacity: 0.9
                    });
                    // Centre la vue sur le pays cliqué
                    map.fitBounds(e.target.getBounds());
                }
            });
        }
        """
        # --- Suppression du carré orange (focus Leaflet) ---
        remove_focus_css = """
        <style>
            /* Supprime le contour orange autour des pays cliqués */
            .leaflet-interactive:focus {
                outline: none !important;
            }
        </style>
        """
        m.get_root().header.add_child(folium.Element(remove_focus_css))


        # Injection du script JS dans la carte
        m.get_root().script.add_child(folium.Element(f"""
            var map = this;
            var geojsonLayer = L.geoJson(null, {{
                style: function(feature) {{
                    return {{ fillColor: '#D6EAF8', color: '#5DADE2', weight: 0.7, fillOpacity: 0.7 }};
                }},
                onEachFeature: onEachFeature
            }});
            {click_js}
        """))

        # --- Ajout des limites de déplacement (le monde entier) ---
        m.fit_bounds([[-60, -180], [85, 180]])

        # --- Export vers le QWebEngineView ---
        data = io.BytesIO()
        m.save(data, close_file=False)
        html_content = data.getvalue().decode("utf-8")
        self.web_view.setHtml(html_content, baseUrl=QUrl("qrc:/"))