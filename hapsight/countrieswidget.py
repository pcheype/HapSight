from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

COUNTRY_COL = "Country"
CONTINENT_COL = "continent"
YEAR_COL = "Year"
HAPPINESS_COL = "happiness_score"
GDP_COL = "gdp_per_capita"
HEALTH_COL = "health"


class PandasTableModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):  # type: ignore
        if not index.isValid():
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):  # type: ignore
            value = self._df.iat[index.row(), index.column()]
            if pd.isna(value):
                return ""
            if isinstance(value, float):
                return f"{value:.3f}"
            return str(value)

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole
    ):  # type: ignore
        if role != Qt.DisplayRole:  # type: ignore
            return None
        if orientation == Qt.Horizontal:  # type: ignore
            return str(self._df.columns[section])
        return str(section + 1)

    def df(self) -> pd.DataFrame:
        return self._df


class CountriesFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name_contains = ""
        self._continent = "Tous"
        self._year: int | None = None
        self._ranges: dict[str, tuple[float | None, float | None]] = {}
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)  # type: ignore

    def set_name_contains(self, text: str):
        self._name_contains = (text or "").strip().lower()
        self.invalidateFilter()

    def set_continent(self, continent: str):
        self._continent = continent or "Tous"
        self.invalidateFilter()

    def set_year(self, year: int | None):
        self._year = year
        self.invalidateFilter()

    def set_range(self, col: str, vmin: float | None, vmax: float | None):
        self._ranges[col] = (vmin, vmax)
        self.invalidateFilter()

    def clear_ranges(self):
        self._ranges = {}
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if model is None:
            return True

        df = model.df()  # type: ignore
        row = df.iloc[source_row]

        if self._name_contains:
            if self._name_contains not in str(row[COUNTRY_COL]).lower():
                return False

        if self._continent != "Tous":
            if str(row[CONTINENT_COL]) != self._continent:
                return False

        if self._year is not None:
            try:
                if int(row[YEAR_COL]) != int(self._year):
                    return False
            except Exception:
                return False

        for col, (vmin, vmax) in self._ranges.items():
            if col not in df.columns:
                continue
            val = row[col]
            if pd.isna(val):
                return False
            try:
                val = float(val)
            except Exception:
                return False
            if vmin is not None and val < vmin:
                return False
            if vmax is not None and val > vmax:
                return False

        return True


class CountriesWidget(QWidget):
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.df = df

        self.model = PandasTableModel(df)
        self.proxy = CountriesFilterProxy(self)
        self.proxy.setSourceModel(self.model)

        layout = QVBoxLayout(self)

        filters_box = QGroupBox("Filtres")
        filters_layout = QHBoxLayout(filters_box)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Rechercher un pays…")
        self.name_input.textChanged.connect(self.proxy.set_name_contains)

        self.continent_combo = QComboBox()
        self.continent_combo.addItem("Tous")
        continents = sorted([c for c in df[CONTINENT_COL].dropna().unique().tolist()])
        for c in continents:
            self.continent_combo.addItem(str(c))
        self.continent_combo.currentTextChanged.connect(self.proxy.set_continent)

        self.year_combo = QComboBox()
        self.year_combo.addItem("Toutes")
        years = sorted([int(y) for y in df[YEAR_COL].dropna().unique().tolist()])
        for y in years:
            self.year_combo.addItem(str(y))

        def on_year_change(text: str):
            if text == "Toutes":
                self.proxy.set_year(None)
            else:
                self.proxy.set_year(int(text))

        self.year_combo.currentTextChanged.connect(on_year_change)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_filters)

        filters_layout.addWidget(QLabel("Pays:"))
        filters_layout.addWidget(self.name_input, 2)
        filters_layout.addWidget(QLabel("Continent:"))
        filters_layout.addWidget(self.continent_combo, 1)
        filters_layout.addWidget(QLabel("Année:"))
        filters_layout.addWidget(self.year_combo, 1)
        filters_layout.addWidget(self.reset_btn)

        layout.addWidget(filters_box)

        # Filtres numériques
        numeric_box = QGroupBox("Filtres numériques")
        numeric_layout = QHBoxLayout(numeric_box)

        # Filtres fixes (bonheur/PIB/santé)
        self.fixed_spins = {}
        self._add_range_filter(
            numeric_layout, label="Bonheur", col=HAPPINESS_COL, store=True
        )
        self._add_range_filter(numeric_layout, label="PIB", col=GDP_COL, store=True)
        self._add_range_filter(
            numeric_layout, label="Santé", col=HEALTH_COL, store=True
        )

        # Filtre custom
        self.custom_col_combo = QComboBox()
        self.custom_col_combo.addItem("— colonne —")

        numeric_cols = []
        for col in df.columns:
            if col == YEAR_COL:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_cols.append(col)
        numeric_cols = sorted(numeric_cols)

        for col in numeric_cols:
            self.custom_col_combo.addItem(col)

        self.custom_min = QDoubleSpinBox()
        self.custom_min.setRange(-1e9, 1e9)
        self.custom_min.setDecimals(3)
        self.custom_min.setSpecialValueText("—")
        self.custom_min.setValue(self.custom_min.minimum())

        self.custom_max = QDoubleSpinBox()
        self.custom_max.setRange(-1e9, 1e9)
        self.custom_max.setDecimals(3)
        self.custom_max.setSpecialValueText("—")
        self.custom_max.setValue(self.custom_max.minimum())

        def apply_custom_range():
            col = self.custom_col_combo.currentText()
            if col == "— colonne —":
                return
            vmin = (
                None
                if self.custom_min.value() == self.custom_min.minimum()
                else float(self.custom_min.value())
            )
            vmax = (
                None
                if self.custom_max.value() == self.custom_max.minimum()
                else float(self.custom_max.value())
            )
            self.proxy.set_range(col, vmin, vmax)

        def on_custom_col_change(_):
            self.custom_min.blockSignals(True)
            self.custom_max.blockSignals(True)
            self.custom_min.setValue(self.custom_min.minimum())
            self.custom_max.setValue(self.custom_max.minimum())
            self.custom_min.blockSignals(False)
            self.custom_max.blockSignals(False)

        self.custom_col_combo.currentTextChanged.connect(on_custom_col_change)
        self.custom_min.valueChanged.connect(apply_custom_range)
        self.custom_max.valueChanged.connect(apply_custom_range)

        numeric_layout.addWidget(QLabel("Filtre custom:"))
        numeric_layout.addWidget(self.custom_col_combo, 1)
        numeric_layout.addWidget(QLabel("min"))
        numeric_layout.addWidget(self.custom_min)
        numeric_layout.addWidget(QLabel("max"))
        numeric_layout.addWidget(self.custom_max)

        layout.addWidget(numeric_box)

        # Compteur de résultats
        self.results_label = QLabel("")
        layout.addWidget(self.results_label)
        self._update_results_label()

        # Met à jour le compteur quand les filtres changent
        self.proxy.modelReset.connect(self._update_results_label)
        self.proxy.layoutChanged.connect(self._update_results_label)
        self.proxy.rowsInserted.connect(self._update_results_label)
        self.proxy.rowsRemoved.connect(self._update_results_label)

        # Table
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)  # tri par clic sur entête
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)  # type: ignore
        self.table.setSelectionMode(QTableView.SingleSelection)  # type: ignore
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.table, 1)

    def _update_results_label(self):
        shown = self.proxy.rowCount()
        total = self.model.rowCount()
        self.results_label.setText(f"{shown} ligne(s) affichée(s) / {total} total")

    def reset_filters(self):
        # Texte / combos
        self.name_input.setText("")
        self.continent_combo.setCurrentText("Tous")
        self.year_combo.setCurrentText("Toutes")

        # Reset ranges (proxy)
        self.proxy.clear_ranges()

        # Reset spins fixes
        for col, (min_spin, max_spin) in self.fixed_spins.items():
            min_spin.blockSignals(True)
            max_spin.blockSignals(True)
            min_spin.setValue(min_spin.minimum())
            max_spin.setValue(max_spin.minimum())
            min_spin.blockSignals(False)
            max_spin.blockSignals(False)

        # Reset custom
        self.custom_col_combo.setCurrentIndex(0)
        self.custom_min.setValue(self.custom_min.minimum())
        self.custom_max.setValue(self.custom_max.minimum())

        self._update_results_label()

    def _add_range_filter(
        self, parent_layout: QHBoxLayout, label: str, col: str, store: bool = False
    ):
        if col not in self.df.columns:
            return

        box = QHBoxLayout()
        box.addWidget(QLabel(f"{label} min"))
        min_spin = QDoubleSpinBox()
        min_spin.setRange(-1e9, 1e9)
        min_spin.setDecimals(3)
        min_spin.setSpecialValueText("—")
        min_spin.setValue(min_spin.minimum())
        box.addWidget(min_spin)

        box.addWidget(QLabel("max"))
        max_spin = QDoubleSpinBox()
        max_spin.setRange(-1e9, 1e9)
        max_spin.setDecimals(3)
        max_spin.setSpecialValueText("—")
        max_spin.setValue(max_spin.minimum())
        box.addWidget(max_spin)

        def on_change():
            vmin = (
                None
                if min_spin.value() == min_spin.minimum()
                else float(min_spin.value())
            )
            vmax = (
                None
                if max_spin.value() == max_spin.minimum()
                else float(max_spin.value())
            )
            self.proxy.set_range(col, vmin, vmax)
            self._update_results_label()

        min_spin.valueChanged.connect(on_change)
        max_spin.valueChanged.connect(on_change)

        parent_layout.addLayout(box)

        if store:
            self.fixed_spins[col] = (min_spin, max_spin)
