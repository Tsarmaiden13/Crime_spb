from dash import Dash, Input, Output, dcc, html
import dash_bootstrap_components as dbc

from data_loader import load_crime_data, get_metric_options, get_year_options
from layout import create_layout
from layout_groups import create_groups_layout
from callbacks import register_callbacks
from callbacks_group import register_group_callbacks
from upload_callbacks import register_upload_callbacks
from monthly_mode_callbacks import register_monthly_mode_callbacks


crime_data = load_crime_data()
metric_options = get_metric_options(crime_data)
year_options = get_year_options(crime_data)

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)
app.title = "Crime_spb Dashboard"
server = app.server

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
    ]
)


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def display_page(pathname):
    if pathname == "/groups":
        return create_groups_layout(metric_options, year_options)
    return create_layout(metric_options, year_options)


register_callbacks(app, crime_data)
register_group_callbacks(app, crime_data)
register_upload_callbacks(app)
register_monthly_mode_callbacks(app, crime_data)


if __name__ == "__main__":
    app.run(debug=True)
    # app.run(
    #     debug=False,
    #     dev_tools_ui=False,
    #     dev_tools_props_check=False
    # )