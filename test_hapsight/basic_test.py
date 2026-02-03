import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication

from hapsight.countrieswidget import CountriesWidget
from hapsight.mainwindow import MainWindow, load_data
from hapsight.mapwidget import MapWidget
from hapsight.stats_widget import StatsWidget


def test_load_data():
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


def test_load_data_years():
    """Vérifie que les années sont entre 2015 et 2020"""
    data = load_data()
    assert data["Year"].min() >= 2015
    assert data["Year"].max() <= 2020


@pytest.fixture
def qapp():
    """Fixture pour créer une QApplication une seule fois"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_mainwindow(qapp):
    """Vérifie que la fenêtre principale se crée sans erreur"""
    window = MainWindow()
    assert isinstance(window, MainWindow)


def test_mainwindow_title(qapp):
    """Vérifie que la fenêtre a le bon titre"""
    window = MainWindow()
    assert window.windowTitle() == "HappySight"


def test_mainwindow_tabs(qapp):
    """Vérifie que tous les onglets sont présents"""
    window = MainWindow()
    tab_count = window.tab_manager.count()
    assert tab_count == 3, f"Attendu 4 onglets, reçu {tab_count}"


def test_mainwindow_tabs_names(qapp):
    """Vérifie que les onglets ont les bons noms"""
    window = MainWindow()
    expected_tabs = ["Carte du Monde", "Stats et Corrélations", "Pays"]
    for i, expected_name in enumerate(expected_tabs):
        actual_name = window.tab_manager.tabText(i)
        assert actual_name == expected_name, (
            f"Onglet {i}: attendu '{expected_name}', reçu '{actual_name}'"
        )


# TESTS DES WIDGETS
def test_mapwidget_data(qapp):
    """Vérifie que MapWidget reçoit les données"""
    data = load_data()
    widget = MapWidget(data)
    assert isinstance(widget.data_happiness, pd.DataFrame)
    assert len(widget.data_happiness) > 0


def test_statswidget_data(qapp):
    """Vérifie que StatsWidget reçoit les données"""
    data = load_data()
    widget = StatsWidget(data)
    assert isinstance(widget.df, pd.DataFrame)
    assert len(widget.df) > 0


def test_countrieswidget_data(qapp):
    """Vérifie que CountriesWidget reçoit les données"""
    data = load_data()
    widget = CountriesWidget(data)
    assert isinstance(widget.df, pd.DataFrame)
    assert len(widget.df) > 0


# TESTS D'INTÉGRITÉ DES DONNÉES


def test_country_not_null():
    """Vérifie qu'il n'y a pas de pays sans nom"""
    data = load_data()
    assert data["Country"].isnull().sum() == 0, "Il y a des pays vides"


def test_years_no_null():
    """Vérifie qu'il n'y a pas d'années manquantes"""
    data = load_data()
    assert data["Year"].isnull().sum() == 0, "Il y a des années vides"


def test_continent_not_null():
    """Vérifie qu'il n'y a pas de continent vide"""
    data = load_data()
    null_continents = data["continent"].isnull().sum()
    assert null_continents == 0, f"Il y a {null_continents} continents vides"
