import numpy as np
import plotly.graph_objects as go
from dash import Input, Output


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
    1: "#5ec2ff",
    2: "#7ad3ff",
    3: "#8be28b",
    4: "#ffd166",
    5: "#ffb86b",
    6: "#ff8c69",
    7: "#c77dff",
    8: "#72efdd",
    9: "#90be6d",
    10: "#f9c74f",
    11: "#f9844a",
    12: "#f94144",
}


def register_monthly_callbacks(app, crime_data):
    chart_data = crime_data.copy()
    chart_data = chart_data.sort_values(["metric_code", "month", "year"])

    previous_values = chart_data.groupby(["metric_code", "month"])["monthly_value"].shift(1)
    chart_data["yoy_rate"] = ((chart_data["monthly_value"] / previous_values) - 1) * 100
    chart_data.loc[
        (previous_values.isna())
        | (previous_values == 0)
        | (chart_data["monthly_value"].isna()),
        "yoy_rate",
    ] = np.nan

    @app.callback(
        Output("monthly_chart", "figure"),
        Input("metric_dropdown", "value"),
        Input("year_dropdown", "value"),
        Input("monthly_view_switch", "value"),
    )
    def update_monthly_chart(selected_metric, selected_year, selected_mode):
        selected_data = chart_data[
            (chart_data["metric_code"] == selected_metric)
            & (chart_data["year"] == int(selected_year))
        ].copy()

        selected_data = selected_data.sort_values("month")
        selected_data["month_name"] = selected_data["month"].map(MONTH_LABELS)

        chart = go.Figure()

        if selected_mode == "growth":
            chart.add_trace(
                go.Scatter(
                    x=selected_data["month_name"],
                    y=selected_data["yoy_rate"],
                    mode="lines+markers",
                    name="Темп роста",
                    line=dict(color="#6ec1ff", width=3),
                    marker=dict(size=8, color="#6ec1ff"),
                    hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
                    connectgaps=False,
                )
            )

            chart.add_hline(y=0, line_dash="dash", line_color="gray")
            title = f"Темп роста, {selected_year} к {int(selected_year) - 1}"
            yaxis_title = "Темп роста, %"

        else:
            bar_colors = [MONTH_COLORS.get(month, "#6ec1ff") for month in selected_data["month"]]

            chart.add_trace(
                go.Bar(
                    x=selected_data["month_name"],
                    y=selected_data["monthly_value"],
                    name="Уровень",
                    marker=dict(
                        color=bar_colors,
                        line=dict(color="rgba(255,255,255,0.18)", width=1),
                    ),
                    hovertemplate="%{x}<br>%{y:.0f}<extra></extra>",
                )
            )

            title = f"Помесячная динамика, {selected_year}"
            yaxis_title = "Значение"

        chart.update_layout(
            template="plotly_dark",
            paper_bgcolor="#16202e",
            plot_bgcolor="#16202e",
            font=dict(color="#e8eef7"),
            margin=dict(l=50, r=30, t=60, b=40),
            title=title,
            xaxis_title="Месяц",
            yaxis_title=yaxis_title,
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )

        chart.update_xaxes(showgrid=False)
        chart.update_yaxes(
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
        )

        return chart
