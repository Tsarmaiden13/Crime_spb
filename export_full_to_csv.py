import os
import pandas as pd
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    dbname="crime_spb",
    user="postgres",
    password="0000",
    port=5432,
)

join_sql = """
SELECT
    r.id              AS report_id,
    r.period_label,
    r.period_start,
    r.period_end,
    r.period_type     AS report_period_type,
    r.file_type,
    c.id              AS crime_id,
    c.city_name,
    c.period_type     AS crime_period_type,
    c.metric_group,
    c.metric_name,
    c.metric_code,
    c.value,
    c.unit
FROM reports r
JOIN crime_city c ON c.report_id = r.id
ORDER BY r.period_start, c.metric_code;
"""

crime_df = pd.read_sql(join_sql, conn)
print("Строк в датафрейме:", crime_df.shape[0])
print(crime_df.head())

base = r"C:\Users\Olga\Диплом\Мой проект"
out_dir = os.path.join(base, "data", "processed")
os.makedirs(out_dir, exist_ok=True)

csv_path = os.path.join(out_dir, "crime_full.csv")
crime_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

print("Общий CSV сохранён:", csv_path)

conn.close()