import pandas as pd
import psycopg2


conn = psycopg2.connect(
    host="localhost",
    dbname="crime_spb",
    user="postgres",
    password="0000",
    port=5432,
)

print("Подключение к базе прошло успешно")

excel_data = "C:\\Users\\Olga\\Диплом\\Мой проект\\data\\raw\\r648qi1biheqw8kwlt6g36a1y9ee59r4.xlsx"
crime_data = pd.read_excel(excel_data)

print("Файл прочитан")
print("Размер таблицы:", crime_data.shape)
print(crime_data.head())

conn.close()