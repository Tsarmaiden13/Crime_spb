import os
from datetime import date
import calendar

import pandas as pd
import psycopg2

# подключение к базе
conn = psycopg2.connect(
    host="localhost",
    dbname="crime_spb",
    user="postgres",
    password="0000",
    port=5432,
)
cur = conn.cursor()

# мой проект
base = r"C:\Users\Olga\Диплом\Мой проект"
raw = os.path.join(base, "data", "raw")

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

def get_period(fname: str):
    name = os.path.splitext(fname)[0]
    parts = name.split("_")

    if len(parts) == 2:
        start_m = 1
        end_m = int(parts[0])
        year = int(parts[1])
    elif len(parts) == 3:
        start_m = int(parts[0])
        end_m = int(parts[1])
        year = int(parts[2])
    else:
        raise ValueError(f"Не разобрать период: {fname}")

    d_start = date(year, 1, 1)
    last_day = calendar.monthrange(year, end_m)[1]
    d_end = date(year, end_m, last_day)

    if start_m == end_m:
        label = f"{MONTHS[end_m]} {year}"
    else:
        label = f"{MONTHS[start_m]}-{MONTHS[end_m]} {year}"

    return d_start, d_end, label


# метьрики
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

url = "https://epp.genproc.gov.ru/ru/proc_78/activity/statistics/office/other/"
p_type = "month_cum"
f_type = "xlsx"

new_rep = 0
new_met = 0
skip_rep = 0

# берём все нужные файлы эксель
all_files = [
    f for f in os.listdir(raw)
    if f.lower().endswith(".xlsx") and f.startswith("01_")
]

def get_sort_key(fname):
    name = os.path.splitext(fname)[0]
    parts = name.split("_")
    if len(parts) == 2:
        end_m = int(parts[0])
        year = int(parts[1])
    else:
        end_m = int(parts[1])
        year = int(parts[2])
    return (year, end_m)

all_files.sort(key=get_sort_key)

print("Найдены файлы для импорта:")
for f in all_files:
    print(" -", f)

for fname in all_files:
    xls_path = os.path.join(raw, fname)
    print(f"\n=== Обрабатываем файл: {xls_path}")

    # период отчёта по имени файла
    try:
        d_start, d_end, label = get_period(fname)
    except ValueError as e:
        print(f"  Пропускаем (непонятное имя файла): {e}")
        continue

    # проверяем, есть ли отчёт уже в БД
    cur.execute(
        """
        SELECT id FROM reports
        WHERE period_start = %s
          AND period_end = %s
          AND source_url = %s
        """,
        (d_start, d_end, url),
    )
    row = cur.fetchone()

    if row:
        print(
            f"  Отчёт за период {label} уже есть в БД (report_id = {row[0]}), пропускаем."
        )
        skip_rep += 1
        continue

    try:
        data = pd.read_excel(xls_path, header=None)
    except Exception as e:
        print(f"  Ошибка чтения Excel, пропускаем файл: {e}")
        continue

    title = (
        f"Основные сведения о состоянии преступности на территории "
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
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id;
        """,
        (
            title,
            url,
            label,
            d_start,
            d_end,
            p_type,
            f_type,
            xls_path,
        ),
    )

    rep_id = cur.fetchone()[0]
    new_rep += 1
    print(f"  Создан отчёт report_id = {rep_id} для периода {label}")

    added_met = 0

    # перебираем строки Excel
    for _, row in data.iterrows():
        vals = [str(x).strip() for x in row.tolist() if pd.notna(x)]
        if not vals:
            continue

        txt = " ".join(vals)

        for key, (met_group, met_name, met_code) in metrics.items():
            if key in txt:
                value = None

                try:
                    value = row.iloc[3]
                except IndexError:
                    value = None

                if value is None or (isinstance(value, float) and pd.isna(value)):
                    print(
                        f"  Не нашли значение для '{met_code}' "
                        f"в строке с ключом '{key}' в файле {fname}"
                    )
                    continue

                # записываем в таблицу crime_city
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
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                    """,
                    (
                        rep_id,
                        "Санкт-Петербург",
                        d_start,
                        d_end,
                        p_type,
                        met_group,
                        met_name,
                        met_code,
                        value,
                        "count",
                    ),
                )

                added_met += 1
                new_met += 1
                print(f"    Добавили метрику '{met_code}' со значением {value}")
                break

    print(f"  Всего метрик для этого отчёта: {added_met}")

conn.commit()

print(
    f"\nИмпорт завершён."
    f"\n  Новых отчётов создано: {new_rep}"
    f"\n  Отчётов пропущено (уже были): {skip_rep}"
    f"\n  Всего новых метрик добавлено: {new_met}"
)

cur.close()
conn.close()