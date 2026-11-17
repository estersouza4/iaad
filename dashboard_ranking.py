
from datetime import datetime

import mysql.connector

from dash import Dash, Input, Output, html, dcc

from componentes import (
    CORES,
    card,
    grafico_ranking,
    grafico_vazio,
    tabela_ranking,
)

from crud_robos_resultados import consultar

from gerenciamento_ui import (
    criar_gerenciamento,
    registrar_callbacks_gerenciamento,
    tratar_erro,
)


# ==========================================
# CONFIGURAÇÃO DO DASH
# ==========================================

app = Dash(__name__)
app.title = "Ranking | Torneio de Robótica"


# ==========================================
# CONSULTA DO RANKING NO MYSQL
# ==========================================

def buscar_ranking_atualizado():
    """
    Busca o ranking das equipes no MySQL.

    Utiliza a conexão configurada em
    crud_equipes.py, através da função
    consultar().

    O ranking é calculado com base nos
    resultados cadastrados no banco.
    """

    return consultar(
        """
        SELECT
            e.nome_equipe AS equipe,
            COUNT(r.id_robo) AS participacoes,
            COALESCE(
                SUM(r.pontuacao), 0
            ) AS pontuacao_total

        FROM equipe e

        LEFT JOIN robo ro
            ON ro.id_equipe = e.id_equipe

        LEFT JOIN resultado r
            ON r.id_robo = ro.id_robo

        GROUP BY
            e.id_equipe,
            e.nome_equipe

        ORDER BY
            pontuacao_total DESC,
            e.nome_equipe
        """
    )


# ==========================================
# LAYOUT PRINCIPAL
# ==========================================

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
                                html.H1(
                                    "Torneio de Robótica"
                                ),

                                html.P(
                                    "Painel de desempenho das equipes"
                                ),
                            ]
                        ),
                    ],
                    className="brand",
                ),

                html.Div(
                    "MySQL • Ranking e Resultados",
                    className="gm-header-tag",
                ),
            ],
            className="topbar",
        ),

        html.Main(
            [
                # Mensagens de erro
                html.Div(
                    id="mensagem",
                    className="message",
                ),

                # Indicadores do ranking
                html.Div(
                    id="cards",
                    className="cards",
                ),

                # ==================================
                # DASHBOARD ORIGINAL
                # ==================================

                html.Div(
                    [
                        # Gráfico do ranking
                        html.Div(
                            [
                                html.H2(
                                    "Ranking por pontuação"
                                ),

                                html.P(
                                    "As equipes com maior "
                                    "desempenho aparecem no topo."
                                ),

                                dcc.Graph(
                                    id="grafico",
                                    config={
                                        "displayModeBar": False
                                    },
                                ),
                            ],
                            className="panel chart-panel",
                        ),

                        # Tabela de classificação
                        html.Div(
                            [
                                html.H2(
                                    "Classificação"
                                ),

                                html.P(
                                    "Resumo das participações "
                                    "no torneio."
                                ),

                                tabela_ranking(),
                            ],
                            className="panel table-panel",
                        ),
                    ],
                    className="content-grid",
                ),

                # ==================================
                # NOVA ÁREA DE GERENCIAMENTO
                # ==================================

                criar_gerenciamento("rs"),

                # Rodapé
                html.Footer(
                    id="ultima-atualizacao"
                ),
            ],
            className="main",
        ),
    ],
    className="page gm-page",
)


# ==========================================
# ATUALIZAR RANKING E INDICADORES
# ==========================================

@app.callback(
    Output("cards", "children"),
    Output("grafico", "figure"),
    Output("tabela", "data"),
    Output("ultima-atualizacao", "children"),
    Output("mensagem", "children"),

    Input("rs-revisao", "data"),
)
def atualizar_ranking(_revisao):
    """
    Atualiza o ranking quando a página
    carrega ou quando um resultado é
    cadastrado, editado ou excluído.
    """

    try:
        ranking = buscar_ranking_atualizado()

        if not ranking:
            return (
                [],
                grafico_vazio(),
                [],
                "",
                "Nenhuma equipe cadastrada.",
            )

        # Soma de todas as pontuações
        total = sum(
            float(item["pontuacao_total"])
            for item in ranking
        )

        # Total de participações
        participacoes = sum(
            item["participacoes"]
            for item in ranking
        )

        # Equipe com maior pontuação
        lider = ranking[0]

        # ==================================
        # CARTÕES DE INDICADORES
        # ==================================

        indicadores = [
            card(
                "Equipes",
                str(len(ranking)),
                "equipes cadastradas",
            ),

            card(
                "Pontuação total",
                f"{total:.2f}",
                "pontos no torneio",
            ),

            card(
                "Participações",
                str(participacoes),
                "resultados registrados",
            ),

            card(
                "Equipe líder",
                lider["equipe"],
                (
                    f"{float(lider['pontuacao_total']):.2f} "
                    "pontos"
                ),
            ),
        ]

        # ==================================
        # TABELA DE CLASSIFICAÇÃO
        # ==================================

        tabela = [
            {
                "posicao": f"{posicao}º",
                "equipe": item["equipe"],
                "pontuacao": (
                    f"{float(item['pontuacao_total']):.2f}"
                ),
                "participacoes": item["participacoes"],
            }

            for posicao, item in enumerate(
                ranking,
                start=1,
            )
        ]

        # ==================================
        # DATA DA ATUALIZAÇÃO
        # ==================================

        atualizado = (
            "Última atualização: "
            + datetime.now().strftime(
                "%d/%m/%Y às %H:%M"
            )
        )

        # ==================================
        # RETORNO DOS COMPONENTES
        # ==================================

        return (
            indicadores,
            grafico_ranking(ranking),
            tabela,
            atualizado,
            "",
        )

    except (
        mysql.connector.Error,
        ValueError,
    ) as erro:

        return (
            [],
            grafico_vazio(),
            [],
            "",
            tratar_erro(erro),
        )


# ==========================================
# REGISTRO DOS CALLBACKS DO CRUD
# ==========================================

registrar_callbacks_gerenciamento(
    app,
    "rs",
)


# ==========================================
# INICIALIZAÇÃO DO SERVIDOR
# ==========================================

if __name__ == "__main__":
    app.run(
        debug=False,
        port=8050,
        use_reloader=False,
    )
