import pandas as pd
import plotly.graph_objects as go


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

MONTH_COLORS = {
    1: "#66c2ff",
    2: "#7bdff2",
    3: "#8ce99a",
    4: "#b8f2a1",
    5: "#ffd166",
    6: "#f9c74f",
    7: "#f9844a",
    8: "#f94144",
    9: "#c77dff",
    10: "#9d4edd",
    11: "#577590",
    12: "#43aa8b",
}


def prepare_chart_data(crime_data: pd.DataFrame) -> pd.DataFrame:
    chart_data = crime_data.copy()

    chart_data = chart_data.rename(
        columns={
            "metriccode": "metric_code",
            "metricname": "metric_name",
            "monthlyvalue": "monthly_value",
        }
    )

    if "year" in chart_data.columns:
        chart_data["year"] = pd.to_numeric(chart_data["year"], errors="coerce")

    if "month" in chart_data.columns:
        chart_data["month"] = pd.to_numeric(chart_data["month"], errors="coerce")

    if "monthly_value" in chart_data.columns:
        chart_data["monthly_value"] = pd.to_numeric(
            chart_data["monthly_value"], errors="coerce"
        )

    return chart_data


def build_base_layout(title: str) -> dict:
    return dict(
        title=title,
        template="plotly_dark",
        paper_bgcolor="#182230",
        plot_bgcolor="#182230",
        font=dict(color="white"),
        title_x=0.5,
        margin=dict(l=40, r=20, t=60, b=40),
        height=420,
        xaxis=dict(
            title="Месяц",
            tickmode="array",
            tickvals=list(MONTH_LABELS.keys()),
            ticktext=list(MONTH_LABELS.values()),
            range=[0.5, 12.5],
        ),
        yaxis=dict(title="Значение"),
    )


def create_empty_figure(title: str):
    chart = go.Figure()
    chart.update_layout(**build_base_layout(title))
    chart.add_annotation(
        text="Нет данных для отображения",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=16, color="white"),
    )
    return chart


def complete_months(chart_data: pd.DataFrame, value_col: str) -> pd.DataFrame:
    months_data = pd.DataFrame({"month": list(MONTH_LABELS.keys())})
    chart_data = months_data.merge(chart_data, on="month", how="left")

    if value_col in chart_data.columns:
        chart_data[value_col] = pd.to_numeric(chart_data[value_col], errors="coerce")

    return chart_data


def create_monthly_chart(crime_data, selected_metric, selected_year):
    chart_data = prepare_chart_data(crime_data)

    selected_data = chart_data[
        (chart_data["metric_code"] == selected_metric)
        & (chart_data["year"] == int(selected_year))
    ].copy()

    selected_data = selected_data.dropna(
        subset=["month", "monthly_value"]
    ).sort_values("month")

    if selected_data.empty:
        return create_empty_figure(f"Помесячная динамика, {selected_year}")

    monthly_data = (
        selected_data.groupby("month", as_index=False)
        .agg(monthly_value=("monthly_value", "sum"))
        .sort_values("month")
    )

    monthly_data = complete_months(monthly_data, "monthly_value")

    bar_colors = [
        MONTH_COLORS.get(int(month), "#66c2ff") for month in monthly_data["month"]
    ]

    chart = go.Figure(
        data=[
            go.Bar(
                x=monthly_data["month"].tolist(),
                y=monthly_data["monthly_value"].tolist(),
                marker_color=bar_colors,
                marker_line_width=0,
                name=str(selected_year),
                customdata=[[MONTH_LABELS[month]] for month in monthly_data["month"]],
                hovertemplate="Месяц: %{customdata[0]}<br>Значение: %{y}<extra></extra>",
            )
        ]
    )

    chart.update_layout(**build_base_layout(f"Помесячная динамика, {selected_year}"))
    return chart


def create_year_comparison_chart(crime_data, selected_metric):
    chart_data = prepare_chart_data(crime_data)

    selected_data = chart_data[chart_data["metric_code"] == selected_metric].copy()
    selected_data = selected_data.dropna(
        subset=["year", "month", "monthly_value"]
    ).sort_values(["year", "month"])

    if selected_data.empty:
        return create_empty_figure("Сравнение по годам")

    chart = go.Figure()

    for year in sorted(selected_data["year"].dropna().unique()):
        year = int(year)
        year_data = selected_data[selected_data["year"] == year].copy()

        monthly_data = (
            year_data.groupby("month", as_index=False)
            .agg(monthly_value=("monthly_value", "sum"))
            .sort_values("month")
        )

        monthly_data = complete_months(monthly_data, "monthly_value")

        chart.add_trace(
            go.Scatter(
                x=monthly_data["month"].tolist(),
                y=monthly_data["monthly_value"].tolist(),
                mode="lines+markers",
                name=str(year),
                marker=dict(size=8),
                customdata=[
                    [MONTH_LABELS[month]] for month in monthly_data["month"]
                ],
                hovertemplate=(
                    "Год: " + str(year)
                    + "<br>Месяц: %{customdata[0]}<br>Значение: %{y}<extra></extra>"
                ),
                connectgaps=False,
            )
        )

    if len(chart.data) == 0:
        return create_empty_figure("Сравнение по годам")

    chart.update_layout(**build_base_layout("Сравнение по годам"))
    chart.update_layout(legend=dict(title="Год"))
    return chart


def create_trend_chart(crime_data, selected_metric, selected_year):
    chart_data = prepare_chart_data(crime_data)

    selected_data = chart_data[
        (chart_data["metric_code"] == selected_metric)
        & (chart_data["year"] == int(selected_year))
    ].copy()

    selected_data = selected_data.dropna(
        subset=["month", "monthly_value"]
    ).sort_values("month")

    if selected_data.empty:
        return create_empty_figure(f"Тренд, {selected_year}")

    monthly_data = (
        selected_data.groupby("month", as_index=False)
        .agg(monthly_value=("monthly_value", "sum"))
        .sort_values("month")
    )

    monthly_data = complete_months(monthly_data, "monthly_value")

    monthly_data["rolling_mean_3"] = (
        monthly_data["monthly_value"].rolling(window=3, min_periods=1).mean()
    )

    chart = go.Figure()

    chart.add_trace(
        go.Scatter(
            x=monthly_data["month"].tolist(),
            y=monthly_data["monthly_value"].tolist(),
            mode="lines+markers",
            name="Факт",
            line=dict(color="#6ec1ff", width=2),
            marker=dict(size=8),
            customdata=[[MONTH_LABELS[month]] for month in monthly_data["month"]],
            hovertemplate="Месяц: %{customdata[0]}<br>Значение: %{y}<extra></extra>",
            connectgaps=False,
        )
    )

    chart.add_trace(
        go.Scatter(
            x=monthly_data["month"].tolist(),
            y=monthly_data["rolling_mean_3"].tolist(),
            mode="lines+markers",
            name="Среднее (3 мес.)",
            line=dict(color="#ff6b6b", width=2, dash="dash"),
            marker=dict(size=7),
            customdata=[[MONTH_LABELS[month]] for month in monthly_data["month"]],
            hovertemplate="Месяц: %{customdata[0]}<br>Среднее: %{y:.2f}<extra></extra>",
            connectgaps=False,
        )
    )

    chart.update_layout(
        title=f"Тренд, {selected_year}",
        template="plotly_dark",
        paper_bgcolor="#182230",
        plot_bgcolor="#182230",
        font=dict(color="white"),
        title_x=0.5,
        margin=dict(l=40, r=20, t=80, b=40),
        height=420,
        xaxis=dict(
            title="Месяц",
            tickmode="array",
            tickvals=list(MONTH_LABELS.keys()),
            ticktext=list(MONTH_LABELS.values()),
            range=[0.5, 12.5],
        ),
        yaxis=dict(title="Значение"),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
    )

    return chart


def get_group_totals_by_year(crime_data, selected_year):
    chart_data = prepare_chart_data(crime_data)

    if selected_year is None:
        return pd.DataFrame(columns=["metric_group", "year_total"])

    if (
        "year" not in chart_data.columns
        or "metric_group" not in chart_data.columns
        or "monthly_value" not in chart_data.columns
    ):
        return pd.DataFrame(columns=["metric_group", "year_total"])

    chart_data["year"] = pd.to_numeric(chart_data["year"], errors="coerce")
    selected_data = chart_data[
        chart_data["year"] == pd.to_numeric(selected_year, errors="coerce")
    ].copy()

    if selected_data.empty:
        return pd.DataFrame(columns=["metric_group", "year_total"])

    selected_data = selected_data.dropna(subset=["metric_group", "monthly_value"])

    group_totals = (
        selected_data.groupby("metric_group", as_index=False)
        .agg(year_total=("monthly_value", "sum"))
        .sort_values("year_total", ascending=False)
    )

    return group_totals


def create_group_bar_chart(crime_data, selected_year):
    group_totals = get_group_totals_by_year(crime_data, selected_year)

    if group_totals.empty:
        return create_empty_figure(
            f"Структура преступности по группам, {selected_year}"
        )

    colors = [
        "#66c2ff",
        "#7bdff2",
        "#8ce99a",
        "#ffd166",
        "#f9844a",
        "#c77dff",
        "#577590",
        "#43aa8b",
    ]

    chart = go.Figure(
        data=[
            go.Bar(
                x=group_totals["year_total"].tolist(),
                y=group_totals["metric_group"].tolist(),
                orientation="h",
                marker=dict(
                    color=colors[: len(group_totals)],
                    line=dict(color="rgba(255,255,255,0.18)", width=1),
                ),
                text=[
                    f"{x:,.0f}".replace(",", " ")
                    for x in group_totals["year_total"]
                ],
                textposition="outside",
                hovertemplate="%{y}<br>Сумма за год: %{x:,.0f}<extra></extra>",
            )
        ]
    )

    chart.update_layout(
        title=f"Структура преступности по группам, {selected_year}",
        template="plotly_dark",
        paper_bgcolor="#182230",
        plot_bgcolor="#182230",
        font=dict(color="white"),
        title_x=0.5,
        margin=dict(l=40, r=40, t=60, b=40),
        height=520,
        xaxis=dict(title="Сумма за год"),
        yaxis=dict(
            title="Группа преступлений",
            categoryorder="total ascending",
        ),
    )

    return chart