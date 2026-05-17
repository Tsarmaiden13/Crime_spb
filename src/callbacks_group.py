from dash import Input, Output
from charts import create_group_bar_chart
from charts_calendar import create_calendar_heatmap


def register_group_callbacks(app, crime_data):
    @app.callback(
        Output("groups_chart", "figure"),
        Output("calendar_heatmap_groups", "figure"),
        Input("groups_year_slider", "value"),
        Input("calendar_metric_dropdown", "value"),
    )
    def update_groups(selected_year, selected_metric):
        groups_fig = create_group_bar_chart(crime_data, selected_year)
        calendar_fig = create_calendar_heatmap(crime_data, selected_metric)
        return groups_fig, calendar_fig
