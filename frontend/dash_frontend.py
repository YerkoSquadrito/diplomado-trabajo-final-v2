import dash
from dash import dcc, html, Input, Output, State, ClientsideFunction
import dash_bootstrap_components as dbc
import requests

# Farma colors
GRUPO_2_PURPLE = "#A100FF"
GRUPO_2_BLACK = "#000000"

# Custom CSS for Farma styling and chat bubbles
custom_styles = {
    'body': {
        'backgroundColor': '#F0F0F0',
        'color': GRUPO_2_BLACK
    },
    'h1': {
        'color': GRUPO_2_PURPLE,
        'fontWeight': 'bold'
    },
    '.card': {
        'border': f'2px solid {GRUPO_2_PURPLE}',
        'borderRadius': '15px'
    },
    '.card-body': {
        'borderRadius': '15px',
        'backgroundColor': '#FFFFFF'
    },
    '#chat-display': {
        'backgroundColor': '#F8F8F8',
        'borderRadius': '10px',
        'padding': '10px',
        'height': '70vh',
        'overflowY': 'auto'
    },
    '.message-container': {
        'display': 'flex',
        'flexDirection': 'column',
        'marginBottom': '15px'
    },
    '.user-message-container': {
        'text-align': 'right',
        'background-color': 'blueviolet',
        'width': 'fit-content',
        'min-width': '50%',
        'border-radius': '15px',
        'padding': '5px',
        'padding-right': '10px',
        'display': 'flex',
        'padding-left': '10px'
    },
    '.bot-message-container': {
        'text-align':'left'
    },
    '.message-bubble': {
        'padding': '10px 15px',
        'borderRadius': '20px',
        'maxWidth': '70%',
        'wordWrap': 'break-word'
    },
    '.user-message': {
        'backgroundColor': GRUPO_2_PURPLE,
        'color': 'white'
    },
    '.bot-message': {
        'backgroundColor': '#E0E0E0',
        'color': GRUPO_2_BLACK
    },
    '.message-sender': {
        'fontWeight': 'bold',
        'marginBottom': '5px',
        'fontSize': '0.9em'
    }
}
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

default_message = """¡Hola! Soy tu asistente virtual de farmacias, desarrollado por el Grupo 2 del Diplomado de IA Generativa para Organizaciones de la FEN. 
Mis capacidades consisten en ayudarte con consultas sobre medicamentos específicos o sobre las farmacias de turno en Chile."""

app.layout = dbc.Container([
    dcc.Store(id='chat-history', data=[('ai', default_message)]),
    dcc.Store(id='custom-styles', data=custom_styles),
    dbc.Row([
        dbc.Col([
            html.H1("Grupo 2 - Chatbot Farmacias", className="text-center mb-4")
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(children=[
                        html.Div([
                                html.Div([
                                    html.Strong("Farma Bot:", className="message-sender"),
                                    html.Div([default_message], className="message-bubble.bot-message")
                                ], className="message-container.bot-message-container"
                                , style = {'text-align' : ['left'][0],
                                    'background-color': ['floralwhite'][0] ,
                                        'width': 'fit-content',
                                        'min-width': '5%',
                                        'max-width': '60%',
                                        'border-radius': '15px',
                                        'padding': '5px',
                                        'padding-right': '10px',
                                        'padding-left': '10px',
                                        'border': '1px solid blueviolet',
                                        'color' : ['black'][0]
                                    }
                                    ),
                                
                            ], style = {'justify-content' : ['end' if ((str("Farma Bot:") != 'Farma Bot:')) else 'start'][0],
                                        'display': 'flex'
                                    }
                            )
                    ],id="chat-display"),
                    html.Hr(style={"borderColor": GRUPO_2_PURPLE}),
                    dbc.Input(id="user-input", placeholder="Type your message here...", type="text"),
                    dbc.Button("Send", id="send-button", color="primary", 
                               style={"backgroundColor": GRUPO_2_PURPLE, "borderColor": GRUPO_2_PURPLE},
                               className="mt-2")
                ])
            ])
        ], width='65%' , className="mx-auto")
    ])
])

app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='apply_custom_styles'
    ),
    Output('custom-styles', 'data'),
    Input('custom-styles', 'data')
)

def create_message_bubble(sender, message):
    return html.Div([
        html.Div([
        html.Strong(sender, className="message-sender"),
        html.Div([message], className=f"message-bubble {'user-message' if ((sender == 'You:') or (sender == 'Tú:')) else 'bot-message'}")
    ], className=f"message-container {'user-message-container' if ((sender == 'You:') or (sender == 'Tú:')) else 'bot-message-container'}"
    , style = {'text-align' : ['right' if ((str(sender) != 'Farma Bot:')) else 'left'][0],
               'background-color': ['blueviolet' if ((str(sender) != 'Farma Bot:')) else 'floralwhite'][0] ,
                'width': 'fit-content',
                'min-width': '5%',
                'max-width': '60%',
                'border-radius': '15px',
                'padding': '5px',
                'padding-right': '10px',
                'padding-left': '10px',
                'border': '1px solid blueviolet',
                'color' : ['white' if ((str(sender) != 'Farma Bot:')) else 'black'][0]
               }
            ),
        
    ], style = {'justify-content' : ['end' if ((str(sender) != 'Farma Bot:')) else 'start'][0],
                'display': 'flex'
            }
    )
import logging
@app.callback(
    Output("chat-display", "children", allow_duplicate=True),
    Output("user-input", "value"),
    Output("chat-history", "data", allow_duplicate=True),
    Input("send-button", "n_clicks"),
    Input("user-input", "n_submit"),
    State("user-input", "value"),
    State("chat-display", "children"),
    State("chat-history", "data"),
    prevent_initial_call=True
)
def send_message(n_clicks, n_submit, user_input, chat_history_display, chat_history):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    input_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if user_input and (input_id == "send-button" or input_id == "user-input"):
        user_message = create_message_bubble("Tú:", user_input)
        if chat_history_display is None:
            chat_history_display = []
        chat_history_display.append(user_message)
        chat_history = chat_history + [('human', user_input)]
        
        # Add "Writing..." message
        writing_message = create_message_bubble("Farma Bot:", "Escribiendo...")
        chat_history_display.append(writing_message)
        
        return chat_history_display, "", chat_history
    return dash.no_update

@app.callback(
    Output("chat-display", "children"),
    Output("chat-history", "data"),
    Input("chat-history", "data"),
    prevent_initial_call=True
)
def update_bot_response(chat_history):
    if chat_history and chat_history[-1][0] == 'human':
        # Send request to FastAPI backend
        input = {"chat_history": chat_history}
        try:
            ai_response = requests.post("http://backend:8001/chat", json=input).json()['response']
        except:
            ai_response = requests.post("http://localhost:8001/chat", json=input).json()['response']
        logging.error(ai_response)
        
        # Reconstruct chat display from chat history
        chat_history_display = []
        for sender, message in chat_history:
            if sender == 'human':
                chat_history_display.append(create_message_bubble("Tú:", message))
            else:
                chat_history_display.append(create_message_bubble("Farma Bot:", dcc.Markdown(message)))
        
        # Add new bot response
        chat_history_display.append(create_message_bubble("Farma Bot:", dcc.Markdown(ai_response)))
        
        # Update chat history
        chat_history = chat_history + [('ai', ai_response)]
        
        return chat_history_display, chat_history
    return dash.no_update



# Create a file named assets/custom_styles.js in your project directory
with open('assets/custom_styles.js', 'w') as f:
    f.write("""
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        apply_custom_styles: function(styles) {
            Object.entries(styles).forEach(([selector, properties]) => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(el => {
                    Object.entries(properties).forEach(([property, value]) => {
                        el.style[property] = value;
                    });
                });
            });
            return styles;
        }
    }
});
""")

if __name__ == "__main__":
    app.run_server(debug=0, host='0.0.0.0', port=8502)