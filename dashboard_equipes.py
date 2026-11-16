
import mysql.connector

from dash import (
    Dash, Input, Output, State,
    ctx, dcc, html, dash_table
)

from componentes import CORES
from crud_equipes import (
    listar_equipes,
    cadastrar_equipe,
    atualizar_equipe,
    excluir_equipe,
)


app = Dash(__name__)
app.title = "Equipes | Torneio de Robótica"

OCULTO = {"display": "none"}
VISIVEL = {"display": "flex"}


def indicador(titulo, valor, detalhe):
    return html.Div(
        [
            html.P(titulo, className="card-title"),
            html.H2(str(valor), className="card-value"),
            html.P(detalhe, className="card-detail"),
        ],
        className="metric-card",
    )


def campo(titulo, identificador, limite):
    return html.Div(
        [
            html.Label(titulo),
            dcc.Input(
                id=identificador,
                type="text",
                maxLength=limite,
                placeholder=f"Informe {titulo.lower()}",
                className="eq-input",
            ),
        ],
        className="eq-field",
    )


def obter_indicadores(equipes):
    return [
        indicador(
            "Equipes cadastradas",
            len(equipes),
            "registradas no torneio",
        ),
        indicador(
            "Escolas",
            len(set(e["escola"] for e in equipes)),
            "instituições participantes",
        ),
        indicador(
            "Cidades",
            len(set(e["cidade"] for e in equipes)),
            "localidades representadas",
        ),
        indicador(
            "Robôs",
            sum(e["quantidade_robos"] for e in equipes),
            "vinculados às equipes",
        ),
    ]


def mensagem_erro(erro):
    if isinstance(erro, ValueError):
        return str(erro)

    if isinstance(erro, mysql.connector.IntegrityError):
        if erro.errno == 1451:
            return (
                "Não é possível excluir esta equipe: "
                "existem robôs vinculados a ela. "
                "A chave estrangeira impede a exclusão."
            )
        if erro.errno == 1062:
            return "Já existe um registro com esta chave."
        return "O banco impediu a operação por integridade."

    if isinstance(erro, mysql.connector.Error):
        return f"Erro ao acessar o MySQL: {erro.msg}"

    return "Ocorreu um erro inesperado."


app.layout = html.Div(
    [
        dcc.Store(id="eq-modo"),
        dcc.Store(id="eq-id"),

        html.Header(
            [
                html.Div(
                    [
                        html.Div("🤖", className="logo"),
                        html.Div(
                            [
                                html.H1("Torneio de Robótica"),
                                html.P(
                                    "Administração e gerenciamento de equipes"
                                ),
                            ]
                        ),
                    ],
                    className="brand",
                ),
                html.Div(
                    [
                        html.Span(
                            "Gerenciamento",
                            className="eq-header-tag",
                        ),
                        html.Button(
                            "↻ Atualizar",
                            id="eq-atualizar-lista",
                            className="eq-btn eq-btn-outline",
                        ),
                    ],
                    className="eq-header-actions",
                ),
            ],
            className="topbar",
        ),

        html.Main(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.P(
                                    "ADMINISTRAÇÃO / EQUIPES",
                                    className="eq-eyebrow",
                                ),
                                html.H2(
                                    "Gerenciamento de equipes",
                                    className="eq-heading",
                                ),
                                html.P(
                                    "Visualize, cadastre e gerencie "
                                    "as equipes participantes do torneio.",
                                    className="eq-description",
                                ),
                            ]
                        ),
                        html.Button(
                            "+ Nova equipe",
                            id="eq-nova",
                            className="eq-btn eq-btn-primary",
                        ),
                    ],
                    className="eq-section-header",
                ),

                html.Div(id="eq-aviso", className="eq-alert"),

                html.Div(
                    id="eq-indicadores",
                    className="cards",
                ),

                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H2(
                                                    "Equipes cadastradas"
                                                ),
                                                html.P(
                                                    "Selecione uma linha "
                                                    "para editar ou excluir."
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Button(
                                                    "Editar selecionada",
                                                    id="eq-editar",
                                                    className=(
                                                        "eq-btn eq-btn-outline"
                                                    ),
                                                ),
                                                html.Button(
                                                    "Excluir selecionada",
                                                    id="eq-excluir",
                                                    className=(
                                                        "eq-btn eq-btn-danger"
                                                    ),
                                                ),
                                            ],
                                            className="eq-actions",
                                        ),
                                    ],
                                    className="eq-table-header",
                                ),

                                dash_table.DataTable(
                                    id="eq-tabela",
                                    columns=[
                                        {
                                            "name": "ID",
                                            "id": "id_equipe",
                                        },
                                        {
                                            "name": "Equipe",
                                            "id": "nome_equipe",
                                        },
                                        {
                                            "name": "Escola",
                                            "id": "escola",
                                        },
                                        {
                                            "name": "Cidade",
                                            "id": "cidade",
                                        },
                                        {
                                            "name": "Robôs",
                                            "id": "quantidade_robos",
                                        },
                                        {
                                            "name": "Integrantes",
                                            "id": "quantidade_integrantes",
                                        },
                                    ],
                                    data=[],
                                    row_selectable="single",
                                    selected_rows=[],
                                    page_size=8,
                                    sort_action="native",
                                    style_table={
                                        "overflowX": "auto",
                                    },
                                    style_header={
                                        "backgroundColor": (
                                            CORES["painel_claro"]
                                        ),
                                        "color": CORES["texto_secundario"],
                                        "padding": "14px 12px",
                                        "border": "none",
                                        "fontWeight": "bold",
                                    },
                                    style_cell={
                                        "backgroundColor": CORES["painel"],
                                        "color": CORES["texto"],
                                        "padding": "14px 12px",
                                        "border": "none",
                                        "textAlign": "left",
                                        "fontFamily": "inherit",
                                        "minWidth": "95px",
                                    },
                                    style_data_conditional=[
                                        {
                                            "if": {
                                                "state": "selected"
                                            },
                                            "backgroundColor": "#164e63",
                                            "color": "#ffffff",
                                        }
                                    ],
                                ),

                                html.P(
                                    "Dica: marque o seletor à esquerda "
                                    "de uma equipe para realizar ações.",
                                    className="eq-tip",
                                ),
                            ],
                            className="panel eq-table-panel",
                        ),
                    ]
                ),

                html.Footer(
                    "Torneio de Robótica • Gerenciamento de equipes"
                ),
            ],
            className="main",
        ),

        # Modal de cadastro e edição.
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H2(id="eq-modal-titulo"),
                                html.Button(
                                    "×",
                                    id="eq-cancelar",
                                    className="eq-close",
                                ),
                            ],
                            className="eq-modal-header",
                        ),
                        html.P(
                            "Preencha os campos da equipe.",
                            className="eq-modal-description",
                        ),
                        campo("Nome da equipe", "eq-nome", 100),
                        campo("Escola", "eq-escola", 100),
                        campo("Cidade", "eq-cidade", 80),
                        html.Div(
                            [
                                html.Button(
                                    "Cancelar",
                                    id="eq-cancelar-rodape",
                                    className="eq-btn eq-btn-outline",
                                ),
                                html.Button(
                                    "Salvar equipe",
                                    id="eq-salvar",
                                    className="eq-btn eq-btn-primary",
                                ),
                            ],
                            className="eq-modal-actions",
                        ),
                    ],
                    className="eq-modal",
                ),
            ],
            id="eq-modal-formulario",
            className="eq-overlay",
            style=OCULTO,
        ),

        # Modal de confirmação de exclusão.
        html.Div(
            [
                html.Div(
                    [
                        html.H2("Excluir equipe?"),
                        html.P(
                            id="eq-texto-exclusao",
                            className="eq-modal-description",
                        ),
                        html.Div(
                            [
                                html.Button(
                                    "Cancelar",
                                    id="eq-cancelar-exclusao",
                                    className="eq-btn eq-btn-outline",
                                ),
                                html.Button(
                                    "Confirmar exclusão",
                                    id="eq-confirmar-exclusao",
                                    className="eq-btn eq-btn-danger",
                                ),
                            ],
                            className="eq-modal-actions",
                        ),
                    ],
                    className="eq-modal",
                ),
            ],
            id="eq-modal-exclusao",
            className="eq-overlay",
            style=OCULTO,
        ),
    ],
    className="page eq-page",
)


@app.callback(
    Output("eq-tabela", "data"),
    Output("eq-tabela", "selected_rows"),
    Output("eq-indicadores", "children"),
    Output("eq-modal-formulario", "style"),
    Output("eq-modal-exclusao", "style"),
    Output("eq-modal-titulo", "children"),
    Output("eq-modo", "data"),
    Output("eq-id", "data"),
    Output("eq-nome", "value"),
    Output("eq-escola", "value"),
    Output("eq-cidade", "value"),
    Output("eq-texto-exclusao", "children"),
    Output("eq-aviso", "children"),
    Output("eq-aviso", "className"),
    Input("eq-atualizar-lista", "n_clicks"),
    Input("eq-nova", "n_clicks"),
    Input("eq-editar", "n_clicks"),
    Input("eq-excluir", "n_clicks"),
    Input("eq-salvar", "n_clicks"),
    Input("eq-cancelar", "n_clicks"),
    Input("eq-cancelar-rodape", "n_clicks"),
    Input("eq-confirmar-exclusao", "n_clicks"),
    Input("eq-cancelar-exclusao", "n_clicks"),
    State("eq-tabela", "selected_rows"),
    State("eq-tabela", "data"),
    State("eq-modo", "data"),
    State("eq-id", "data"),
    State("eq-nome", "value"),
    State("eq-escola", "value"),
    State("eq-cidade", "value"),
)
def gerenciar_equipes(
    _atualizar, _nova, _editar, _excluir, _salvar,
    _cancelar, _cancelar_rodape, _confirmar, _cancelar_exclusao,
    selecionadas, dados_atuais, modo, id_equipe,
    nome, escola, cidade,
):
    acao = ctx.triggered_id

    dados = dados_atuais or []
    selecionadas = selecionadas or []
    formulario = OCULTO
    confirmacao = OCULTO
    titulo = "Cadastrar equipe"
    texto_exclusao = ""
    aviso = ""
    tipo_aviso = "eq-alert"

    def equipe_selecionada():
        if not selecionadas:
            return None

        indice = selecionadas[0]
        if indice < 0 or indice >= len(dados):
            return None

        return dados[indice]

    try:
        if acao == "eq-nova":
            modo = "criar"
            id_equipe = None
            nome = escola = cidade = ""
            formulario = VISIVEL
            titulo = "Cadastrar nova equipe"

        elif acao == "eq-editar":
            equipe = equipe_selecionada()

            if equipe is None:
                aviso = "Selecione uma equipe na tabela."
                tipo_aviso = "eq-alert eq-alert-warning"
            else:
                modo = "editar"
                id_equipe = equipe["id_equipe"]
                nome = equipe["nome_equipe"]
                escola = equipe["escola"]
                cidade = equipe["cidade"]
                titulo = "Editar equipe"
                formulario = VISIVEL

        elif acao == "eq-excluir":
            equipe = equipe_selecionada()

            if equipe is None:
                aviso = "Selecione uma equipe na tabela."
                tipo_aviso = "eq-alert eq-alert-warning"
            else:
                id_equipe = equipe["id_equipe"]
                texto_exclusao = (
                    f"Deseja excluir '{equipe['nome_equipe']}'? "
                    "Essa ação não pode ser desfeita. "
                    "Integrantes vinculados podem ser removidos "
                    "em cascata. Equipes com robôs vinculados "
                    "não podem ser excluídas."
                )
                confirmacao = VISIVEL

        elif acao == "eq-salvar":
            formulario = VISIVEL
            titulo = (
                "Editar equipe" if modo == "editar"
                else "Cadastrar nova equipe"
            )

            if modo == "editar" and id_equipe is not None:
                linhas = atualizar_equipe(
                    id_equipe, nome, escola, cidade
                )
                aviso = (
                    "Equipe atualizada com sucesso!"
                    if linhas
                    else "Nenhuma alteração foi realizada."
                )
            elif modo == "criar":
                novo_id = cadastrar_equipe(
                    nome, escola, cidade
                )
                aviso = (
                    f"Equipe cadastrada! ID: {novo_id}"
                )
            else:
                raise ValueError(
                    "Abra o formulário de cadastro ou edição."
                )

            formulario = OCULTO
            tipo_aviso = "eq-alert eq-alert-success"
            nome = escola = cidade = ""
            id_equipe = None
            modo = None
            selecionadas = []

        elif acao == "eq-confirmar-exclusao":
            if id_equipe is None:
                raise ValueError(
                    "Nenhuma equipe selecionada para exclusão."
                )

            linhas = excluir_equipe(id_equipe)
            aviso = (
                "Equipe excluída com sucesso!"
                if linhas
                else "A equipe não foi encontrada."
            )
            tipo_aviso = "eq-alert eq-alert-success"
            id_equipe = None
            selecionadas = []

        elif acao in (
            "eq-cancelar",
            "eq-cancelar-rodape",
            "eq-cancelar-exclusao",
        ):
            modo = None
            id_equipe = None
            nome = escola = cidade = ""

        # READ: sempre consulta os dados atualizados do banco.
        equipes = listar_equipes()
        dados = equipes
        cards = obter_indicadores(equipes)

        return (
            dados, selecionadas, cards,
            formulario, confirmacao, titulo,
            modo, id_equipe, nome, escola, cidade,
            texto_exclusao, aviso, tipo_aviso,
        )

    except (
        mysql.connector.Error,
        ValueError,
    ) as erro:
        aviso = mensagem_erro(erro)
        tipo_aviso = "eq-alert eq-alert-error"

        # Preserva os campos quando falha o cadastro/edição.
        if acao == "eq-salvar":
            formulario = VISIVEL
            titulo = (
                "Editar equipe" if modo == "editar"
                else "Cadastrar nova equipe"
            )

        # Evita uma confirmação de exclusão presa na tela.
        if acao == "eq-confirmar-exclusao":
            confirmacao = OCULTO
            id_equipe = None

        cards = obter_indicadores(dados)

        return (
            dados, selecionadas, cards,
            formulario, confirmacao, titulo,
            modo, id_equipe, nome, escola, cidade,
            texto_exclusao, aviso, tipo_aviso,
        )


if __name__ == "__main__":
    app.run(
        debug=False,
        port=8052,
        use_reloader=False
    )