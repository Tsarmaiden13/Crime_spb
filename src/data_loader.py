import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


BD_CRIME = {
    "host": "localhost",
    "port": 5432,
    "database": "crime_spb",
    "user": "postgres",
    "password": "0000",
}

KPI_CODES = [
    "total_crimes",
    "serious_total",
    "econ_total",
    "theft_total",
    "property_total",
    "drugs_total",
    "solved_crimes",
]

KPI_LABELS = {
    "total_crimes": "Всего преступлений",
    "serious_total": "Тяжкие и особо тяжкие",
    "econ_total": "Экономические преступления",
    "theft_total": "Кражи",
    "property_total": "Преступления против собственности",
    "drugs_total": "Наркопреступления",
    "solved_crimes": "Раскрытые преступления",
}

MONTH_LABELS = {
    1: "Янв",
    2: "Фев",
    3: "Мар",
    4: "Апр",
    5: "Май",
    6: "Июн",
    7: "Июл",
    8: "Авг",
    9: "Сен",
    10: "Окт",
    11: "Ноя",
    12: "Дек",
}


def get_engine():
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=BD_CRIME["user"],
        password=BD_CRIME["password"],
        host=BD_CRIME["host"],
        port=BD_CRIME["port"],
        database=BD_CRIME["database"],
    )
    return create_engine(url)


def load_crime_data():
    engine = get_engine()

    query = """
        SELECT
            city_name,
            period_start,
            period_end,
            year,
            month,
            metric_group,
            metric_code,
            metric_name,
            value,
            monthly_value
        FROM crime_spb2
        WHERE metric_code IN (
            'total_crimes',
            'serious_total',
            'econ_total',
            'theft_total',
            'property_total',
            'drugs_total',
            'solved_crimes'
        )
        ORDER BY year, month, metric_code
    """

    crime_data = pd.read_sql(query, con=engine)

    if "year" in crime_data.columns:
        crime_data["year"] = pd.to_numeric(crime_data["year"], errors="coerce")

    if "month" in crime_data.columns:
        crime_data["month"] = pd.to_numeric(crime_data["month"], errors="coerce")

    if "value" in crime_data.columns:
        crime_data["value"] = pd.to_numeric(crime_data["value"], errors="coerce")

    if "monthly_value" in crime_data.columns:
        crime_data["monthly_value"] = pd.to_numeric(
            crime_data["monthly_value"], errors="coerce"
        )
    else:
        crime_data["monthly_value"] = crime_data["value"]

    if "metric_code" in crime_data.columns:
        crime_data["metric_code"] = crime_data["metric_code"].astype(str).str.strip()
        crime_data = crime_data[crime_data["metric_code"].isin(KPI_CODES)].copy()

    crime_data["metric_name"] = crime_data["metric_code"].map(KPI_LABELS)

    if "month" in crime_data.columns:
        crime_data["month_name"] = crime_data["month"].map(MONTH_LABELS)

    return crime_data


def get_metric_options(crime_data):
    if "metric_code" not in crime_data.columns:
        return []

    available_codes = [
        code for code in KPI_CODES
        if code in crime_data["metric_code"].dropna().unique()
    ]

    return [
        {
            "label": KPI_LABELS.get(code, code),
            "value": code,
        }
        for code in available_codes
    ]


def get_year_options(crime_data):
    if "year" not in crime_data.columns:
        return []

    years = sorted(crime_data["year"].dropna().unique())

    return [
        {
            "label": str(int(year)),
            "value": int(year),
        }
        for year in years
    ]
