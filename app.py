import base64
import io
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import datetime as dt
import urllib
import dash
import pandas as pd
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
from dash import dash_table
from collections import Counter
from tensorflow.keras.preprocessing.sequence import pad_sequences
from predict_sql_queries import build_model

model, tokenizer1 = build_model()

# Create href for csv example file
df_example_file = pd.read_csv('sql_queries_test.csv')
csv_string = df_example_file.to_csv(index=False, encoding='utf-8')
csv_string = "data:text/csv;charset=utf-8,%EF%BB%BF" + urllib.parse.quote(csv_string)

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
                html.P(
                    children='* Acceptable only csv files with: Queries, Date headers.',
                    style={
                        'text-align': 'center',
                        'color': 'red'
                    }
                ),
                dbc.Row(
                    dbc.Col(
                        html.A(
                            id="download_csv",
                            children="Download example file",
                            href=csv_string,
                            download='example.csv',
                            target="_blank",
                            className="btn btn-outline-secondary btn-sm d-flex justify-content-center",
                        ),
                        width={"size": 2},

                    ),

                    justify="center",
                    align="center"
                ),
            ]
        ),
        html.Div(
            children=[
                html.Div(id='Mycards',
                         style={
                             'marginTop': '6px'
                         })
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
                    display_format='DD/MM/YYYY',
                    style={
                        'textAlign': 'center'
                    }
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
        html.Div(
            children=[
                html.Footer(id='Footer',
                            children='Dudi & Avihay - SCE © 2022',
                            style={
                                'position': 'fixed',
                                'left': 0,
                                'bottom': 0,
                                'width': '100%',
                                'backgroundColor': 'rgb(34, 34, 34)',
                                'color': 'white',
                                'textAlign': 'center'
                            })
            ]
        ),
    ]
)


def update_cards(df):
    """Updates the cards that represents the percent of total, plain and malicious queries

    Parameters
    ----------
    df : DataFrame
        a dataframe object that represents the csv file that user was uploads

    Returns
    -------
    dash.html.Div
        a object that represented the content of the cards
    """
    total_queries = len(df['Queries'])
    query_type = df['Type']
    total_sqli_queries = 0
    total_plain_queries = 0

    for q_type in query_type:
        if q_type == "sqli":
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


def update_graph(df, start_date, end_date):
    """Updates the graph that represents the total plain and malicious queries at selected dates

    Parameters
    ----------
    df : DataFrame
        a dataframe object that represents the csv file that user was uploads
    start_date : str
        a string representing the start date of the data to be displayed in the graph
    end_date : str
        a string representing the end date of the data to be displayed in the graph

    Returns
    -------
    dash.html.Div
        a dict that represented the content of the graph
    """
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
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
            'plot_bgcolor': 'graphBackground',
            'paper_bgcolor': 'graphBackground'
        }
    }
    return fig


def update_table(df, filename):
    """Updates the table that classifies each query

    Parameters
    ----------
    df : DataFrame
        a dataframe object that represents the csv file that user was uploads
    filename : str
        a string representing the name of file that was upload

    Returns
    -------
    dash.html.Div
        a object that represented the content of the table
    """
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    df["Date"] = df.Date.dt.strftime('%Y-%m-%d')
    df.sort_values("Date", inplace=True)
    table = html.Div([
        html.H5(children=f'{filename}',
                style={
                    'textAlign': 'center'
                }),
        html.P(
            children='A table that shows a classification of all queries, you can edit it and export it '
                     'as a CSV file.',
            style={
                'textAlign': 'center'
            }),
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
        html.Hr()
    ])
    return table


def assert_modal(modal_title, modal_body):
    modal = html.Div(
        [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(modal_title)),
                    dbc.ModalBody(modal_body),
                ],
                id="modal",
                is_open=True,
                style={
                    'color': 'red',
                    'textAlign': 'center'
                }
            ),
        ]
    )
    return modal


def check_integrity_csv(df):
    col_0 = df.columns[0]
    col_1 = df.columns[1]
    if col_0 == 'Queries' and col_1 == 'Date':
        try:
            pd.to_datetime(df.Date, format='%Y-%m-%d', errors='raise')
            return True
        except ValueError:
            return False
    return False


def classification_query(df):
    df.sort_values("Date", inplace=True)
    # Add 'Type' column that classify each query to plain query and sqli query
    query_type = []
    for query in df.iloc[:, 0]:
        temp_query_lst = [query.lower()]
        token = tokenizer1.texts_to_sequences(temp_query_lst)
        pad = pad_sequences(token, maxlen=150, padding="post")
        decision = model.predict(pad)[0][0]

        if decision < 0.6:
            query_type.append("plain")
        else:
            query_type.append("sqli")
    df['Type'] = query_type


def parse_data(contents, filename):
    df = None
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.endswith(".csv"):
            # Assume that the user uploaded a CSV or TXT file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            if check_integrity_csv(df):
                classification_query(df)
        else:
            return dash.no_update, False

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return df


@app.callback([Output('Mycards', 'children'), Output('Mygraph', 'figure'), Output('output-data-upload', 'children')],
              [
                  Input('upload-data', 'contents'),
                  Input('upload-data', 'filename'),
                  Input('date-range', 'start_date'),
                  Input('date-range', 'end_date'),
              ])
def update_components(contents, filename, start_date, end_date):
    cards = html.Div()
    table = html.Div()
    fig = {}

    if contents:
        contents = contents[0]
        filename = filename[0]
        if filename.endswith(".csv"):
            df = parse_data(contents, filename)
            if check_integrity_csv(df):
                cards = update_cards(df)
                fig = update_graph(df, start_date, end_date)
                table = update_table(df, filename)
            else:
                modal_title = "Error"
                modal_body = "Please upload a csv files with: Queries, Date headers. See Example file! (Date format " \
                             "should be: Y-m-d) "
                cards = assert_modal(modal_title, modal_body)
        else:
            modal_title = "Error"
            modal_body = "Please upload only csv files"
            cards = assert_modal(modal_title, modal_body)

    return cards, fig, table


if __name__ == '__main__':
    app.run_server(debug=True)
