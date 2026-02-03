This project was started with [supopo-pai-cookiecutter-template](https://github.com/ClementPinard/supop-pai-cookiecuttter-template/tree/main)

## HapSight

HappySight is a desktop application developed in Python to explore and analyze **world happiness** and **corruption perception** data over the period **2015–2020**.

This project was developed as part of a course.

---

## Project Objectives

The main goal of HappySight is to provide an interactive tool that allows users to:

- visualize data using an **interactive world map**,
- explore the dataset through a **filterable and sortable table**,
- generate **statistical graphs**,
- compare multiple countries over time,
- analyze **correlations** between happiness and socio-economic indicators.

---

## Dataset

The project uses the **World Happiness & Corruption (2015–2020)** dataset from Kaggle, which includes:
- 132 countries,
- 6 years (2015 to 2020),
- multiple indicators such as happiness score, GDP per capita, health, freedom, generosity, and corruption perception.

All data are loaded into a **single Pandas DataFrame**, which is shared across all application modules to ensure consistency between views.

---

## Contributing to the Project

Contributions are encouraged within a pedagogical context.

---

## How to run

⚠️ Chose one of the two method below, and remove the other one.

### How to run with PySide

```bash
uv run hapsight
```

## Development

### How to run pre-commit

```bash
uvx pre-commit run -a
```

Alternatively, you can install it so that it runs before every commit :

```bash
uvx pre-commit install
```

### How to run tests

```bash
uv sync --group test
uv run pytest
```

### How to run type checking

```bash
uvx pyright hapsight --pythonpath .venv/bin/python
```

### How to build docs

```bash
uv sync --group docs
cd docs && uv run make html
```

#### How to run autobuild for docs

```bash
uv sync --group docs
cd docs && make livehtml
