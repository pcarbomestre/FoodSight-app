
# Libraries
import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
import dash
from dash import Dash, dcc, html, Input, Output, callback, no_update
from dash.exceptions import PreventUpdate
import geopandas as gpd

import os
import pathlib
import re
import datetime

from shapely.geometry import Point
from geopandas.tools import sjoin
import math
import json
import numpy as np

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_daq as daq
import pandas as pd
from dash.dependencies import Input, Output, State



app = dash.Dash(__name__, external_stylesheets=['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'])

# Declare server for Heroku deployment. Needed for Procfile.
server = app.server


# -- Import and clean data (importing csv into pandas)
# df = pd.read_csv("intro_bees.csv")
# df = pd.read_csv("https://raw.githubusercontent.com/Coding-with-Adam/Dash-by-Plotly/master/Other/Dash_Introduction/intro_bees.csv")

# df = df.groupby(['State', 'ANSI', 'Affected by', 'Year', 'state_code'])[['Pct of Colonies Impacted']].mean()
# df.reset_index(inplace=True)
# print(df[:5])

# # ANPP data
# sw_hist_anpp_path = '/Users/polcarbo/Documents/Documents/2023/Work/Grasslands_UCSB_project/grasscast_project/data/additional_data/GrassCast_1982-2019_grid_ANPP_SW.xlsx'
# sw_hist_anpp = pd.read_excel(sw_hist_anpp_path, sheet_name= 'annual_1982-2019_grid_ANNP')
# sw_hist_anpp.head()

# # Grid
# # read shapefile
# southwest_shp_path = '/Users/polcarbo/Documents/Documents/2023/Work/Grasslands_UCSB_project/grasscast_project/data/shapefiles/southwest_grid/southwest_grid.shp'
# southwest_grid_raw = gpd.read_file(southwest_shp_path)
# southwest_grid_raw.head()
# # add the forcast data to the shapefile
# southwest_grid = southwest_grid_raw.merge(sw_hist_anpp, left_on='Id', right_on='gridID')
# southwest_grid.columns
# # Convert the CRS to EPSG:4326
# gdf = southwest_grid.to_crs(epsg=4326)

# gdf.columns

# selected_columns = ['Id', 'year', 'predicted_Spring_ANPP (lbs/ac)', 'geometry']
# subset = gdf[selected_columns]

# output_file = "/Users/polcarbo/Documents/Documents/2023/Work/Grasslands_UCSB_project/grasscast_project/grasscast_project/app_shp_data/app_shp_data.shp"

# # Save the GeoDataFrame to a Shapefile
# subset.to_file(output_file, driver='ESRI Shapefile')

# # Historic data
# gdf_path = 'app/app_data/hist_data/hist_data.shp'
# gdf = gpd.read_file(gdf_path)
# Forcast data
# df_forcast_path = 'app/app_data/forcast_data/pred_southwest_clean.csv'
# df_forcast = pd.read_csv(df_forcast_path)
# # Climate data
# gdf_clim_path = 'app/app_data/climate_data/swgrid/seasprcp_202306_swgrid.shp'
# gdf_clim = gpd.read_file(gdf_clim_path)

# Historic data
df_hist_path = 'src/app_data/postgre/hist_data_grasscast.csv'
df_hist = pd.read_csv(df_hist_path)
# Forcast data
df_forcast_path = 'src/app_data/postgre/forcast_data_grasscast.csv'
df_forcast = pd.read_csv(df_forcast_path)
# SW Grid
sw_grid_path = 'src/app_data/postgre/southwest_grid/southwest_grid.shp'
sw_grid = gpd.read_file(sw_grid_path).to_crs(epsg=4326)

# Merge for historical data map representation
gdf = sw_grid.merge(df_hist, left_on='gridID', right_on='gridID')
gdf_forcast = sw_grid.merge(df_forcast, left_on='gridID', right_on='gridID')
# Slider range
YEARS = gdf['year'].unique().tolist()

## Counties
sw_counties_path = 'src/app_data/postgre/sw_counties/sw_counties.shp'
sw_counties = gpd.read_file(sw_counties_path).to_crs(epsg=4326)

counties_list = sw_counties['NAME'].tolist()

# Mapbox token
token = open("src/.mapbox_token").read() # you will need your own token

def get_dropdown_options():
    return [{'label': i, 'value': i} for i in counties_list]

# ------------------------------------------------------------------------------
# Layout

app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            children=[
                html.Div(
                    id='header-title',
                    children=[
                        html.Div(  # Add new div to contain description and location-container
                            className='description-container',  # Add class here
                            children=[
                                html.P(
                                    id="description",
                                    children="Explore projected grassland Aboveground Net Primary Productivity (ANPP) in your area or anywhere across New Mexico and Arizona. Our forecast integrates anticipated weather patterns for the season to predict the production for spring and summer. Enhance your understanding by comparing present conditions with data from the past 36 years.",
                                ),
                                html.Div(
                                    id = "location-container",
                                    children=[
                                        html.Button(
                                            html.I(className="fa fa-crosshairs"), 
                                            id="update_btn",
                                            n_clicks=0,
                                        ),
                                        dcc.Geolocation(id="geolocation"),
                                        dcc.Dropdown(
                                            id='autocomplete-input',
                                            className='location-dropdown',
                                            options=get_dropdown_options(),
                                            value='none',
                                            multi=False,
                                            placeholder='Select County...',
                                            search_value=''
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        html.Div(
                            html.Img(id="logo", src=app.get_asset_url("logo.png")),
                            id="logo-link"  # Add a class to the <a> tag
                        ),
                    ]
                ),
            ],
        ),
        html.Div(
            id="app-container",
            children=[
                html.Div(
                    id="left-column",
                    children=[
                        html.Div(
                            [
                                html.Div(id='firstText', className='mini_container'),
                                html.Div(id='secondText', className='mini_container'),
                                html.Div(id='thirdText', className='mini_container'),
                                html.Div(id='fourthText', className='mini_container'),
                            ], 
                            id='info-container', className='row container-display'
                        ),
                        # html.Div(
                        #     id="slider-container",
                        #     children=[
                        #         html.P(
                        #             id="slider-text",
                        #             children="Drag the slider to change the year:",
                        #         ),
                        #         dcc.Slider(
                        #             id="slct_year",
                        #             min=min(YEARS),
                        #             max=max(YEARS),
                        #             value=max(YEARS),
                        #             step=1,
                        #             marks={
                        #                 str(year): {
                        #                     "label": str(year) if year % 5 == 0 else "",
                        #                     "style": {"color": "#7fafdf"},
                        #                 }
                        #                 for year in YEARS
                        #             },
                        #         ),
                        #     ],
                        # ),
                        html.Div(
                            id="graph-container",
                            children=[
                                html.P(
                                    id="output_text",
                                    children=[],
                                ),
                                dcc.Tabs(id="tabs", value='tab-1', children=[
                                    # dcc.Tab(label='Forcast', value='tab-2', children=[
                                    #     html.P(id="chart-selector", children="ANPP forcast"),
                                    #     daq.ToggleSwitch(
                                    #         id='my-toggle-switch',
                                    #         value=False,
                                    #         label='See scenarios',
                                    #         labelPosition='top'      
                                    #     ),
                                    #     dcc.Graph(id='line-plot-2', figure={}),
                                    # ]),
                                    dcc.Tab(label='Forecast', value='tab-1', 
                                        children=[
                                            html.Div(
                                                id="plot-and-switch-container",
                                                children=[
                                                html.Div([
                                                    html.Div(daq.BooleanSwitch(
                                                        id='my-toggle-switch',
                                                        on=False,
                                                        # label='See scenarios',
                                                        # labelPosition='right'
                                                    ), 
                                                    style={'display': 'inline-block', 'text-align': 'left', 
                                                            'padding-left':'3rem'}),
                                                ]),
                                                dcc.Graph(id='line-plot-2', figure={}),
                                        ]),
                                        ],
                                    ),
                                    dcc.Tab(label='Historical', value='tab-2', children=[
                                        html.Div(
                                            id="plot-and-slider-container",
                                            children=[
                                                dcc.Graph(id='line-plot', figure={}),
                                                dcc.Slider(
                                                    id="slct_year",
                                                    min=min(YEARS),
                                                    max=max(YEARS),
                                                    value=max(YEARS),
                                                    step=1,
                                                    marks={
                                                        str(min(YEARS)): {
                                                            "label": str(min(YEARS)),
                                                            "style": {"color": "#7fafdf"},
                                                        },
                                                        str(max(YEARS)): {
                                                            "label": str(max(YEARS)),
                                                            "style": {"color": "#7fafdf"},
                                                        }
                                                    },
                                                    tooltip = {
                                                        'always_visible': True,
                                                        "placement": "bottom" 
                                                    }
                                                ),
                                            ]
                                        ),
                                    ]),
                                ]),
                            ],
                        )
                    ],
                ),
                html.Div(
                    id="right-column",
                    children=[
                        html.Div(
                            id="heatmap-container",
                            children=[
                                html.P(
                                    id='output_container', 
                                    children=[]
                                ),
                                dcc.Graph(
                                    id='choropleth-map',
                                    config={'scrollZoom': True, 'displayModeBar': False, 'clickable': True}, 
                                    clickData = None, 
                                    figure={}
                                ),
                            ],
                        ), 
                        
                    ],
                ),
            ],
        ),
    ],
)


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components


# Autofill input

@app.callback(
    Output('output-div', 'children'),
    [Input('autocomplete-input', 'value')])
def update_output(value):
    return 'You have selected "{}"'.format(value)

# Geolocation

@app.callback(Output("geolocation", "update_now"), Input("update_btn", "n_clicks"))
def update_now(click):
    return True if click and click > 0 else False


@app.callback(
    Output("text_position", "children"),
    Input("geolocation", "local_date"),
    Input("geolocation", "position"),
)
def display_output(date, pos):
    if pos:
        point = Point(pos['lat'],pos['lon'])
        if sw_grid.contains(point).any():
            return html.P(
                f"As of {date} your location was: lat {pos['lat']},lon {pos['lon']}, accuracy {pos['accuracy']} meters",
            )
        else:
            return html.P(
                f"Your location ({pos['lat']},lon {pos['lon']}) falls outside the area of interest. For testing purposes we will use lat 35.6854, lon -105.9926"
            )
    return "No position data available"


# Update dropdown input based on user location
# NEEDS TO BE UPDATED TO REMOVE SELECTION IF MAP IS CLICKED
@app.callback(
    Output('autocomplete-input', 'value'),
    [Input('geolocation', 'position')]
)
def update_input(position):
    if position:
        point = Point(position['lat'], position['lon'])
        if sw_grid.contains(point).any():
            coordinates = [position['lat'], position['lon']]
        else:
            # Default coordinates if user is outside the SW area (For representation purposes)
            coordinates = [35.685421459731884, -105.99264908645465]

        point = Point(coordinates[1], coordinates[0])
        polygon = sw_counties.loc[sw_counties.geometry.contains(point)]
        if not polygon.empty:
            polygon_name = polygon['NAME'].values[0]
            dropdown_options = get_dropdown_options()
            if polygon_name in [option['value'] for option in dropdown_options]:
                return polygon_name
    # return None if position is not provided or if polygon_name is not in dropdown_options
    return None





# # Choropleth map
# @app.callback(
#     [Output(component_id='output_container', component_property='children'),
#      Output(component_id='choropleth-map', component_property='figure')],
#     [Input(component_id='slct_year', component_property='value')],
#     [State(component_id='choropleth-map', component_property='clickData')] # Update to highligh selected cell
# )
# def update_graph(option_slctd, clickData):
#     print(option_slctd)
#     print(type(option_slctd))

#     # Get the current month
#     current_month = datetime.datetime.now().month

#     # Set container and color according to the current month
#     if current_month in [4, 5]:  # April or May
#         container = "ANPP (lb/ac) for Spring {}".format(option_slctd)
#         color = 'predicted_Spring_ANPP (lbs/ac)'
#     else:
#         container = "ANPP (lb/ac) for Summer {}".format(option_slctd)
#         color = 'predicted_Summer_ANPP (lbs/ac)'


#     dff = gdf.copy()
#     dff = dff[dff["year"] == option_slctd]

#     # Create a Choropleth map
#     fig = px.choropleth_mapbox(
#         data_frame=dff,
#         geojson=dff.geometry,
#         locations=dff.index,
#         color=color,
#         color_continuous_scale="YlGnBu",
#         mapbox_style="carto-positron",
#         zoom=5, 
#         center = {"lat": dff['geometry'].centroid.y.mean(),
#                   "lon": dff['geometry'].centroid.x.mean()},
#         opacity=0.7,
#         labels={color:'ANPP (lbs/ac)'},
#         custom_data=['gridID'])
    
    
#     # df = df_hist[df_hist["year"] == option_slctd]
#     # dff = sw_grid.merge(df, left_on='gridID', right_on='gridID')
#     # # Create a Choropleth map
#     # fig = px.choropleth_mapbox(
#     #     data_frame=dff,
#     #     geojson=dff.geometry,
#     #     locations=dff.index,
#     #     color='predicted_Total_ANPP (lbs/ac)',
#     #     color_continuous_scale="YlGnBu",
#     #     mapbox_style="carto-positron",
#     #     zoom=5, 
#     #     center = {"lat": dff['geometry'].centroid.y.mean(),
#     #               "lon": dff['geometry'].centroid.x.mean()},
#     #     opacity=0.7,
#     #     labels={'predicted_Total_ANPP (lbs/ac)':'ANPP (lbs/ac)'},
#     #     custom_data=['Id'])
    
    
#     # Update contour properties
#     fig.update_traces(marker_line=dict(width=0))
    
#     # Update background color
#     fig.update_layout(
#             plot_bgcolor='rgba(0,0,0,0)',
#             paper_bgcolor='rgba(0,0,0,0)',
#         )

#     # # After generating the figure
#     # if clickData is not None:
#     #     selected_point = clickData['points'][0]['pointNumber']
#     #     fig.update_traces(selectedpoints=[selected_point])

#     return container, fig


@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='choropleth-map', component_property='figure'),
    #  Output(component_id='mean_value', component_property='children')
     ],
    [Input(component_id='slct_year', component_property='value'),
     Input(component_id='autocomplete-input', component_property='value')],
    [State(component_id='choropleth-map', component_property='clickData')] 
)
def update_graph(option_slctd, autocomplete, clickData):


    current_month = datetime.datetime.now().month

    if current_month in [4, 5]:  # April or May
        container = "ANPP (lb/ac) for Spring {}".format(option_slctd)
        color = 'predicted_Spring_ANPP (lbs/ac)'
    else:
        container = "ANPP (lb/ac) for Summer {}".format(option_slctd)
        color = 'predicted_Summer_ANPP (lbs/ac)'

    dff = gdf.copy()
    dff = dff[dff["year"] == option_slctd]

    # Create a Point with the given coordinates

    by_county = autocomplete

    # mean_value = "No data available"
    polygon_name = None

    if by_county:  # check if by_county is not empty
        if by_county in counties_list:  # check if by_county is in counties_list
            polygon = sw_counties.loc[sw_counties['NAME'] == by_county]
            if not polygon.empty:
                # getting the name of the polygon
                polygon_name = polygon['NAME'].values[0]

                # spatial join between the gdf and the polygon
                dff_polygon = sjoin(dff, polygon, how='inner', op='intersects')

                # calculate the mean value
                # mean_value = dff_polygon[color].mean()

                # Zoom in to polygon
                bounds = polygon.geometry.total_bounds  # get the bounding box
                center_lat = (bounds[1] + bounds[3]) / 2  # calculate the center latitude
                center_lon = (bounds[0] + bounds[2]) / 2  # calculate the center longitude
                # estimate the zoom level based on the size of the bounding box
                zoom = 7     
    else:  
        # mean_value = "Point does not belong to any polygon in sw_counties"

        # Zoom in to polygon
        polygon = sw_counties # To select all SW
        center_lat = polygon['geometry'].centroid.y.mean()  # calculate the center latitude
        center_lon = polygon['geometry'].centroid.x.mean()  # calculate the center longitude
        # estimate the zoom level based on the size of the bounding box
        zoom = 5
    

    fig = px.choropleth_mapbox(
        data_frame=dff,
        geojson=dff.geometry,
        locations=dff.index,
        color=color,
        color_continuous_scale="YlGnBu",
        mapbox_style="carto-positron",
        zoom=5, 
        center = {"lat": dff['geometry'].centroid.y.mean(),
                    "lon": dff['geometry'].centroid.x.mean()},
        opacity=0.6,
        labels={color:''},
        custom_data=['gridID'],
        range_color=(0, dff[color].max()),
    )

    fig.update_traces(marker_line=dict(width=0))

    fig.update_layout(
        mapbox_style="streets",
        mapbox_accesstoken=token,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_zoom=zoom,  # use the estimated zoom level
                    mapbox_center = {"lat": center_lat, 
                                    "lon": center_lon},
        coloraxis_colorbar=dict(
            len=0.8,  # Adjust this value to change the height of the colorbar
            x=0.85,  # x position (try adjusting this value to place it in your preferred location)
            y=0.5,  # y position (try adjusting this value to place it in your preferred location)
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return container, fig #, f"Mean value within buffer: {mean_value}, {polygon_name}"








# @app.callback(
#     Output(component_id='output-selected-value', component_property='children'),
#     [Input(component_id='choropleth-map', component_property='clickData')]
# )
# def display_selected_data(clickData): 
#     if clickData is None:
#         return "No data selected"
#     else:
#         # Extract the 'predicted_' and 'Id' values of the clicked point and return them
#         predicted_value = clickData['points'][0]['z']
#         id_value = clickData['points'][0]['customdata'][0]  # Extract the 'Id' from the custom data
#         return f"The selected 'predicted_' value is: {predicted_value}. The 'Id' value is: {id_value}."
# # Sustitute 'clickData' by 'selectedData' if you want to used values from box and lasso select



# Store intermedied data


# @app.callback(
#     Output(component_id='output_text', component_property='children'),
#     Output("firstText", "children"),
#     Output("secondText", "children"),
#     Output("thirdText", "children"),
#     Output("fourthText", "children"),
#     [Input(component_id='choropleth-map', component_property='clickData')]
# )
# def update_summary(clickData):
#     if clickData is None:
#         return "Select data on the map", "", "", ""
#     else:
#         id_value = clickData['points'][0]['customdata'][0]

#         # Load and filter your data here
#         dff = df_forcast.copy()

#         # Filter the data frame by the 'Id' selected from the map
#         df_plot = dff[dff['gridID'] == id_value]

#         # Select current year
#         current_year = datetime.datetime.now().year
#         df_plot = df_plot[df_plot['Year'] == current_year]

        
#         latest_date_rows = df_plot[df_plot['Date'] == df_plot['Date'].max()]

#         cat_descriptions = {
#             'Below': 'drier than normal',
#             'Above': 'rainier than normal',
#             'EC': 'normal',
#         }

#         for _, row in latest_date_rows.iterrows():
#             predict = row['NPP_predict_clim']
#             mean = row['meanANPPgrid']
#             cat = row['Cat']

#             cat_description = cat_descriptions[cat]

#             difference = predict - mean
#             percentage = (abs(difference) * 100) / mean

#             direction = "higher" if difference > 0 else "lower"

#             month = datetime.datetime.now().month
#             if 4 <= month <= 5:
#                 season = 'Spring'
#             elif 6 <= month <= 9:
#                 season = 'Summer'
#             else:
#                 season = 'Last season'

#             # Calculate the absolute difference between each value in the column and the predicted value
#             hist_data = df_hist.copy()

#             if season == 'Spring':
#                 hist_data['abs_diff'] = abs(hist_data['predicted_Spring_ANPP (lbs/ac)'] - predict)
#             else:
#                 hist_data['abs_diff'] = abs(hist_data['predicted_Summer_ANPP (lbs/ac)'] - predict)

#             # Find the row with the minimum absolute difference
#             most_similar_row = hist_data.loc[hist_data['abs_diff'].idxmin()]

#             # Access the year value from the most similar row
#             most_similar_year = most_similar_row['year']

#             text = (f"For this location, the expected production for the next weeks is about {predict} lb/ac. Being this season {cat_description}, the production is {percentage:.2f}% {direction} than expected")
#             first_box = (f"The expected production for this {season} is {round(predict,2)} lb/ac.")
#             second_box = (f"Weather is {cat_description}")
#             third_box = (f"The production is {round(percentage,2):.2f}% {direction} than expected")
#             fourth_box = (f"These conditions are most similar to those from {most_similar_year}")

#         # Show the graph
#         return text, first_box, second_box, third_box, fourth_box



@app.callback(
    Output(component_id='output_text', component_property='children'),
    Output("firstText", "children"),
    Output("secondText", "children"),
    Output("thirdText", "children"),
    Output("fourthText", "children"),
    [Input(component_id='choropleth-map', component_property='clickData'),
     Input(component_id='autocomplete-input', component_property='value')]
)
def update_summary(clickData, by_county):
    ctx = dash.callback_context

    # If nothing has triggered the callback yet, do nothing
    if not ctx.triggered:
        return go.Figure()

    # Identify which input triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'choropleth-map' and clickData is not None:
        id_value = clickData['points'][0]['customdata'][0]
        dff = df_forcast.copy()
        df_plot = dff[dff['gridID'] == id_value]
        current_year = datetime.datetime.now().year
        df_plot = df_plot[df_plot['Year'] == current_year]


    elif triggered_id == 'autocomplete-input' and by_county is not None:
        polygon = sw_counties.loc[sw_counties['NAME'] == by_county]
        columns_to_keep_forcast = ['gridID','Date','NPP_predict_below', 'NPP_predict_avg','NPP_predict_above',
                                'Cat', 'Prob','Year', 'NPP_predict_clim','meanANPPgrid','geometry']
        # spatial join between the gdf_forcast and the polygon
        dff_forcast_polygon = sjoin(gdf_forcast[columns_to_keep_forcast], polygon, how='inner', op='intersects')
        dff_forcast_polygon['Date'] = pd.to_datetime(dff_forcast_polygon['Date'])
        forcast_summaries = []
        for Date in dff_forcast_polygon['Date'].unique():
            dff_year = dff_forcast_polygon[dff_forcast_polygon['Date'] == Date]
            forcast_summary_dict = dff_year.iloc[0].to_dict() # get first row values
            forcast_summary_dict['Date'] = Date
            # override with mean values for specified columns
            forcast_summary_dict.update({
                'NPP_predict_below': dff_year['NPP_predict_below'].mean(),
                'NPP_predict_avg': dff_year['NPP_predict_avg'].mean(),
                'NPP_predict_above': dff_year['NPP_predict_above'].mean(),
                'Prob': dff_year['Prob'].mean(),
                'NPP_predict_clim': dff_year['NPP_predict_clim'].mean(),
                'Cat': dff_year['Cat'].mode()[0] if not dff_year['Cat'].mode().empty else None
            })
            forcast_summaries.append(forcast_summary_dict)
        
        # Convert the summaries to GeoDataFrames
        df_plot = pd.DataFrame(forcast_summaries)
        current_year = datetime.datetime.now().year
        df_plot = df_plot[df_plot['Year'] == current_year]
    
    latest_date_rows = df_plot[df_plot['Date'] == df_plot['Date'].max()]

    cat_descriptions = {
        'Below': 'drier than normal',
        'Above': 'rainier than normal',
        'EC': 'normal',
    }

    for _, row in latest_date_rows.iterrows():
        predict = row['NPP_predict_clim']
        mean = row['meanANPPgrid']
        cat = row['Cat']

        cat_description = cat_descriptions[cat]

        difference = predict - mean
        percentage = (abs(difference) * 100) / mean

        direction = "higher" if difference > 0 else "lower"
        direction = "higher" if difference > 0 else "lower"
        arrow_direction = "up" if direction == "higher" else "down"

        month = datetime.datetime.now().month
        if 4 <= month <= 5:
            season = 'Spring'
        elif 6 <= month <= 9:
            season = 'Summer'
        else:
            season = 'Last season'

        # THE COMPARISON WIOTH HISTORIC DATA MUST BE UPDATED
        # RIGHT NOW IS NOT REFLECTING WHAT IT IS INTENDED TO DO
        # Calculate the absolute difference between each value in the column and the predicted value
        hist_data = df_hist.copy()

        if season == 'Spring':
            hist_data['abs_diff'] = abs(hist_data['predicted_Spring_ANPP (lbs/ac)'] - predict)
        else:
            hist_data['abs_diff'] = abs(hist_data['predicted_Summer_ANPP (lbs/ac)'] - predict)

        # Find the row with the minimum absolute difference
        most_similar_row = hist_data.loc[hist_data['abs_diff'].idxmin()]

        # Access the year value from the most similar row
        most_similar_year = most_similar_row['year']

        text = (f"For this location, the expected production for this season is about {round(predict,2)} lb/ac. Being this year {cat_description}, the production is {percentage:.2f}% {direction} than the average historical production.")

        first_box = html.Div([
            html.Span(f"The expected production for this {season} is ", style={"color": "black"}),
            html.Br(),
            html.Span(f"{round(predict,2)}", style={"color": "#2e55a3", "font-size": "24px"}),
            html.Span(" lb/ac.", style={"color": "black"})
        ])

        second_box = html.Div([
            html.Span("Weather is "),
            html.Br(),
            html.Span(f"{cat_description.split(' ')[0]}", style={"color": "#2e55a3", "font-size": "24px"}) if cat_description != 'normal' else "",
            html.Span(" than normal") if cat_description != 'normal' else "",
            html.Span(f"{cat_description}", style={"color": "#2e55a3", "font-size": "24px"}) if cat_description == 'normal' else ""
        ])

        third_box = html.Div([
            html.Span(f"The production will be"),
            html.Br(),
            html.Span(f"{round(percentage,2):.2f}% ", style={"color": "#2e55a3", "font-size": "20px"}),
            html.Span(f"{direction}   ", style={"color": "#2e55a3", "font-size": "20px"}),
            html.Span(className=f"fa fa-arrow-{arrow_direction}", style={"color": "#2e55a3","font-size": "20px"}),
            html.Br(),
            html.Span(" than expected")
        ])


        fourth_box = html.Div([
            html.Span(f"These conditions are most similar to those from "),
            html.Span(f"{most_similar_year}", style={"color": "#2e55a3", "font-size": "20px"}),
        ])

    return text, first_box, second_box, third_box, fourth_box



# # Forcast production chart
# @app.callback(
#     Output(component_id='line-plot-2', component_property='figure'),
#     [Input(component_id='choropleth-map', component_property='clickData'),
#      Input(component_id='my-toggle-switch', component_property='on')]
# )
# def update_line_plot2(clickData, on):
#     if clickData is None:
#         return go.Figure().update_layout(
#             title="Please click on the map to display data",
#             xaxis=dict(visible=False),
#             yaxis=dict(visible=False)
#         )
#     else:
#         id_value = clickData['points'][0]['customdata'][0]

        
#         # Load and filter your data here
#         dff = df_forcast.copy()

#         # Filter the data frame by the 'Id' selected from the map
#         df_plot = dff[dff['gridID'] == id_value]

#         # Select current year
#         current_year = datetime.datetime.now().year
#         df_plot = df_plot[df_plot['Year'] == current_year]

#         if on:  # This means the button was clicked
#             # Create the Plotly figure
#             fig = go.Figure()

#             # Add 'NPP_predict_avg' line
#             fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['NPP_predict_avg'], 
#                                     name='ANPP avg', line=dict(color='rgb(128, 128, 0)', dash='dash')))

#             # Add 'NPP_predict_below' line
#             fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['NPP_predict_below'], 
#                                     name='ANPP below', line=dict(color='rgb(237, 189, 69)', dash='dash')))

#             # Add 'NPP_predict_above' line
#             fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['NPP_predict_above'], 
#                                     name='ANPP above', line=dict(color='rgb(0, 128, 0)', dash='dash')))

#             # Add 'NPP_predict_clim' line
#             fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['NPP_predict_clim'], 
#                                     name='actual ANPP', line=dict(color='rgba(0,0,0,0.2)', width=1),
#                                     mode='lines', showlegend=False))

#             # Set y-axis labels
#             fig.update_yaxes(title_text='ANPP')

#             # Update the layout of the plot to have a transparent background
#             fig.update_layout(
#                 plot_bgcolor='rgba(0,0,0,0)',
#                 paper_bgcolor='rgba(0,0,0,0)',
#                 xaxis=dict(
#                     title=None,  # Remove title
#                     tickformat='%b %d'  # Show only month and day on x-axis, in the format "Month Day"
#                 ),
#                 margin=dict(l=10, r=50, t=0, b=0),
#                 legend=dict(x=0.05, y=0.92, bgcolor='rgba(255, 255, 255, 0.5)')  # Set legend to top left corner and semi-transparent
#             )

#             # Show the graph
#             return fig
#         else:
#             # If the button was not clicked, just generate the figure normally
#             # Create the Plotly figure
#             trace0 = go.Scatter(
#                 x=df_plot['Date'],
#                 y=df_plot['NPP_predict_below'],
#                 mode='lines',
#                 name='NPP_predict_below',
#                 line=dict(color='rgb(0, 128, 0)', width=1, dash='dot'),
#                 showlegend=False
#             )
#             trace1 = go.Scatter(
#                 x=df_plot['Date'],
#                 y=df_plot['NPP_predict_above'],
#                 mode='lines',
#                 name='NPP_predict_above',
#                 fill='tonexty',
#                 fillcolor='rgba(0,100,80,0.2)',
#                 line=dict(color='rgb(0, 128, 0)', width=1, dash='dot'),
#                 showlegend=False
#             )
#             trace2 = go.Scatter(
#                 x=df_plot['Date'],
#                 y=df_plot['NPP_predict_avg'],
#                 mode='lines',
#                 name='NPP_predict_avg',
#                 line=dict(color='rgba(0, 128, 0, 0.5)', width=1, dash='dot'),
#                 showlegend=False
#             )
#             trace3 = go.Scatter(
#                 x=df_plot['Date'],
#                 y=df_plot['NPP_predict_clim'],
#                 mode='lines+markers',
#                 name='NPP_predict_clim',
#                 line=dict(color='rgb(237, 189, 69)', width=4),
#                 marker=dict(
#                     size=6,
#                     color='rgb(237, 189, 69)',
#                     line=dict(
#                         color='white',
#                         width=1
#                     )
#                 ),
#                 showlegend=False
#             )

#             data = [trace0, trace1, trace2, trace3]

#             layout = go.Layout(
#                 xaxis=dict(
#                     title=None,
#                     tickformat='%b %d'
#                 ),
#                 yaxis=dict(title=None),
#                 showlegend=False
#             )

#             fig = go.Figure(data=data, layout=layout)

#             fig.update_yaxes(title_text='ANPP')

#             fig.update_layout(
#                 plot_bgcolor='rgba(0,0,0,0)',
#                 paper_bgcolor='rgba(0,0,0,0)',
#                 margin=dict(l=10, r=50, t=0, b=0)
#             )

#             return fig




# Forcast production chart
@app.callback(
    Output(component_id='line-plot-2', component_property='figure'),
    [Input(component_id='choropleth-map', component_property='clickData'),
     Input(component_id='my-toggle-switch', component_property='on'),
     Input(component_id='autocomplete-input', component_property='value')]
)
def update_line_plot2(clickData, on, by_county):
    ctx = dash.callback_context

    # If nothing has triggered the callback yet, do nothing
    if not ctx.triggered:
        return go.Figure()

    # Identify which input triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    
    if triggered_id in ['my-toggle-switch', 'choropleth-map'] and clickData is not None:
        id_value = clickData['points'][0]['customdata'][0]
        dff = df_forcast.copy()
        df_plot = dff[dff['gridID'] == id_value]
        current_year = datetime.datetime.now().year
        df_plot = df_plot[df_plot['Year'] == current_year]

    # NEEDS TO BE UPDATED, IT DOES NOT SWITCHES INITIALLY
    elif triggered_id in ['my-toggle-switch', 'autocomplete-input'] and by_county is not None:
        polygon = sw_counties.loc[sw_counties['NAME'] == by_county]
        columns_to_keep_forcast = ['gridID','Date','NPP_predict_below', 'NPP_predict_avg','NPP_predict_above',
                                'Cat', 'Prob','Year', 'NPP_predict_clim','geometry']
        # spatial join between the gdf_forcast and the polygon
        dff_forcast_polygon = sjoin(gdf_forcast[columns_to_keep_forcast], polygon, how='inner', op='intersects')
        dff_forcast_polygon['Date'] = pd.to_datetime(dff_forcast_polygon['Date'])
        forcast_summaries = []
        for Date in dff_forcast_polygon['Date'].unique():
            dff_year = dff_forcast_polygon[dff_forcast_polygon['Date'] == Date]
            forcast_summary_dict = dff_year.iloc[0].to_dict() # get first row values
            forcast_summary_dict['Date'] = Date
            # override with mean values for specified columns
            forcast_summary_dict.update({
                'NPP_predict_below': dff_year['NPP_predict_below'].mean(),
                'NPP_predict_avg': dff_year['NPP_predict_avg'].mean(),
                'NPP_predict_above': dff_year['NPP_predict_above'].mean(),
                'Prob': dff_year['Prob'].mean(),
                'NPP_predict_clim': dff_year['NPP_predict_clim'].mean(),
                'Cat': dff_year['Cat'].mode()[0] if not dff_year['Cat'].mode().empty else None
            })
            forcast_summaries.append(forcast_summary_dict)

        # Convert the summaries to GeoDataFrames
        df_plot = pd.DataFrame(forcast_summaries)
        current_year = datetime.datetime.now().year
        df_plot = df_plot[df_plot['Year'] == current_year]

    # UPDATE SWITCH SO IT AUTOMATICALLY UPDATES WHEN PRESSING
    if on:  # This means the button was clicked
        # Create the Plotly figure
        fig = go.Figure()

        # Add 'NPP_predict_avg' line
        fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['NPP_predict_avg'], 
                                name='ANPP avg', line=dict(color='rgb(128, 128, 0)', dash='dash')))

        # Add 'NPP_predict_below' line
        fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['NPP_predict_below'], 
                                name='ANPP below', line=dict(color='rgb(237, 189, 69)', dash='dash')))

        # Add 'NPP_predict_above' line
        fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['NPP_predict_above'], 
                                name='ANPP above', line=dict(color='rgb(0, 128, 0)', dash='dash')))

        # Add 'NPP_predict_clim' line
        fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['NPP_predict_clim'], 
                                name='actual ANPP', line=dict(color='rgba(0,0,0,0.2)', width=1),
                                mode='lines', showlegend=False))

        # Set y-axis labels
        fig.update_yaxes(title_text='ANPP')

        # Update the layout of the plot to have a transparent background
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                title=None,  # Remove title
                tickformat='%b %d'  # Show only month and day on x-axis, in the format "Month Day"
            ),
            margin=dict(l=10, r=50, t=0, b=0),
            legend=dict(x=0.05, y=0.92, bgcolor='rgba(255, 255, 255, 0.5)')  # Set legend to top left corner and semi-transparent
        )

        # Show the graph
        return fig
    else:
        # If the button was not clicked, just generate the figure normally
        # Create the Plotly figure
        trace0 = go.Scatter(
            x=df_plot['Date'],
            y=df_plot['NPP_predict_below'],
            mode='lines',
            name='NPP_predict_below',
            line=dict(color='rgb(0, 128, 0)', width=1, dash='dot'),
            showlegend=False
        )
        trace1 = go.Scatter(
            x=df_plot['Date'],
            y=df_plot['NPP_predict_above'],
            mode='lines',
            name='NPP_predict_above',
            fill='tonexty',
            fillcolor='rgba(0,100,80,0.2)',
            line=dict(color='rgb(0, 128, 0)', width=1, dash='dot'),
            showlegend=False
        )
        trace2 = go.Scatter(
            x=df_plot['Date'],
            y=df_plot['NPP_predict_avg'],
            mode='lines',
            name='NPP_predict_avg',
            line=dict(color='rgba(0, 128, 0, 0.5)', width=1, dash='dot'),
            showlegend=False
        )
        trace3 = go.Scatter(
            x=df_plot['Date'],
            y=df_plot['NPP_predict_clim'],
            mode='lines+markers',
            name='NPP_predict_clim',
            line=dict(color='rgb(237, 189, 69)', width=4),
            marker=dict(
                size=6,
                color='rgb(237, 189, 69)',
                line=dict(
                    color='white',
                    width=1
                )
            ),
            showlegend=False
        )

        data = [trace0, trace1, trace2, trace3]

        layout = go.Layout(
            xaxis=dict(
                title=None,
                tickformat='%b %d'
            ),
            yaxis=dict(title=None),
            showlegend=False
        )

        fig = go.Figure(data=data, layout=layout)

        fig.update_yaxes(title_text='ANPP (lb/ac)')

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=50, t=0, b=0)
        )

        return fig




@app.callback(
    Output(component_id='line-plot', component_property='figure'),
    [Input(component_id='choropleth-map', component_property='clickData'),
     Input(component_id='slct_year', component_property='value'),
     Input(component_id='autocomplete-input', component_property='value')]
)
def update_line_plot(clickData, option_slctd, by_county):
    ctx = dash.callback_context

    # If nothing has triggered the callback yet, do nothing
    if not ctx.triggered:
        return go.Figure()

    # Identify which input triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    fig = go.Figure()

    # SLIDER UPDATE STILL HAS TO BE FIXED
    slctd_year = pd.to_datetime(option_slctd, format='%Y')

    # Determine y_column based on current month
    current_month = datetime.datetime.now().month

    if current_month in [4, 5]:  # April or May
        y_column = 'predicted_Spring_ANPP (lbs/ac)'
    else:
        y_column = 'predicted_Summer_ANPP (lbs/ac)'

    if triggered_id in ['slct_year', 'choropleth-map'] and clickData is not None:
        id_value = clickData['points'][0]['customdata'][0]
        dff = gdf.copy()
        df_plot = dff[dff['gridID'] == id_value]
        df_plot['year'] = pd.to_datetime(df_plot['year'], format='%Y')
        y_range = [0, max(dff[y_column])]

    elif triggered_id in ['slct_year', 'autocomplete-input'] and by_county is not None:
        # similar logic for autocomplete-input trigger
        # here df_plot should be set appropriately
        polygon = sw_counties.loc[sw_counties['NAME'] == by_county]
        gdf_hist = gdf
        columns_to_keep_hist = ['gridID', 'predicted_Spring_ANPP (lbs/ac)', 'predicted_Summer_ANPP (lbs/ac)','year','geometry']
        dff_hist_polygon = sjoin(gdf_hist[columns_to_keep_hist], polygon, how='inner', op='intersects')
        hist_summaries = []
        for year in dff_hist_polygon['year'].unique():
            dff_year = dff_hist_polygon[dff_hist_polygon['year'] == year]
            hist_summary_dict = dff_year.iloc[0].to_dict() # get first row values
            hist_summary_dict['year'] = pd.to_datetime(str(year), format='%Y')
            hist_summary_dict.update({
                'predicted_Spring_ANPP (lbs/ac)': dff_year['predicted_Spring_ANPP (lbs/ac)'].mean(),
                'predicted_Summer_ANPP (lbs/ac)': dff_year['predicted_Summer_ANPP (lbs/ac)'].mean()
            })
            hist_summaries.append(hist_summary_dict)
        df_plot = pd.DataFrame(hist_summaries)
        df_plot['year'] = pd.to_datetime(df_plot['year'], format='%Y')
        y_range = [0, max(gdf_hist[y_column])]


    # now plot is called only once, after preparing data based on input trigger
    fig.add_trace(go.Scatter(
        x=df_plot['year'],
        y=df_plot[y_column],
        fill='tozeroy',
        fillcolor='rgba(0, 128, 0, 0.2)', #green color with 0.4 opacity
        mode='lines+markers', #adds points to the line
        line=dict(color='green'),
        marker=dict(size=4), #changes size of the
        name='ANPP_mean_Spring (lbs/ac)'
    ))

    # Update axes
    fig.update_xaxes(title_text='', tickangle=45, showticklabels=False)
    fig.update_yaxes(title_text=y_column, 
                    range=y_range)

    # Add vertical dashed line
    fig.add_shape(
        type="line",
        x0=slctd_year, y0=0,
        x1=slctd_year, y1=1,
        yref="paper",
        line=dict(
            color="black",
            width=1,
            dash="dash",
        )
    )

    # Update the layout of the plot to have a transparent background
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=50, t=0, b=0)
    )

    return fig




# @app.callback(
#     Output(component_id='line-plot', component_property='figure'),
#     [Input(component_id='choropleth-map', component_property='clickData')]
# )
# def update_line_plot(clickData):
#     if clickData is None:
#         return go.Figure().update_layout(
#             title="Please click on the map to display data",
#             xaxis=dict(visible=False),
#             yaxis=dict(visible=False)
#         )
#     else:
#         id_value = clickData['points'][0]['customdata'][0]

#         dff = gdf.copy()

#         # Filter the data frame by the 'Id' selected from the map
#         df_plot = dff[dff['Id'] == id_value]

#         # Convert the 'year' column to a datetime format
#         df_plot['year'] = pd.to_datetime(df_plot['year'], format='%Y')

#         # Create the Plotly figure
#         fig = px.line(df_plot, x='year', y='predicted_', title='ANPP_mean_Spring over Time')
#         fig.update_xaxes(title_text='Year')
#         fig.update_yaxes(title_text='ANPP_mean_Spring (lbs/ac)')
#         return fig


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=False)
