import io
import pandas as pd  # <-- AJOUT

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox
)
from PySide6.QtCore import Qt, QUrl, Signal
import folium
from PySide6.QtWebEngineWidgets import QWebEngineView


class MapWidget(QWidget):
    """
    Widget de carte du monde (Folium dans QWebEngineView).
    df est stocké pour usage futur (stats au clic, etc.)
    """
    country_clicked = Signal(str)  # Signal émis lorsqu'un pays est cliqué

    # ✅ CHANGEMENT ICI : df en premier argument
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)  # ✅ parent reste un QWidget, pas df
        self.df = df              # ✅ on stocke le DataFrame

        layout = QHBoxLayout(self)

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

        layout.setStretch(0, 10)
        layout.setStretch(1, 4)

    def load_folium_map(self):
        """
        Génère une carte Folium interactive :
        - Impossible de se déplacer hors du monde.
        - Le pays cliqué se colore d'une teinte plus foncée.
        """

        geo_data_url = (
            "https://raw.githubusercontent.com/python-visualization/folium/main/"
            "examples/data/world-countries.json"
        )

        coords = [20, 0]

        m = folium.Map(
            location=coords,
            tiles="CartoDB positron",
            zoom_start=2,
            min_zoom=2,
            max_zoom=6,
            max_bounds=True,
        )

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
                "fillColor": "#3498DB",
                "color": "#1F618D",
                "weight": 1.5,
                "fillOpacity": 0.9,
            },
            tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Pays :"]),
        )
        geojson.add_to(m)

        click_js = """
        function onEachFeature(feature, layer) {
            layer.on({
                click: function (e) {
                    geojsonLayer.resetStyle();
                    e.target.setStyle({
                        fillColor: '#2E86C1',
                        color: '#154360',
                        weight: 2,
                        fillOpacity: 0.9
                    });
                    map.fitBounds(e.target.getBounds());
                }
            });
        }
        """

        remove_focus_css = """
        <style>
            .leaflet-interactive:focus {
                outline: none !important;
            }
        </style>
        """
        m.get_root().header.add_child(folium.Element(remove_focus_css))

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

        m.fit_bounds([[-60, -180], [85, 180]])

        data = io.BytesIO()
        m.save(data, close_file=False)
        html_content = data.getvalue().decode("utf-8")
        self.web_view.setHtml(html_content, baseUrl=QUrl("qrc:/"))
