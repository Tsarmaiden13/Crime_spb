import os
import calendar
from datetime import date

import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Не задана переменная окружения {name}")
    return value

MONTHS = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}

# соответствие строка в отчете - группа/название/код
metrics = {
    "В С Е Г О": (
        "Общая преступность",
        "Всего преступлений",
        "total_crimes",
    ),
    "ВСЕГО РАСКРЫТО": (
        "Раскрываемость",
        "Всего раскрыто",
        "solved_crimes",
    ),
    "ТЯЖКИЕ И ОСОБО ТЯЖКИЕ": (
        "Тяжкие и особо тяжкие",
        "Всего тяжких и особо тяжких преступлений",
        "serious_total",
    ),
    "ПРЕСТУПЛ.ЭКОНОМИЧЕСКОЙ НАПРАВЛЕННОСТИ": (
        "Экономические преступления",
        "Всего преступлений экономической направленности",
        "econ_total",
    ),
    "НЕЗАКОННЫМ ОБОРОТОМ НАРКОТИК": (
        "Наркопреступления",
        "Всего преступлений, связанных с незаконным оборотом наркотиков",
        "drugs_total",
    ),
    "ПРЕСТУПЛЕНИЯ ПРОТИВ СОБСТВЕННОСТИ": (
        "Преступления против собственности",
        "Всего преступлений против собственности",
        "property_total",
    ),
    "КРАЖА (ВСЕГО) СТ.158": (
        "Кражи",
        "Всего краж (ст. 158)",
        "theft_total",
    ),
}

base = r"C:\Users\Olga\Диплом\Мой проект"
raw_dir = os.path.join(base, "data", "raw")

url = "https://epp.genproc.gov.ru/ru/proc_78/activity/statistics/office/other/"
period_type = "month_cum"
file_type = "xlsx"


def get_period(fname: str):
    name = os.path.splitext(fname)[0]
    parts = name.split("_")

    if len(parts) == 2:
        start_month = 1
        end_month = int(parts[0])
        year = int(parts[1])
    elif len(parts) == 3:
        start_month = int(parts[0])
        end_month = int(parts[1])
        year = int(parts[2])
    else:
        raise ValueError(f"Не разобрать период: {fname}")

    start_date = date(year, 1, 1)
    last_day = calendar.monthrange(year, end_month)[1]
    end_date = date(year, end_month, last_day)

    if start_month == end_month:
        label = f"{MONTHS[end_month]} {year}"
    else:
        label = f"{MONTHS[start_month]}-{MONTHS[end_month]} {year}"

    return start_date, end_date, label


def get_sort_key(fname: str):
    name = os.path.splitext(fname)[0]
    parts = name.split("_")

    if len(parts) == 2:
        end_month = int(parts[0])
        year = int(parts[1])
    else:
        end_month = int(parts[1])
        year = int(parts[2])

    return year, end_month


def main():
    conn = psycopg2.connect(
        host=get_env("CRIME_DB_HOST"),
        dbname=get_env("CRIME_DB_NAME"),
        user=get_env("CRIME_DB_USER"),
        password=get_env("CRIME_DB_PASSWORD"),
        port=int(get_env("CRIME_DB_PORT")),
    )
    cur = conn.cursor()

    new_reports = 0
    new_metrics = 0
    skipped_reports = 0

    all_files = [
        f
        for f in os.listdir(raw_dir)
        if f.lower().endswith(".xlsx") and f.startswith("01_")
    ]
    all_files.sort(key=get_sort_key)

    print("Найдены файлы:")
    for f in all_files:
        print(" -", f)

    for fname in all_files:
        xls_path = os.path.join(raw_dir, fname)
        print(f"\nОбрабатываю файл: {fname}")

        try:
            period_start, period_end, label = get_period(fname)
        except ValueError as err:
            print(f"  Пропускаю (непонятное имя файла): {err}")
            continue

        cur.execute(
            """
            SELECT id
            FROM reports
            WHERE period_start = %s
              AND period_end = %s
              AND source_url = %s
            """,
            (period_start, period_end, url),
        )
        row = cur.fetchone()

        if row:
            print(
                f"  Отчёт за {label} уже есть в БД "
                f"(report_id = {row[0]}), пропускаю."
            )
            skipped_reports += 1
            continue

        try:
            data = pd.read_excel(xls_path, header=None)
        except Exception as err:
            print(f"  Ошибка чтения, пропускаю файл: {err}")
            continue

        print(f"  Таблица: {data.shape[0]} строк, {data.shape[1]} столбцов")

        title = (
            "Основные сведения о состоянии преступности на территории "
            f"Санкт-Петербурга за {label}"
        )

        cur.execute(
            """
            INSERT INTO reports (
                title,
                source_url,
                period_label,
                period_start,
                period_end,
                period_type,
                file_type,
                local_path
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                title,
                url,
                label,
                period_start,
                period_end,
                period_type,
                file_type,
                xls_path,
            ),
        )

        report_id = cur.fetchone()[0]
        new_reports += 1
        added_for_report = 0

        print(f"Создан отчёт report_id = {report_id} для периода {label}")

        for _, row in data.iterrows():
            text = " ".join(str(x).strip() for x in row if pd.notna(x))
            if not text:
                continue

            for key, (met_group, met_name, met_code) in metrics.items():
                if key not in text:
                    continue

                try:
                    value = row.iloc[3]
                except IndexError:
                    value = None

                if pd.isna(value):
                    print(f"Нет значения для {met_code} в файле {fname}")
                    continue

                cur.execute(
                    """
                    INSERT INTO crime_city (
                        report_id,
                        city_name,
                        period_start,
                        period_end,
                        period_type,
                        metric_group,
                        metric_name,
                        metric_code,
                        value,
                        unit
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        report_id,
                        "Санкт-Петербург",
                        period_start,
                        period_end,
                        period_type,
                        met_group,
                        met_name,
                        met_code,
                        value,
                        "count",
                    ),
                )

                added_for_report += 1
                new_metrics += 1
                print(f"Добавила метрику {met_code}: {value}")
                break

        print(f"Всего метрик для отчёта: {added_for_report}")

    conn.commit()

    print("\nИмпорт завершён")
    print(f"Новых отчётов: {new_reports}")
    print(f"Пропущено отчётов: {skipped_reports}")
    print(f"Новых метрик: {new_metrics}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()