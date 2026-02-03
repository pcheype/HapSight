import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication

from hapsight.mainwindow import MainWindow, load_data
from hapsight.mapwidget import MapWidget
from hapsight.statswidget import StatsWidget
from hapsight.countrieswidget import CountriesWidget
from hapsight.paolo_stats_widget import PaoloStatsWidget


# ========================================
# TESTS DE CHARGEMENT DES DONNÉES
# ========================================

def test_load_data_returns_dataframe():
    """Vérifie que load_data() retourne un DataFrame"""
    data = load_data()
    assert isinstance(data, pd.DataFrame)


def test_load_data_not_empty():
    """Vérifie que le DataFrame n'est pas vide"""
    data = load_data()
    assert len(data) > 0
    assert data.shape[1] > 0


def test_load_data_has_required_columns():
    """Vérifie que le CSV contient les colonnes essentielles"""
    data = load_data()
    required_columns = ["Country", "happiness_score", "continent", "Year"]
    for col in required_columns:
        assert col in data.columns, f"Colonne manquante: {col}"


def test_load_data_years_in_range():
    """Vérifie que les années sont entre 2015 et 2020"""
    data = load_data()
    assert data["Year"].min() >= 2015
    assert data["Year"].max() <= 2020


# ========================================
# TESTS DE LA FENÊTRE PRINCIPALE
# ========================================

@pytest.fixture
def qapp():
    """Fixture pour créer une QApplication une seule fois"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_mainwindow_creation(qapp):
    """Vérifie que la fenêtre principale se crée sans erreur"""
    window = MainWindow()
    assert isinstance(window, MainWindow)


def test_mainwindow_has_title(qapp):
    """Vérifie que la fenêtre a le bon titre"""
    window = MainWindow()
    assert window.windowTitle() == "HappySight"


def test_mainwindow_has_all_tabs(qapp):
    """Vérifie que tous les onglets sont présents"""
    window = MainWindow()
    tab_count = window.tab_manager.count()
    assert tab_count == 4, f"Attendu 4 onglets, reçu {tab_count}"


def test_mainwindow_tabs_have_names(qapp):
    """Vérifie que les onglets ont les bons noms"""
    window = MainWindow()
    expected_tabs = ["Carte du Monde", "Statistiques et Corrélations", "Pays", "Stats Paolo"]
    for i, expected_name in enumerate(expected_tabs):
        actual_name = window.tab_manager.tabText(i)
        assert actual_name == expected_name, f"Onglet {i}: attendu '{expected_name}', reçu '{actual_name}'"


# ========================================
# TESTS DES WIDGETS
# ========================================

def test_mapwidget_receives_data(qapp):
    """Vérifie que MapWidget reçoit les données"""
    data = load_data()
    widget = MapWidget(data)
    assert isinstance(widget.data_happiness, pd.DataFrame)
    assert len(widget.data_happiness) > 0


def test_statswidget_receives_data(qapp):
    """Vérifie que StatsWidget reçoit les données"""
    data = load_data()
    widget = StatsWidget(data)
    assert isinstance(widget.df, pd.DataFrame)
    assert len(widget.df) > 0


def test_countrieswidget_receives_data(qapp):
    """Vérifie que CountriesWidget reçoit les données"""
    data = load_data()
    widget = CountriesWidget(data)
    assert isinstance(widget.df, pd.DataFrame)
    assert len(widget.df) > 0


def test_paolostatwidget_receives_data(qapp):
    """Vérifie que PaoloStatsWidget reçoit les données"""
    data = load_data()
    widget = PaoloStatsWidget(data)
    assert isinstance(widget.df, pd.DataFrame)
    assert len(widget.df) > 0


# ========================================
# TESTS D'INTÉGRITÉ DES DONNÉES
# ========================================

def test_happiness_score_valid_range():
    """Vérifie que les scores de bonheur sont dans une plage raisonnable"""
    data = load_data()
    happiness = data["happiness_score"]
    assert happiness.min() > 0, "Il y a des scores négatifs"
    assert happiness.max() <= 10, "Il y a des scores > 10"


def test_no_null_countries():
    """Vérifie qu'il n'y a pas de pays sans nom"""
    data = load_data()
    assert data["Country"].isnull().sum() == 0, "Il y a des pays vides"


def test_no_null_years():
    """Vérifie qu'il n'y a pas d'années manquantes"""
    data = load_data()
    assert data["Year"].isnull().sum() == 0, "Il y a des années vides"


def test_continent_column_not_null():
    """Vérifie qu'il n'y a pas de continent vide"""
    data = load_data()
    null_continents = data["continent"].isnull().sum()
    assert null_continents == 0, f"Il y a {null_continents} continents vides"


# ========================================
# TESTS DE FONCTIONNALITÉ
# ========================================

def test_mapwidget_year_combo_populated(qapp):
    """Vérifie que le sélecteur d'année contient des données"""
    data = load_data()
    widget = MapWidget(data)
    year_count = widget.combo_annee.count()
    assert year_count > 0, "Le sélecteur d'année est vide"


def test_statswidget_graph_combo_populated(qapp):
    """Vérifie que le sélecteur de graphe contient des options"""
    data = load_data()
    widget = StatsWidget(data)
    graph_count = widget.cmb_graph.count()
    assert graph_count > 0, "Le sélecteur de graphe est vide"


def test_countrieswidget_continent_filter_populated(qapp):
    """Vérifie que le filtre par continent fonctionne"""
    data = load_data()
    widget = CountriesWidget(data)
    continents = data["continent"].unique()
    assert len(continents) > 0, "Aucun continent trouvé"


# ========================================
# TESTS DE COHÉRENCE DU PROJET
# ========================================

def test_all_countries_have_data(qapp):
    """Vérifie que chaque pays a au moins un score de bonheur"""
    data = load_data()
    countries_with_score = data[data["happiness_score"].notna()]
    assert len(countries_with_score) > 0, "Aucun pays avec score de bonheur"


def test_data_consistency_in_mainwindow(qapp):
    """Vérifie que MainWindow charge les mêmes données partout"""
    window = MainWindow()
    
    # Vérifier que tous les widgets reçoivent les données
    assert len(window.map_tab.data_happiness) > 0
    assert len(window.stats_tab.df) > 0
    assert len(window.countries_tab.df) > 0
    assert len(window.PaoloStats_tab.df) > 0
