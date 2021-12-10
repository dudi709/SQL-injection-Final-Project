import base64
import io
import plotly.graph_objs as go
import cufflinks as cf
import os
import datetime as dt

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
from dash import dash_table
# from datetime import datetime, date
import pandas as pd
from collections import Counter

from predict_sql_queries import build_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

import dash_bootstrap_components as dbc

model, tokenizer1 = build_model()

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

"""
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
"""

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "SQL Query Analysis"

colors = {
    "graphBackground": "#F5F5F5",
    "background": "#ffffff",
    "text": "#000000"
}

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children=html.Img(src="https://img.icons8.com/color/96/000000/sql.png"),
                       className="header-emoji"),
                html.H1(
                    children="SQL Query Analysis", className="header-title"
                ),
                html.P(
                    children="Analyze sql queries and classify them"
                             " according to queries that may contain"
                             " malicious content (sql injection) and valid content.",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    # Allow multiple files to be uploaded
                    multiple=True,
                    className='upload-file'
                ),
            ]
        ),
        html.Div(
            children=[
                html.Div(id='Mycards')
            ]
        ),
        html.Div(
            children=[
                dcc.DatePickerRange(
                    id="date-range",
                    start_date=dt.datetime(2000, 1, 1),
                    end_date=dt.datetime.now(),
                    min_date_allowed=dt.datetime(1955, 1, 1),
                    max_date_allowed=dt.datetime.now(),
                    display_format='DD/MM/YYYY'
                ),
            ]
        ),
        html.Div(
            children=[
                dcc.Graph(id='Mygraph')
            ]
        ),
        html.Div(
            children=[
                html.Div(id='output-data-upload')
            ]
        ),
    ]
)


def parse_data(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV or TXT file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            df.sort_values("Date", inplace=True)
            # Add 'Type' column that classify each query to plain query and sqli query
            query_type = []
            for query in df.iloc[:, 0]:
                temp_query_lst = []
                temp_query_lst.append(query.lower())
                token = tokenizer1.texts_to_sequences(temp_query_lst)
                pad = pad_sequences(token, maxlen=150, padding="post")
                decision = model.predict(pad)[0][0]

                if decision < 0.6:
                    query_type.append("plain")
                    # print(f"{entry} - is not identified as a malicious query")
                else:
                    query_type.append("sqli")
                    # print(f"{entry} - is identified as a malicious query !!!")
            df['Type'] = query_type

        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif 'txt' or 'tsv' in filename:
            # Assume that the user upl, delimiter = r'\s+'oaded an excel file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')), delimiter=r'\s+')
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return df


@app.callback(Output('Mycards', 'children'),
              [
                  Input('upload-data', 'contents'),
                  Input('upload-data', 'filename')
              ])
def update_cards(contents, filename):
    cards = html.Div()

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

        total_queries = len(df['Queries'])
        query_type = df['Type']
        total_sqli_queries = 0
        total_plain_queries = 0

        for type in query_type:
            if type == "sqli":
                total_sqli_queries += 1
            else:
                total_plain_queries += 1

        total_queries_card = [
            dbc.CardHeader("Total Queries"),
            dbc.CardBody(
                [
                    html.H5(f"{total_queries}", className="card-title"),
                    dbc.Progress(value=int((total_queries / total_queries) * 100),
                                 label=f"{int(total_queries / total_queries) * 100}%",
                                 color="info", className="mb-3"),
                ]
            ),
        ]

        total_plain_queries_card = [
            dbc.CardHeader("Total Plain Queries"),
            dbc.CardBody(
                [
                    html.H5(f"{total_plain_queries}", className="card-title"),
                    dbc.Progress(value=int((total_plain_queries / total_queries) * 100),
                                 label=f"{int((total_plain_queries / total_queries) * 100)}%",
                                 color="success", className="mb-3"),
                ]
            ),
        ]

        total_sqli_queries_card = [
            dbc.CardHeader("Total SQLi Queries"),
            dbc.CardBody(
                [
                    html.H5(f"{total_sqli_queries}", className="card-title"),
                    dbc.Progress(value=int((total_sqli_queries / total_queries) * 100),
                                 label=f"{int((total_sqli_queries / total_queries) * 100)}%",
                                 color="danger", className="mb-3"),
                ]
            ),
        ]

        cards_row = dbc.Row(
            [
                dbc.Col(dbc.Card(total_queries_card, color="info", outline=True)),
                dbc.Col(dbc.Card(total_plain_queries_card, color="success", outline=True)),
                dbc.Col(dbc.Card(total_sqli_queries_card, color="danger", outline=True)),
            ],
            className="mb-4"
        )

        cards = html.Div([cards_row])

    return cards


@app.callback(Output('Mygraph', 'figure'),
              [
                  Input('upload-data', 'contents'),
                  Input('upload-data', 'filename'),
                  Input('date-range', 'start_date'),
                  Input('date-range', 'end_date'),
              ])
def update_graph(contents, filename, start_date, end_date):
    fig = {}
    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
        df.sort_values("Date", inplace=True)

        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        filtered_df = df[df.Date.between(
            dt.datetime.strftime(start_date, "%Y-%m-%d"),
            dt.datetime.strftime(end_date, "%Y-%m-%d")
        )]
        filtered_df.sort_values("Date", inplace=True)

        new_filtered_df = filtered_df.groupby('Date')['Type'].apply(list).reset_index(name='Type')
        x = list(Counter(new_filtered_df.Date.dt.strftime('%Y-%m-%d')).keys())
        y1 = []
        y2 = []
        for lst_type in new_filtered_df['Type']:
            y1.append(lst_type.count('plain'))
            y2.append(lst_type.count('sqli'))

        fig = {'data': [
            {'x': x, 'y': y1, 'type': 'bar', 'name': 'plain', 'marker': dict(color='198754')},
            {'x': x, 'y': y2, 'type': 'bar', 'name': 'sqli', 'marker': dict(color='DC3545')},
        ],
            'layout': {
                'title': 'Plain vs. Malicious Queries on Selected Dates',
                "xaxis": {"fixedrange": True},
                "yaxis": {"fixedrange": True},
                'plot_bgcolor': 'graphBackground',
                'paper_bgcolor': 'graphBackground'
            }
        }

    return fig


@app.callback(Output('output-data-upload', 'children'),
              [
                  Input('upload-data', 'contents'),
                  Input('upload-data', 'filename')
              ])
def update_table(contents, filename):
    table = html.Div()

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)
        table = html.Div([
            html.H5(filename),
            dash_table.DataTable(
                data=df.to_dict('rows'),
                columns=[{'name': i, 'id': i, "deletable": True} for i in df.columns],
                export_format='csv',
                editable=True,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                column_selectable="single",
                row_deletable=True,
                selected_columns=[],
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=10,
                style_header={
                    'backgroundColor': 'rgb(30, 30, 30)',
                    'color': 'white',
                    'textAlign': 'left'
                },
                style_data={
                    'backgroundColor': 'rgb(50, 50, 50)',
                    'color': 'white',
                    'textAlign': 'left'
                },
            ),
            html.Hr(),
            html.Div('Raw Content'),
            html.Pre(contents[0:200] + '...', style={
                'whiteSpace': 'pre-wrap',
                'wordBreak': 'break-all'
            })
        ])

    return table


if __name__ == '__main__':
    app.run_server(debug=True)
