"""Data loading and emission calculation pipeline."""

import logging
import math
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# Resolve data paths relative to the repository root.
_REPO_ROOT = Path(__file__).parent.parent.parent
_DATA_DIR = _REPO_ROOT / "data"


def _resolve_data_path(filename: str) -> Path | None:
    candidate = _DATA_DIR / filename
    if candidate.exists():
        return candidate
    return None

# myClimate emission factors: Economy kg CO₂eq per km per passenger (incl. RFI)
# Source: myClimate Flight Emission Calculator methodology
_ECO_FACTORS: dict[str, float] = {
    "short": 0.255,   # < 1 500 km
    "medium": 0.185,  # 1 500–3 700 km
    "long": 0.147,    # ≥ 3 700 km
}
_BUSINESS_MULTIPLIER = 2.0

_SWISS_IATAS = {"ZRH", "GVA", "BSL", "BRN", "MLH", "LUZ", "SIR", "ACH", "BXO"}

_HAUL_MAP: dict[str, str] = {
    "Kurzstreckenflug": "short",
    "Mittelstreckenflug": "medium",
    "Langstreckenflug": "long",
    "Short-Haul": "short",
    "Medium-Haul": "medium",
    "Long-Haul": "long",
}

# (filename, sheet_name, source_year)
_FILES: list[tuple[str, str, int]] = [
    ("flugliste-rumba-2020-de.xlsx", " Flugliste Liste des vols", 2020),
    ("flugliste-rumba-2021-fr.xlsx", " Flugliste Liste des vols", 2021),
    ("flugliste-rumba-2022 (1).xlsx", " Flugliste Liste des vols", 2022),
    ("Flugliste_2023.xlsx", " Flugliste Liste des vols", 2023),
    ("Flugliste 2024 (3).xlsx", "Flugliste", 2024),
]

# Normalise the bilingual column names across all files to a single canonical name.
# Both the German-only and the bilingual variants are mapped.
_COL_MAP: dict[str, str] = {
    "Flughafen Abflug (A)\nAéroport de départ (A)\n": "departure_airport",
    "Flughafen Abflug (A)\nA\ufffdroport de d\ufffdpart (A)\n": "departure_airport",
    "IATA-Code (A)": "iata_from",
    "Flughafen Ankunft (B)\nAéroport d'arrivée (B)": "arrival_airport",
    "Flughafen Ankunft (B)\nA\ufffdroport d'arriv\ufffde (B)": "arrival_airport",
    "IATA-Code (B)": "iata_to",
    "Enddestination\nDestination finale": "final_destination",
    "Monat\nMois": "date_raw",
    "Klasse\nClasse": "class_",
    "Departement\nDépartement": "department",
    "Departement\nD\ufffdpartement": "department",
    "Verwaltungseinheit\nUnité administrative": "unit",
    "Verwaltungseinheit\nUnit\ufffd administrative": "unit",
    "RUMBA/RUMS\nRUMBA/SMEA": "rumba_rums",
    "Direkte Fluglinie (km) Trajectoire de vol \ndirecte (km)": "distance_km",
    # 2021–2022 use two-category column name; values still include 'Mittelstrecke'
    "Kurz-/Langstreckenflug\nVol court/long-courrier": "haul_type_raw",
    # 2023–2024 use three-category column name
    "Kurz-/Mittel-/Langstreckenflug\nVol court/moyen/long-courrier": "haul_type_raw",
    "Teilstrecke eines Gabelfluges\nParcours partiel d'un vol de correspondance": "is_connecting",
}


def _load_single(filename: str, sheet: str, year: int) -> pd.DataFrame:
    path = _resolve_data_path(filename)
    if path is None:
        logger.warning("Data file not found: %s (searched %s)", filename, _DATA_DIR)
        return pd.DataFrame()

    df = pd.read_excel(path, sheet_name=sheet, header=0)
    df = df.rename(columns=_COL_MAP)

    # Keep only known canonical columns that exist in this file.
    # Use dict.fromkeys to deduplicate while preserving order (haul_type_raw
    # appears twice in _COL_MAP values since two source columns share one target).
    known = list(dict.fromkeys(c for c in _COL_MAP.values() if c in df.columns))
    df = df[known].copy()

    df["source_year"] = year
    return df


def _compute_co2(df: pd.DataFrame) -> pd.DataFrame:
    df["haul_type"] = df["haul_type_raw"].map(_HAUL_MAP)
    unmapped = df["haul_type"].isna().sum()
    if unmapped:
        logger.warning("%d rows have unmapped haul_type", unmapped)

    factor = df["haul_type"].map(_ECO_FACTORS).fillna(_ECO_FACTORS["long"])
    multiplier = df["class_"].map({"Economy": 1.0, "Business": _BUSINESS_MULTIPLIER}).fillna(1.0)
    df["co2_kg"] = (df["distance_km"] * factor * multiplier).round(1)
    return df


def _load_airports() -> pd.DataFrame:
    path = _resolve_data_path("airports.csv")
    if path is None:
        logger.warning("airports.csv not found in %s", _DATA_DIR)
        return pd.DataFrame(columns=["iata", "lat", "lon", "name", "city", "country"])

    # OpenFlights format: no header row
    cols = ["id", "name", "city", "country", "iata", "icao", "lat", "lon",
            "altitude", "tz_offset", "dst", "tz", "type", "source"]
    airports = pd.read_csv(path, header=None, names=cols, low_memory=False)
    airports = airports[airports["iata"].notna() & (airports["iata"] != "\\N")]
    return airports[["iata", "name", "city", "country", "lat", "lon"]].drop_duplicates("iata")


@st.cache_data(show_spinner="Lade Flugdaten …")
def load_flights() -> pd.DataFrame:
    """Load and merge all five flight-list Excel files.

    Returns a DataFrame with canonical columns plus computed co2_kg.
    Results are cached by Streamlit between reruns.
    """
    frames = [_load_single(fn, sheet, yr) for fn, sheet, yr in _FILES]
    frames = [f for f in frames if not f.empty]
    if not frames:
        logger.error("No flight data loaded — check data dir: %s", _DATA_DIR)
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df = _compute_co2(df)

    # Normalise is_connecting to bool (missing in 2021/2022)
    if "is_connecting" in df.columns:
        df["is_connecting"] = (
            df["is_connecting"]
            .map({"Ja": True, "Nein": False, True: True, False: False})
            .astype("boolean")
            .fillna(False)
            .astype(bool)
        )
    else:
        df["is_connecting"] = False

    logger.info("Loaded %d flight legs across years %s", len(df), sorted(df["source_year"].unique()))
    return df


def add_destination_country(df: pd.DataFrame, airports: pd.DataFrame) -> pd.DataFrame:
    """Add a destination-country column based on arrival airport IATA codes.

    Args:
        df: Flight legs dataframe.
        airports: Airports lookup with IATA and country columns.

    Returns:
        Copy of df with a dest_country column.
    """
    if df.empty:
        return df.copy()

    if "dest_country" in df.columns:
        return df.copy()

    if airports.empty or "iata" not in airports.columns:
        enriched = df.copy()
        enriched["dest_country"] = "Unbekannt"
        return enriched

    country_map = airports.set_index("iata")["country"].to_dict()
    enriched = df.copy()
    enriched["dest_country"] = enriched["iata_to"].map(country_map).fillna("Unbekannt")
    return enriched


def filter_flights(
    df: pd.DataFrame,
    year: int | None = None,
    department: str | None = None,
    dest_country: str | None = None,
    swiss_only: bool = False,
) -> pd.DataFrame:
    """Filter flight legs by year, department, destination country, and origin scope.

    Args:
        df: Flight legs dataframe.
        year: Optional year filter.
        department: Optional department filter.
        dest_country: Optional destination-country filter.
        swiss_only: Limit to Swiss departure airports when True.

    Returns:
        Filtered dataframe copy.
    """
    if df.empty:
        return df.copy()

    mask = pd.Series(True, index=df.index)
    if swiss_only:
        mask &= df["iata_from"].isin(_SWISS_IATAS)
    if year is not None:
        mask &= df["source_year"] == year
    if department and department != "Alle":
        mask &= df["department"] == department
    if dest_country and dest_country != "Alle":
        if "dest_country" not in df.columns:
            logger.warning("dest_country filter requested but column missing")
        else:
            mask &= df["dest_country"] == dest_country

    return df[mask].copy()


@st.cache_data(show_spinner=False)
def load_airports() -> pd.DataFrame:
    """Return airports lookup with iata, lat, lon, name, city, country."""
    return _load_airports()


@st.cache_data(show_spinner=False)
def yearly_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total CO₂ per year in tonnes."""
    return (
        df.groupby("source_year")["co2_kg"]
        .sum()
        .div(1000)
        .round(1)
        .reset_index()
        .rename(columns={"source_year": "year", "co2_kg": "co2_t"})
    )


@st.cache_data(show_spinner=False)
def top_routes(
    df: pd.DataFrame,
    year: int | None = None,
    department: str | None = None,
    dest_country: str | None = None,
    top_n: int = 50,
    swiss_only: bool = False,
) -> pd.DataFrame:
    """Return top-N routes aggregated from flight legs.

    Args:
        df: Flight legs dataframe.
        year: Optional year filter.
        department: Optional department filter.
        dest_country: Optional destination-country filter.
        top_n: Number of routes to return (sorted by CO2).
        swiss_only: Limit to Swiss departure airports when True.

    Returns:
        Aggregated routes dataframe for the arc-map.
    """
    sub = filter_flights(
        df,
        year=year,
        department=department,
        dest_country=dest_country,
        swiss_only=swiss_only,
    )
    if sub.empty:
        return pd.DataFrame()

    agg = (
        sub.groupby(["iata_from", "departure_airport", "iata_to", "arrival_airport",
                     "final_destination"])
        .agg(co2_kg=("co2_kg", "sum"), trips=("co2_kg", "count"))
        .reset_index()
        .sort_values("co2_kg", ascending=False)
        .head(top_n)
    )
    return agg


@st.cache_data(show_spinner=False)
def globe_routes(
    df: pd.DataFrame,
    airports: pd.DataFrame,
    year: int | None = None,
    department: str | None = None,
    dest_country: str | None = None,
    top_n: int = 120,
    swiss_only: bool = False,
) -> list[dict[str, object]]:
    """Return aggregated routes with coordinates for the rotating globe.

    Args:
        df: Flight legs dataframe.
        airports: Airports lookup with iata, lat, lon.
        year: Optional year filter.
        department: Optional department filter.
        dest_country: Optional destination-country filter.
        top_n: Number of routes to include (sorted by CO2).
        swiss_only: Limit to Swiss departure airports when True.

    Returns:
        List of dicts containing from/to coordinates and CO2 per route.
    """
    if df.empty or airports.empty:
        return []

    routes = top_routes(
        df,
        year=year,
        department=department,
        dest_country=dest_country,
        top_n=top_n,
        swiss_only=swiss_only,
    )
    if routes.empty:
        return []

    ap = airports.set_index("iata")
    rows: list[dict[str, object]] = []
    for idx, row in routes.iterrows():
        iata_from = row["iata_from"]
        iata_to = row["iata_to"]
        if iata_from not in ap.index or iata_to not in ap.index:
            continue

        src = ap.loc[iata_from]
        dst = ap.loc[iata_to]
        dest_name = row["final_destination"]
        if pd.isna(dest_name) or not str(dest_name).strip():
            dest_name = row["arrival_airport"]

        rows.append({
            "id": f"{iata_from}-{iata_to}-{idx}",
            "from": [float(src["lat"]), float(src["lon"])],
            "to": [float(dst["lat"]), float(dst["lon"])],
            "co2": float(row["co2_kg"]),
            "trips": int(row["trips"]),
            "from_name": str(row["departure_airport"]),
            "to_name": str(dest_name),
        })

    return rows


# ── Personal emissions helpers (Chapter 5) ──────────────────────────────────

# Haul-type thresholds matching the source data labels (short < 1 500 km,
# medium < 3 700 km, otherwise long). Same logic as _HAUL_MAP applied to
# numeric distances.
_SHORT_MAX_KM = 1_500.0
_MEDIUM_MAX_KM = 3_700.0


def _haul_for_km(distance_km: float) -> str:
    if distance_km < _SHORT_MAX_KM:
        return "short"
    if distance_km < _MEDIUM_MAX_KM:
        return "medium"
    return "long"


def co2_for_distance(distance_km: float, class_: str = "Economy") -> float:
    """Estimate CO₂eq in kg for a single flight leg of given distance and class.

    Uses the same myClimate factors as the pipeline (_ECO_FACTORS) and the
    Business multiplier (_BUSINESS_MULTIPLIER). Haul-type is derived from
    distance via the 1 500 / 3 700 km thresholds.

    Args:
        distance_km: Great-circle distance of the leg in kilometres.
        class_: "Economy" or "Business". Anything else is treated as Economy.

    Returns:
        Emissions in kg CO₂eq for a single passenger on this leg.
    """
    if distance_km <= 0:
        return 0.0
    factor = _ECO_FACTORS[_haul_for_km(distance_km)]
    multiplier = _BUSINESS_MULTIPLIER if class_ == "Business" else 1.0
    return distance_km * factor * multiplier


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points in kilometres.

    Args:
        lat1: Latitude of point 1 in degrees.
        lon1: Longitude of point 1 in degrees.
        lat2: Latitude of point 2 in degrees.
        lon2: Longitude of point 2 in degrees.

    Returns:
        Distance in kilometres (Earth radius = 6 371 km).
    """
    r_km = 6_371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r_km * math.asin(math.sqrt(a))


def avg_leg_metrics(df: pd.DataFrame, year: int) -> dict[str, float]:
    """Mean distance and CO₂ per flight leg for a given source year.

    Args:
        df: Flight legs dataframe (output of load_flights).
        year: source_year to filter on.

    Returns:
        Dict with keys n_legs (int as float), mean_distance_km, mean_co2_kg.
        Zero values when the filtered slice is empty.
    """
    sub = df[df["source_year"] == year]
    if sub.empty:
        return {"n_legs": 0.0, "mean_distance_km": 0.0, "mean_co2_kg": 0.0}
    return {
        "n_legs": float(len(sub)),
        "mean_distance_km": float(sub["distance_km"].mean()),
        "mean_co2_kg": float(sub["co2_kg"].mean()),
    }


def route_distance_km(
    airports: pd.DataFrame, iata_from: str, iata_to: str
) -> float | None:
    """Great-circle distance between two airports identified by IATA code.

    Args:
        airports: Airports lookup with iata, lat, lon.
        iata_from: Origin IATA code.
        iata_to: Destination IATA code.

    Returns:
        Distance in kilometres, or None if either code is not in the lookup.
    """
    if airports.empty or not iata_from or not iata_to:
        return None
    ap = airports.set_index("iata")
    if iata_from not in ap.index or iata_to not in ap.index:
        return None
    src = ap.loc[iata_from]
    dst = ap.loc[iata_to]
    return haversine_km(float(src["lat"]), float(src["lon"]),
                        float(dst["lat"]), float(dst["lon"]))
