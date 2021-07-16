import dash
import dash_html_components as html
import dash_core_components as dcc
from sqlalchemy import create_engine
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
import plotly.graph_objects as go

pd.options.display.max_columns = 999

# get the data:
engine = create_engine(
    "mysql+pymysql://seb:Pass_word@3.19.73.138:3306/idealista", echo=False
)
df = pd.read_sql("SELECT * FROM property", con=engine)

# create list for dropdown:
drop_list = [{"label": x, "value": x} for x in df.district.unique() if x is not None]
drop_list = [
    {"label": "All", "value": "All"}
] + drop_list  # adding 'All' option for dropdown

# avg price by area for district: -> prepare plot
pba = df.groupby("district")["priceByArea"].mean().sort_values(ascending=False)
pba_fig = px.bar(pba, hover_data=["value"], color="value", height=600)
pba_fig.update_xaxes(title_font=dict(size=18, family="Courier", color="black"))
pba_fig.update_yaxes(title_font=dict(size=18, family="Courier", color="black"))


# Let's define the figure for
fig_bar = px.bar(
    pba,
    hover_data=["value"],
    color="value",
    height=600,
    color_continuous_scale="Bluered",
)
fig_bar.update_xaxes(title_font=dict(size=20, family="Raleway", color="black"))
fig_bar.update_yaxes(title_font=dict(size=20, family="Raleway", color="black"))
fig_bar.add_shape(  # add a horizontal "target" line
    type="line",
    line_color="salmon",
    line_width=3,
    opacity=1,
    line_dash="dot",
    x0=0,
    x1=1,
    xref="paper",
    y0=pba.mean(),
    y1=pba.mean(),
    yref="y",
)

# valuation per district:
def categorizer(row, pba):
    if row["district"] is None:
        return None
    if row["priceByArea"] > 1.05 * pba[row["district"]]:
        return "overpriced"
    elif row["priceByArea"] < 0.95 * pba[row["district"]]:
        return "underpriced"
    else:
        return "average"


df["valuation"] = df.apply(lambda x: categorizer(x, pba), axis=1)

# create list for price dropdown
drop_list_price = [
    {"label": "All", "value": "All"},
    {"label": "Cheap (less than 1 Mio EUR)", "value": 1},
    {"label": "Medium (less than 2 Mio EUR)", "value": 2},
    {"label": "Expensive (more than 2 Mio EUR)", "value": 3},
]

# dash:
app = dash.Dash("dashboard")

# layout:
app.layout = html.Div(
    className="layout",
    children=[
        html.H1(className="title", children="Final project Datawarehousing"),
        html.H3(className="subsubtitle", children="By Elio, Buelent and Simon"),
        html.H3("Average price per area across districts", className="subtitle"),
        dcc.Graph(id="barplot", figure=fig_bar),
        html.H3("What district are you interested in?", className="subtitle"),
        dcc.Dropdown(
            id="district_dropdown",
            options=drop_list,
            value="All",
            style={"marginBottom": 50},
        ),
        html.H3("Set your preferred price range", className="subtitle"),
        dcc.Dropdown(
            id="price_dropdown",
            options=drop_list_price,
            value="All",
            style={"marginBottom": 50},
        ),
        html.Div(
            className="dcc_components",
            children=[
                dcc.Graph(id="clustermap", figure={}, style={"margin-left": "450px"}),
                dcc.Textarea(
                    id="textarea",
                    value="Textarea content initialized\nwith multiple lines of text",
                    style={
                        "width": "36%",
                        "height": 480,
                        "marginBottom": 70,
                        "marginTop": -1500,
                        "border": "none",
                    },
                    readOnly=True,
                ),
            ],
        ),
        html.Div(id="textarea-example-output", style={"whiteSpace": "pre-line"}),
    ],
)

# callback:
# Input for the callback: dropdown
# Output of the callback is the clustermap figure:


@app.callback(
    Output("clustermap", "figure"),
    [Input("district_dropdown", "value"), Input("price_dropdown", "value")],
)
def update_output(value, value_price):
    # filter district
    if value == "All":
        df_filtered = df.copy()
    else:
        df_filtered = df[df["district"] == value]
    # filter price range
    if value_price == 1:  # cheap == 1:
        df_filtered = df_filtered[df_filtered.price < 1000000]
    elif value_price == 2:  # medium == 2:
        df_filtered = df_filtered[df_filtered.price < 2000000]
    elif value_price == 3:  # expensive == 3:
        df_filtered = df_filtered[df_filtered.price >= 2000000]
    # Map figure
    df_filtered["text"] = (
        "Price/m2 :"
        + " "
        + df_filtered["priceByArea"].astype(str)
        + " "
        + "€/m2"
        + ", "
        + "Value :"
        + " "
        + df_filtered["valuation"].astype(str)
        + " "
        + ", "
        + "Property Code :"
        + " "
        + df_filtered["propertyCode"].astype(str)

    )
    scatt = go.Scattermapbox(
        lat=df_filtered.latitude,
        lon=df_filtered.longitude,
        text=df_filtered["text"],
        hovertext=df_filtered["text"],
        hoverinfo="text",
        marker=dict(
            size=5,
            opacity=0.8,
            reversescale=False,
            autocolorscale=False,
            colorscale="Bluered",
            color=df_filtered["priceByArea"],
            cmin=df_filtered["priceByArea"].min(),
            cmax=df_filtered["priceByArea"].max(),
            colorbar_title="Price per Meter Squared",
        ),
    )
    layout = go.Layout(
        mapbox=dict(
            center=dict(lat=41.386914, lon=2.170000), zoom=10.5, style="stamen-terrain"
        )
    )
    fig = go.Figure(data=scatt, layout=layout)
    return fig


@app.callback(
    Output("textarea", "value"),
    [Input("district_dropdown", "value"), Input("price_dropdown", "value")],
)
def update_text(value, value_price):
    # prepare filtered dataset
    if value == "All":
        df_filtered = df.copy()
    else:
        df_filtered = df[df["district"] == value]

    # filter price range
    if value_price == 1:
        df_filtered = df_filtered[df_filtered.price < 1000000]
    elif value_price == 2:
        df_filtered = df_filtered[df_filtered.price < 2000000]
    elif value_price == 3:
        df_filtered = df_filtered[df_filtered.price >= 2000000]

    # early stoppage if empty dataset:
    if len(df_filtered) == 0:
        return (
            "Too many filters! - For the desired category there is no data available."
            "Please choose a different price range/district."
        )

    # Now we filter for the entry that has the lowest price per area:
    df_filtered_low = df_filtered.sort_values("priceByArea", ascending=True).iloc[0, :]

    property_details = {
        "Property code": df_filtered_low["propertyCode"],
        "Property type": df_filtered_low["propertyType"],
        "Address": df_filtered_low["address"],
        "Price": df_filtered_low["price"],
        "Size": df_filtered_low["size"],
        "Price by area": df_filtered_low["priceByArea"],
        "Rooms": df_filtered_low["rooms"],
        "Bathrooms": df_filtered_low["bathrooms"],
        "Valuation": df_filtered_low["valuation"],
    }

    text = (
        "The property with the lowest price per area in your preferred neighborhood and price range is:"
        "\n\nProperty"
        " code: "
        + str(property_details["Property code"])
        + "\nAddress: "
        + str(property_details["Address"])
        + "\nProperty type: "
        + str(property_details["Property type"])
        + "\n\nProperty details:"
        + "\n\nPrice: "
        + str(property_details["Price"])
        + "\nSize: "
        + str(property_details["Size"])
        + "\nPrice by area: "
        + str(property_details["Price by area"])
        + "\nRooms: "
        + str(property_details["Rooms"])
        + "\nBathrooms: "
        + str(property_details["Bathrooms"])
        + "\nValuation: "
        + str(property_details["Valuation"])
        + "\n\n"
        + "A property is underpriced if its price by area is less than 95% of the respective district average "
        + "and overpriced if its price per area exceeds the corresponding district average by more than 5%."
    )

    return text


# print statement for terminal
print("Code runs through")


#app.run_server(debug=True)