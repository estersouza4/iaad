from datetime import datetime

import mysql.connector
from dash import Dash, Input, Output, State, dcc, html

from componentes import CORES, card, grafico_robos, grafico_vazio, tabela_robos
from conectar import buscar_robos


app = Dash(__name__)
app.title = "Robôs por Equipe"


app.layout = html.Div(
    [
        dcc.Store(id="dados-robos"),
        html.Header(
            [
                html.Div(
                    [
                        html.Div("🤖", className="logo"),
                        html.Div(
                            [
                                html.H1("Robôs por equipe"),
                                html.P("Quantidade de robôs cadastrados no torneio"),
                            ]
                        ),
                    ],
                    className="brand",
                ),
                html.Div(
                    [
                        dcc.Input(
                            id="senha",
                            type="password",
                            placeholder="Senha do MySQL",
                            className="password-input",
                        ),
                        html.Button(
                            "Atualizar dados",
                            id="botao-atualizar",
                            className="update-button",
                        ),
                    ],
                    className="connection-box",
                ),
            ],
            className="topbar",
        ),
        html.Main(
            [
                html.Div(id="mensagem", className="message"),
                html.Div(id="cards", className="cards"),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H2("Quantidade de robôs por equipe"),
                                html.P(
                                    "Compare rapidamente a estrutura de cada equipe."
                                ),
                                dcc.Graph(
                                    id="grafico-robos",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="panel chart-panel",
                        ),
                        html.Div(
                            [
                                html.H2("Detalhamento"),
                                html.P("Resumo dos robôs cadastrados."),
                                tabela_robos(),
                            ],
                            className="panel table-panel",
                        ),
                    ],
                    className="content-grid",
                ),
                html.Footer(id="ultima-atualizacao"),
            ],
            className="main",
        ),
    ],
    className="page",
)


@app.callback(
    Output("dados-robos", "data"),
    Output("mensagem", "children"),
    Input("botao-atualizar", "n_clicks"),
    State("senha", "value"),
    prevent_initial_call=True,
)
def atualizar_dados(_, senha):
    if not senha:
        return None, "Digite a senha do MySQL para carregar os dados."
    try:
        return buscar_robos(senha), ""
    except mysql.connector.Error as erro:
        return None, f"Não foi possível conectar ao MySQL: {erro}"


@app.callback(
    Output("cards", "children"),
    Output("grafico-robos", "figure"),
    Output("tabela-robos", "data"),
    Output("ultima-atualizacao", "children"),
    Input("dados-robos", "data"),
)
def atualizar_tela(robos):
    if not robos:
        return [], grafico_vazio(), [], ""

    total = sum(item["quantidade_robos"] for item in robos)
    maior_equipe = robos[0]
    cards = [
        card("Equipes", str(len(robos)), "equipes cadastradas"),
        card("Robôs cadastrados", str(total), "robôs no torneio"),
        card("Média por equipe", f"{total / len(robos):.1f}", "robôs por equipe"),
        card(
            "Maior equipe",
            maior_equipe["equipe"],
            f"{maior_equipe['quantidade_robos']} robô(s)",
        ),
    ]
    atualizado = f"Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    return cards, grafico_robos(robos), robos, atualizado


if __name__ == "__main__":
    app.run(debug=True)
