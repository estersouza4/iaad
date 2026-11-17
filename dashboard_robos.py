
from datetime import datetime

import mysql.connector
from dash import Dash, Input, Output, dcc, html

from componentes import (
    card,
    grafico_robos,
    grafico_vazio,
    tabela_robos,
)

from crud_robos_resultados import consultar

from gerenciamento_ui import (
    criar_gerenciamento,
    registrar_callbacks_gerenciamento,
    tratar_erro,
)


app = Dash(__name__)
app.title = "Robôs | Torneio de Robótica"


def buscar_resumo_robos():
    """
    Consulta os robôs por equipe no MySQL.
    Preserva as informações usadas no gráfico.
    """
    return consultar(
        """
        SELECT
            e.nome_equipe AS equipe,
            COUNT(r.id_robo) AS quantidade_robos
        FROM equipe e
        LEFT JOIN robo r
            ON r.id_equipe = e.id_equipe
        GROUP BY
            e.id_equipe,
            e.nome_equipe
        ORDER BY
            quantidade_robos DESC,
            e.nome_equipe
        """
    )


app.layout = html.Div(
    [
        html.Header(
            [
                html.Div(
                    [
                        html.Div(
                            "🤖",
                            className="logo",
                        ),
                        html.Div(
                            [
                                html.H1("Robôs por equipe"),
                                html.P(
                                    "Quantidade de robôs "
                                    "cadastrados no torneio"
                                ),
                            ]
                        ),
                    ],
                    className="brand",
                ),
                html.Div(
                    "MySQL • Gerenciamento",
                    className="gm-header-tag",
                ),
            ],
            className="topbar",
        ),

        html.Main(
            [
                html.Div(
                    id="mensagem",
                    className="message",
                ),

                html.Div(
                    id="cards",
                    className="cards",
                ),

                # Gráfico e tabela originais
                html.Div(
                    [
                        html.Div(
                            [
                                html.H2(
                                    "Quantidade de robôs por equipe"
                                ),
                                html.P(
                                    "Compare a quantidade "
                                    "de robôs de cada equipe."
                                ),
                                dcc.Graph(
                                    id="grafico-robos",
                                    config={
                                        "displayModeBar": False
                                    },
                                ),
                            ],
                            className="panel chart-panel",
                        ),

                        html.Div(
                            [
                                html.H2("Detalhamento"),
                                html.P(
                                    "Resumo dos robôs cadastrados."
                                ),
                                tabela_robos(),
                            ],
                            className="panel table-panel",
                        ),
                    ],
                    className="content-grid",
                ),

                # CRUD de robôs
                criar_gerenciamento("rb"),

                html.Footer(
                    id="ultima-atualizacao"
                ),
            ],
            className="main",
        ),
    ],
    className="page gm-page",
)


@app.callback(
    Output("cards", "children"),
    Output("grafico-robos", "figure"),
    Output("tabela-robos", "data"),
    Output("ultima-atualizacao", "children"),
    Output("mensagem", "children"),
    Input("rb-revisao", "data"),
)
def atualizar_visualizacoes(_revisao):
    try:
        robos = buscar_resumo_robos()

        if not robos:
            return (
                [],
                grafico_vazio(),
                [],
                "",
                "Nenhuma equipe encontrada.",
            )

        total_robos = sum(
            item["quantidade_robos"]
            for item in robos
        )

        total_equipes = len(robos)
        maior_equipe = robos[0]

        indicadores = [
            card(
                "Equipes",
                str(total_equipes),
                "equipes cadastradas",
            ),
            card(
                "Robôs cadastrados",
                str(total_robos),
                "robôs no torneio",
            ),
            card(
                "Média por equipe",
                f"{total_robos / total_equipes:.1f}",
                "robôs por equipe",
            ),
            card(
                "Maior equipe",
                maior_equipe["equipe"],
                (
                    f"{maior_equipe['quantidade_robos']} "
                    "robô(s)"
                ),
            ),
        ]

        atualizado = (
            "Última atualização: "
            + datetime.now().strftime(
                "%d/%m/%Y às %H:%M"
            )
        )

        return (
            indicadores,
            grafico_robos(robos),
            robos,
            atualizado,
            "",
        )

    except (mysql.connector.Error, ValueError) as erro:
        return (
            [],
            grafico_vazio(),
            [],
            "",
            tratar_erro(erro),
        )


registrar_callbacks_gerenciamento(app, "rb")


if __name__ == "__main__":
    app.run(
        debug=False,
        port=8051,
        use_reloader=False,
    )
