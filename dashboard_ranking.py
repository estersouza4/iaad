from datetime import datetime

import mysql.connector
from dash import Dash, Input, Output, State, dcc, html

from componentes import (
    CORES,
    card,
    grafico_ranking,
    grafico_vazio,
    tabela_ranking,
)
from conectar import buscar_ranking


app = Dash(__name__)
app.title = "Torneio de Robótica"


app.layout = html.Div(
    [
        dcc.Store(id="dados-ranking"),
        html.Header(
            [
                html.Div(
                    [
                        html.Div("🤖", className="logo"),
                        html.Div(
                            [
                                html.H1("Torneio de Robótica"),
                                html.P("Painel de desempenho das equipes"),
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
                            "Atualizar ranking",
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
                                html.H2("Ranking por pontuação"),
                                html.P(
                                    "As equipes com maior desempenho aparecem no topo."
                                ),
                                dcc.Graph(
                                    id="grafico",
                                    config={"displayModeBar": False},
                                ),
                            ],
                            className="panel chart-panel",
                        ),
                        html.Div(
                            [
                                html.H2("Classificação"),
                                html.P("Resumo das participações no torneio."),
                                tabela_ranking(),
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
    Output("dados-ranking", "data"),
    Output("mensagem", "children"),
    Input("botao-atualizar", "n_clicks"),
    State("senha", "value"),
    prevent_initial_call=True,
)
def atualizar_dados(_, senha):
    if not senha:
        return None, "Digite a senha do MySQL para carregar os dados."
    try:
        return buscar_ranking(senha), ""
    except mysql.connector.Error as erro:
        return None, f"Não foi possível conectar ao MySQL: {erro}"


@app.callback(
    Output("cards", "children"),
    Output("grafico", "figure"),
    Output("tabela", "data"),
    Output("ultima-atualizacao", "children"),
    Input("dados-ranking", "data"),
)
def atualizar_tela(ranking):
    if not ranking:
        return [], grafico_vazio(), [], ""

    total = sum(float(item["pontuacao_total"]) for item in ranking)
    participacoes = sum(item["participacoes"] for item in ranking)
    lider = ranking[0]
    cards = [
        card("Equipes", str(len(ranking)), "equipes cadastradas"),
        card("Pontuação total", f"{total:.2f}", "pontos no torneio"),
        card("Participações", str(participacoes), "resultados registrados"),
        card("Equipe líder", lider["equipe"], f"{float(lider['pontuacao_total']):.2f} pontos"),
    ]
    tabela = [
        {
            "posicao": f"{posicao}º",
            "equipe": item["equipe"],
            "pontuacao": f"{float(item['pontuacao_total']):.2f}",
            "participacoes": item["participacoes"],
        }
        for posicao, item in enumerate(ranking, start=1)
    ]
    atualizado = f"Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    return cards, grafico_ranking(ranking), tabela, atualizado


if __name__ == "__main__":
    app.run(debug=True)
