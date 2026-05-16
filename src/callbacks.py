from dash import Input, Output, html
from charts import (
    create_empty_figure,
    create_year_comparison_chart,
    create_trend_chart,
)


def register_callbacks(app, crime_data):
    crime_data = crime_data.copy()

    crime_data = crime_data.rename(
        columns={
            "metriccode": "metric_code",
            "metricname": "metric_name",
            "monthlyvalue": "monthly_value",
        }
    )

    if "year" in crime_data.columns:
        crime_data["year"] = crime_data["year"].astype(int)

    if "month" in crime_data.columns:
        crime_data["month"] = crime_data["month"].astype(int)

    needed_cols = ["metric_code", "year", "month", "monthly_value"]
    missing_cols = [col for col in needed_cols if col not in crime_data.columns]

    if missing_cols:
        raise ValueError(
            f"В crime_data отсутствуют обязательные колонки: {missing_cols}"
        )

    if "is_partial_first_month" not in crime_data.columns:
        crime_data["is_partial_first_month"] = False

    @app.callback(
        Output("kpi_card", "children"),
        Output("comparison_chart", "figure"),
        Output("trend_chart", "figure"),
        Input("metric_dropdown", "value"),
        Input("year_dropdown", "value"),
    )
    def update_dashboard(selected_metric, selected_year):
        if selected_metric is None or selected_year is None:
            empty_chart = create_empty_figure("Выберите показатель и год")

            kpi_card = [
                html.H3("Нет данных для отображения", style={"color": "#ffffff"}),
                html.P(
                    "Сначала выберите показатель и год.",
                    style={"color": "#d7e2f0"},
                ),
            ]

            return kpi_card, empty_chart, empty_chart

        selected_year = int(selected_year)

        selected_data = crime_data[
            (crime_data["metric_code"] == selected_metric)
            & (crime_data["year"] == selected_year)
        ].copy()

        if selected_data.empty:
            empty_chart = create_empty_figure("Нет данных")

            kpi_card = [
                html.H3("Нет данных", style={"color": "#ffffff"}),
                html.P(
                    "Для выбранного показателя данные отсутствуют.",
                    style={"color": "#d7e2f0"},
                ),
            ]

            return kpi_card, empty_chart, empty_chart

        if "metric_name" in selected_data.columns and not selected_data["metric_name"].isna().all():
            metric_name = selected_data["metric_name"].iloc[0]
        else:
            metric_name = selected_metric

        kpi_data = selected_data[
            ~(
                (selected_data["is_partial_first_month"])
                & (selected_data["month"] != 1)
            )
        ].copy()

        if kpi_data.empty:
            total_value = 0
        else:
            total_value = kpi_data["monthly_value"].sum()

        kpi_card = [
            html.H3(f"{metric_name} — {selected_year}", style={"color": "#ffffff"}),
            html.P(
                f"Сумма всего: {total_value:,.0f}".replace(",", " "),
                style={"color": "#d7e2f0"},
            ),
        ]

        comparison_chart = create_year_comparison_chart(crime_data, selected_metric)
        trend_chart = create_trend_chart(crime_data, selected_metric, selected_year)

        return kpi_card, comparison_chart, trend_chart