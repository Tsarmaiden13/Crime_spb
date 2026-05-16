from dash import dcc, html
from upload_layout import create_upload_block


def create_layout(metric_options, year_options):
    available_years = [int(item["value"]) for item in year_options] if year_options else []
    min_year = min(available_years) if available_years else 2021
    max_year = max(available_years) if available_years else 2025
    selected_year = max_year

    year_marks = {
        int(year): {
            "label": "" if year == max_year else str(year),
            "style": {
                "color": "#ffffff",
                "fontWeight": "700",
                "textShadow": "0 1px 3px rgba(0, 0, 0, 0.65)",
            },
        }
        for year in available_years
    }

    chart_config = {
        "displaylogo": False,
        "toImageButtonOptions": {
            "format": "png",
            "filename": "crime_dashboard_chart",
            "height": 600,
            "width": 1000,
            "scale": 2,
        },
    }

    return html.Div(
        [
            html.H1("Преступность в Санкт-Петербурге"),
            html.Div(
                className="top-nav",
                children=[
                    dcc.Link("Главная", href="/", className="nav-link active-link"),
                    dcc.Link("Группы преступлений", href="/groups", className="nav-link"),
                ],
            ),
            html.Div(
                className="filters-row",
                children=[
                    html.Div(
                        className="filter-box",
                        children=[
                            html.Label("Выберите показатель"),
                            dcc.Dropdown(
                                id="metric_dropdown",
                                options=metric_options,
                                value=metric_options[0]["value"] if metric_options else None,
                                clearable=False,
                                style={
                                    "color": "#111111",
                                    "backgroundColor": "#ffffff",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        className="filter-box",
                        children=[
                            html.Label("Выберите год"),
                            dcc.Slider(
                                id="year_dropdown",
                                min=min_year,
                                max=max_year,
                                step=1,
                                value=selected_year,
                                marks=year_marks,
                                included=False,
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(id="kpi_card"),
            html.Div(
                className="charts-row",
                children=[
                    html.Div(
                        className="chart-wrapper",
                        children=[
                            html.Div(
                                className="chart-header-row",
                                children=[
                                    html.H3("Помесячный уровень преступности", className="chart-title"),
                                    dcc.RadioItems(
                                        id="monthly_view_switch",
                                        options=[
                                            {"label": "Уровень", "value": "level"},
                                            {"label": "Темп роста", "value": "growth"},
                                        ],
                                        value="level",
                                        inline=True,
                                        className="view-mode-switch",
                                        labelClassName="view-mode-option",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="chart-box",
                                children=[
                                    dcc.Graph(
                                        id="monthly_chart",
                                        config=chart_config,
                                        style={"height": "420px", "width": "100%"},
                                    )
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="chart-wrapper",
                        children=[
                            html.H3("Сравнение по годам", className="chart-title"),
                            html.Div(
                                className="chart-box",
                                children=[
                                    dcc.Graph(
                                        id="comparison_chart",
                                        config=chart_config,
                                        style={"height": "420px", "width": "100%"},
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="trend-section",
                children=[
                    html.H3("Долгосрочная динамика", className="chart-title"),
                    html.Div(
                        className="chart-box",
                        children=[
                            dcc.Graph(
                                id="trend_chart",
                                config=chart_config,
                                style={"height": "430px", "width": "100%"},
                            )
                        ],
                    ),
                ],
            ),
            create_upload_block(),
        ],
        className="main-container",
    )
