
import mysql.connector

from dash import (
    Input, Output, State, ctx,
    dcc, html, dash_table
)

from componentes import CORES

from crud_robos_resultados import (
    listar_robos,
    listar_resultados,
    listar_opcoes_equipes,
    listar_opcoes_robos,
    cadastrar_robo,
    atualizar_robo,
    excluir_robo,
    cadastrar_resultado,
    atualizar_resultado,
    excluir_resultado,
)


OCULTO = {"display": "none"}
VISIVEL = {"display": "flex"}


def campo(nome, identificador, tipo="text", limite=None):
    props = {
        "id": identificador,
        "type": tipo,
        "className": "gm-input",
        "placeholder": f"Informe {nome.lower()}",
    }

    if limite is not None:
        props["maxLength"] = limite

    if tipo == "number":
        props["min"] = 0
        props["step"] = "any"

    return html.Div(
        [
            html.Label(nome),
            dcc.Input(**props),
        ],
        className="gm-field",
    )


def dropdown(nome, identificador):
    return html.Div(
        [
            html.Label(nome),
            dcc.Dropdown(
                id=identificador,
                options=[],
                placeholder="Selecione uma opção",
                clearable=True,
                className="gm-select",
            ),
        ],
        className="gm-field",
    )


def criar_gerenciamento(tipo):
    """
    rb = CRUD de robôs
    rs = CRUD de resultados
    """

    if tipo not in ("rb", "rs"):
        raise ValueError("Tipo de gerenciamento inválido.")

    robo = tipo == "rb"
    titulo = "robôs" if robo else "resultados"
    singular = "robô" if robo else "resultado"

    if robo:
        campos = [
            campo("Nome do robô", "rb-nome", limite=100),
            campo("Categoria", "rb-categoria", limite=50),
            campo("Data de criação", "rb-data", "date"),
            dropdown("Equipe", "rb-vinculo"),
        ]

        colunas = [
            {"name": "ID", "id": "id_robo"},
            {"name": "Robô", "id": "nome_robo"},
            {"name": "Categoria", "id": "categoria"},
            {"name": "Data", "id": "data_criacao"},
            {"name": "Equipe", "id": "nome_equipe"},
            {
                "name": "Resultados",
                "id": "quantidade_resultados",
            },
        ]

    else:
        campos = [
            campo("Nome da prova", "rs-nome", limite=100),
            campo("Classificação", "rs-categoria", "number"),
            campo("Pontuação", "rs-data", "number"),
            dropdown("Robô", "rs-vinculo"),
        ]

        colunas = [
            {"name": "Prova", "id": "nome_prova"},
            {"name": "Classificação", "id": "classificacao"},
            {"name": "Pontuação", "id": "pontuacao"},
            {"name": "Robô", "id": "nome_robo"},
            {"name": "Equipe", "id": "nome_equipe"},
        ]

    return html.Section(
        [
            dcc.Store(id=f"{tipo}-modo"),
            dcc.Store(id=f"{tipo}-registro"),
            dcc.Store(id=f"{tipo}-revisao", data=0),

            html.Div(
                [
                    html.Div(
                        [
                            html.P(
                                "GERENCIAMENTO",
                                className="gm-eyebrow",
                            ),
                            html.H2(
                                f"Gerenciar {titulo}",
                                className="gm-heading",
                            ),
                            html.P(
                                "Cadastre, consulte, edite e exclua "
                                f"{titulo} diretamente no MySQL.",
                                className="gm-description",
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Button(
                                "↻ Atualizar",
                                id=f"{tipo}-atualizar",
                                className="gm-btn gm-btn-outline",
                            ),
                            html.Button(
                                f"+ Novo {singular}",
                                id=f"{tipo}-novo",
                                className="gm-btn gm-btn-primary",
                            ),
                        ],
                        className="gm-actions",
                    ),
                ],
                className="gm-heading-row",
            ),

            html.Div(
                id=f"{tipo}-aviso",
                className="gm-alert",
                role="status",
            ),

            html.Div(
                [
                    html.Div(
                        [
                            html.H2(f"{titulo.capitalize()} cadastrados"),
                            html.P(
                                "Selecione uma linha para editar ou excluir."
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Editar selecionado",
                                id=f"{tipo}-editar",
                                className="gm-btn gm-btn-outline",
                            ),
                            html.Button(
                                "Excluir selecionado",
                                id=f"{tipo}-excluir",
                                className="gm-btn gm-btn-danger",
                            ),
                        ],
                        className="gm-actions",
                    ),
                ],
                className="gm-table-header",
            ),

            dash_table.DataTable(
                id=f"{tipo}-tabela",
                columns=colunas,
                data=[],
                row_selectable="single",
                selected_row_ids=[],
                sort_action="native",
                filter_action="native",
                page_size=8,
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": CORES["painel_claro"],
                    "color": CORES["texto_secundario"],
                    "padding": "14px",
                    "border": "none",
                    "fontWeight": "600",
                },
                style_cell={
                    "backgroundColor": CORES["painel"],
                    "color": CORES["texto"],
                    "padding": "14px",
                    "border": "none",
                    "textAlign": "left",
                    "fontFamily": "inherit",
                    "minWidth": "100px",
                },
                style_data_conditional=[
                    {
                        "if": {"state": "selected"},
                        "backgroundColor": "#164e63",
                        "color": "#ffffff",
                    }
                ],
            ),

            html.P(
                "As alterações são aplicadas diretamente no banco.",
                className="gm-tip",
            ),

            # Modal de cadastro e edição
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H2(id=f"{tipo}-titulo-modal"),
                                    html.Button(
                                        "×",
                                        id=f"{tipo}-fechar",
                                        className="gm-close",
                                    ),
                                ],
                                className="gm-modal-header",
                            ),
                            html.P(
                                "Preencha os dados abaixo.",
                                className="gm-modal-description",
                            ),
                            *campos,
                            html.Div(
                                [
                                    html.Button(
                                        "Cancelar",
                                        id=f"{tipo}-cancelar",
                                        className="gm-btn gm-btn-outline",
                                    ),
                                    html.Button(
                                        "Salvar",
                                        id=f"{tipo}-salvar",
                                        className="gm-btn gm-btn-primary",
                                    ),
                                ],
                                className="gm-modal-actions",
                            ),
                        ],
                        className="gm-modal",
                    ),
                ],
                id=f"{tipo}-modal",
                className="gm-overlay",
                style=OCULTO,
            ),

            # Modal de confirmação de exclusão
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Confirmar exclusão"),
                            html.P(
                                id=f"{tipo}-texto-exclusao",
                                className="gm-modal-description",
                            ),
                            html.Div(
                                [
                                    html.Button(
                                        "Cancelar",
                                        id=f"{tipo}-cancelar-exclusao",
                                        className="gm-btn gm-btn-outline",
                                    ),
                                    html.Button(
                                        "Confirmar exclusão",
                                        id=f"{tipo}-confirmar",
                                        className="gm-btn gm-btn-danger",
                                    ),
                                ],
                                className="gm-modal-actions",
                            ),
                        ],
                        className="gm-modal",
                    ),
                ],
                id=f"{tipo}-modal-exclusao",
                className="gm-overlay",
                style=OCULTO,
            ),
        ],
        className="panel gm-table-panel",
    )


def tratar_erro(erro):
    if isinstance(erro, ValueError):
        return str(erro)

    if isinstance(erro, mysql.connector.IntegrityError):
        if erro.errno == 1062:
            return (
                "Já existe um resultado com esta prova "
                "e classificação."
            )

        if erro.errno == 1452:
            return (
                "A equipe ou o robô selecionado "
                "não existe no banco."
            )

        if erro.errno == 1451:
            return (
                "Operação bloqueada por uma chave estrangeira."
            )

        return "Operação impedida por integridade referencial."

    if isinstance(erro, mysql.connector.Error):
        return f"Erro no MySQL: {erro.msg}"

    return "Erro inesperado durante a operação."


def registrar_callbacks_gerenciamento(app, tipo):
    """Registra os callbacks para robôs ou resultados."""

    if tipo not in ("rb", "rs"):
        raise ValueError("Tipo de gerenciamento inválido.")

    robo = tipo == "rb"
    entidade = "Robô" if robo else "Resultado"

    @app.callback(
        Output(f"{tipo}-tabela", "data"),
        Output(f"{tipo}-tabela", "selected_row_ids"),
        Output(f"{tipo}-vinculo", "options"),
        Output(f"{tipo}-modal", "style"),
        Output(f"{tipo}-modal-exclusao", "style"),
        Output(f"{tipo}-titulo-modal", "children"),
        Output(f"{tipo}-nome", "value"),
        Output(f"{tipo}-categoria", "value"),
        Output(f"{tipo}-data", "value"),
        Output(f"{tipo}-vinculo", "value"),
        Output(f"{tipo}-modo", "data"),
        Output(f"{tipo}-registro", "data"),
        Output(f"{tipo}-texto-exclusao", "children"),
        Output(f"{tipo}-aviso", "children"),
        Output(f"{tipo}-aviso", "className"),
        Output(f"{tipo}-revisao", "data"),

        Input(f"{tipo}-atualizar", "n_clicks"),
        Input(f"{tipo}-novo", "n_clicks"),
        Input(f"{tipo}-editar", "n_clicks"),
        Input(f"{tipo}-excluir", "n_clicks"),
        Input(f"{tipo}-salvar", "n_clicks"),
        Input(f"{tipo}-fechar", "n_clicks"),
        Input(f"{tipo}-cancelar", "n_clicks"),
        Input(f"{tipo}-confirmar", "n_clicks"),
        Input(f"{tipo}-cancelar-exclusao", "n_clicks"),

        State(f"{tipo}-tabela", "selected_row_ids"),
        State(f"{tipo}-tabela", "data"),
        State(f"{tipo}-vinculo", "options"),
        State(f"{tipo}-modo", "data"),
        State(f"{tipo}-registro", "data"),
        State(f"{tipo}-nome", "value"),
        State(f"{tipo}-categoria", "value"),
        State(f"{tipo}-data", "value"),
        State(f"{tipo}-vinculo", "value"),
        State(f"{tipo}-revisao", "data"),
    )
    def gerenciar(
        _atualizar, _novo, _editar, _excluir,
        _salvar, _fechar, _cancelar,
        _confirmar, _cancelar_exclusao,
        selecionados, dados, opcoes,
        modo, registro, nome, categoria,
        data, vinculo, revisao,
    ):
        acao = ctx.triggered_id
        selecionados = selecionados or []
        dados = dados or []
        opcoes = opcoes or []

        modal = OCULTO
        exclusao = OCULTO
        titulo = f"Cadastrar {entidade.lower()}"
        texto_exclusao = ""
        aviso = ""
        classe = "gm-alert"
        revisao = revisao or 0

        def selecionado():
            if not selecionados:
                return None

            return next(
                (
                    linha for linha in dados
                    if linha.get("id") == selecionados[0]
                ),
                None,
            )

        def retornar():
            return (
                dados,
                selecionados,
                opcoes,
                modal,
                exclusao,
                titulo,
                nome,
                categoria,
                data,
                vinculo,
                modo,
                registro,
                texto_exclusao,
                aviso,
                classe,
                revisao,
            )

        try:
            if acao == f"{tipo}-novo":
                modo = "criar"
                registro = None
                nome = categoria = data = vinculo = None
                modal = VISIVEL

            elif acao == f"{tipo}-editar":
                item = selecionado()

                if item is None:
                    aviso = "Selecione uma linha na tabela."
                    classe = "gm-alert gm-alert-warning"
                else:
                    modo = "editar"
                    titulo = f"Editar {entidade.lower()}"

                    if robo:
                        registro = item["id_robo"]
                        nome = item["nome_robo"]
                        categoria = item["categoria"]
                        data = item["data_criacao"]
                        vinculo = item["id_equipe"]
                    else:
                        registro = {
                            "nome_prova": item["nome_prova"],
                            "classificacao": item["classificacao"],
                        }
                        nome = item["nome_prova"]
                        categoria = item["classificacao"]
                        data = item["pontuacao"]
                        vinculo = item["id_robo"]

                    modal = VISIVEL

            elif acao == f"{tipo}-excluir":
                item = selecionado()

                if item is None:
                    aviso = "Selecione uma linha na tabela."
                    classe = "gm-alert gm-alert-warning"
                else:
                    if robo:
                        registro = item["id_robo"]
                        total = item["quantidade_resultados"]

                        texto_exclusao = (
                            f"Excluir o robô '{item['nome_robo']}'? "
                            f"Ele possui {total} resultado(s). "
                            "Resultados vinculados serão excluídos "
                            "em cascata. Esta ação é irreversível."
                        )
                    else:
                        registro = {
                            "nome_prova": item["nome_prova"],
                            "classificacao": item["classificacao"],
                        }

                        texto_exclusao = (
                            f"Excluir a classificação "
                            f"{item['classificacao']} da prova "
                            f"'{item['nome_prova']}'? "
                            "Esta ação é irreversível."
                        )

                    exclusao = VISIVEL

            elif acao == f"{tipo}-salvar":
                modal = VISIVEL

                if modo == "criar":
                    if robo:
                        cadastrar_robo(
                            nome, categoria, data, vinculo
                        )
                    else:
                        cadastrar_resultado(
                            nome, categoria, data, vinculo
                        )

                    aviso = f"{entidade} cadastrado com sucesso!"

                elif modo == "editar" and registro is not None:
                    if robo:
                        linhas = atualizar_robo(
                            registro,
                            nome, categoria, data, vinculo,
                        )
                    else:
                        linhas = atualizar_resultado(
                            registro["nome_prova"],
                            registro["classificacao"],
                            nome, categoria, data, vinculo,
                        )

                    aviso = (
                        f"{entidade} atualizado com sucesso!"
                        if linhas else
                        "Nenhum registro foi alterado."
                    )
                else:
                    raise ValueError(
                        "Abra o formulário antes de salvar."
                    )

                modal = OCULTO
                classe = "gm-alert gm-alert-success"
                selecionados = []
                registro = None
                modo = None
                nome = categoria = data = vinculo = None

            elif acao == f"{tipo}-confirmar":
                if registro is None:
                    raise ValueError(
                        "Nenhum registro para exclusão."
                    )

                if robo:
                    linhas = excluir_robo(registro)
                else:
                    linhas = excluir_resultado(
                        registro["nome_prova"],
                        registro["classificacao"],
                    )

                aviso = (
                    f"{entidade} excluído com sucesso!"
                    if linhas else
                    "Registro não encontrado."
                )
                classe = "gm-alert gm-alert-success"
                registro = None
                modo = None
                selecionados = []

            elif acao in (
                f"{tipo}-fechar",
                f"{tipo}-cancelar",
                f"{tipo}-cancelar-exclusao",
            ):
                modo = None
                registro = None
                nome = categoria = data = vinculo = None

            # Atualiza a listagem do banco.
            if robo:
                dados = listar_robos()
                opcoes = listar_opcoes_equipes()
            else:
                dados = listar_resultados()
                opcoes = listar_opcoes_robos()

            if acao is None or acao in (
                f"{tipo}-atualizar",
                f"{tipo}-salvar",
                f"{tipo}-confirmar",
            ):
                revisao += 1

            return retornar()

        except (mysql.connector.Error, ValueError) as erro:
            aviso = tratar_erro(erro)
            classe = "gm-alert gm-alert-error"

            if acao == f"{tipo}-salvar":
                modal = VISIVEL
                titulo = (
                    f"Editar {entidade.lower()}"
                    if modo == "editar"
                    else f"Cadastrar {entidade.lower()}"
                )

            return retornar()
