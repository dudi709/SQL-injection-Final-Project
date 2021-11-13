import base64
import datetime
import io
import plotly.graph_objs as go
import cufflinks as cf

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import pandas as pd

from predict_sql_queries import build_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

model, tokenizer1 = build_model()

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
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
                html.P(children=html.Img(src="https://img.icons8.com/color/96/000000/sql.png"), className="header-emoji"),
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


@app.callback(Output('Mygraph', 'figure'),
              [
                  Input('upload-data', 'contents'),
                  Input('upload-data', 'filename')
              ])
def update_graph(contents, filename):
    fig = {
        'layout': go.Layout(
            plot_bgcolor=colors["graphBackground"],
            paper_bgcolor=colors["graphBackground"])
    }

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)
        df = df.set_index(df.columns[0])
        fig['data'] = df.iplot(asFigure=True, kind='scatter', mode='lines+markers', size=1)

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
                columns=[{'name': i, 'id': i} for i in df.columns],
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
