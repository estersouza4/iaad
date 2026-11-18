import os
import subprocess
import sys
import atexit
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from dash import Dash, Input, Output, State, dcc, html

from crud_equipes import conectar_banco


PASTA_PROJETO = Path(__file__).resolve().parent
RELATORIO_PYTEST = PASTA_PROJETO / "relatorios" / "resultado_pytest.xml"

APLICACOES = {
    "ranking": ("Ranking", "http://127.0.0.1:8050", "dashboard_ranking.py"),
    "robos": ("Robôs e resultados", "http://127.0.0.1:8051", "dashboard_robos.py"),
    "equipes": ("Equipes", "http://127.0.0.1:8052", "dashboard_equipes.py"),
    "integrantes": ("Integrantes", "http://127.0.0.1:8053", "dashboard_integrantes.py"),
}


def iniciar_aplicacoes():
    processos = []
    ambiente = os.environ.copy()

    for _, _, arquivo in APLICACOES.values():
        processo = subprocess.Popen(
            [sys.executable, str(PASTA_PROJETO / arquivo)],
            cwd=str(PASTA_PROJETO),
            env=ambiente,
        )
        processos.append(processo)

    return processos


processos = []


def encerrar_aplicacoes():
    global processos

    for processo in processos:
        if processo.poll() is None:
            processo.terminate()
            try:
                processo.wait(timeout=3)
            except subprocess.TimeoutExpired:
                processo.kill()

    processos = []


atexit.register(encerrar_aplicacoes)



def classificar_teste(nome, classe):
    identificador = f"{classe}.{nome}".lower()
    if "test_validacoes" in identificador:
        return "Validações Python"
    if "test_integracao_mysql" in identificador:
        return "Integração MySQL"
    if "test_painel_geral" in identificador:
        return "Painel Geral"
    return "Outros testes"


def carregar_resultados_testes():
    """Lê um relatório gerado pelo pytest, sem executar testes nem alterar o BD."""
    if not RELATORIO_PYTEST.is_file():
        return html.Div([
            html.H3("Relatório ainda não disponível"),
            html.P("Execute o pytest com --junitxml=relatorios/resultado_pytest.xml "
                   "e clique em Atualizar relatório."),
        ])

    try:
        raiz = ET.parse(RELATORIO_PYTEST).getroot()
        casos = list(raiz.iter("testcase"))
        if not casos:
            return html.P("O arquivo XML não contém casos de teste.")

        agrupados = {}
        detalhes = []
        totais = {"aprovados": 0, "falhas": 0, "ignorados": 0}
        for caso in casos:
            nome = caso.get("name", "Teste sem nome")
            classe = caso.get("classname", "")
            categoria = classificar_teste(nome, classe)
            if caso.find("skipped") is not None:
                situacao = "IGNORADO"
                totais["ignorados"] += 1
            elif caso.find("failure") is not None or caso.find("error") is not None:
                situacao = "FALHOU"
                totais["falhas"] += 1
            else:
                situacao = "APROVADO"
                totais["aprovados"] += 1
            agrupados.setdefault(categoria, {"total": 0, "aprovados": 0})
            agrupados[categoria]["total"] += 1
            if situacao == "APROVADO":
                agrupados[categoria]["aprovados"] += 1
            detalhes.append((nome, categoria, situacao))

        modificado = datetime.fromtimestamp(RELATORIO_PYTEST.stat().st_mtime)
        destaques = [
            ("Chave estrangeira (FK)", "fk_rejeita_robo_sem_equipe"),
            ("Exclusão em cascata (robô → resultados)", "cascade_exclui_resultados_ao_excluir_robo"),
            ("Proteção RESTRICT (equipe com robô)", "fk_restrict_impede_excluir_equipe_com_robo"),
            ("Trigger de pontuação", "trigger_impede_pontuacao_negativa_no_sql"),
            ("Stored procedure", "procedure_calcula_desempenho_da_equipe"),
        ]
        itens_destaque = []
        for rotulo, fragmento in destaques:
            encontrados = [d for d in detalhes if fragmento in d[0]]
            estado = encontrados[0][2] if encontrados else "NÃO EXECUTADO"
            itens_destaque.append(html.Div(
                [html.Span(rotulo), html.Strong(estado, className=(
                    "teste-ok" if estado == "APROVADO" else "teste-alerta"))],
                className="teste-linha",
            ))

        return html.Div([
            html.P("Relatório atualizado em: " + modificado.strftime("%d/%m/%Y %H:%M"),
                   className="teste-data"),
            html.Div([
                html.Div([html.Strong(str(len(casos))), html.Small("Executados")],
                         className="teste-indicador"),
                html.Div([html.Strong(str(totais["aprovados"])), html.Small("Aprovados")],
                         className="teste-indicador"),
                html.Div([html.Strong(str(totais["falhas"])), html.Small("Falhas")],
                         className="teste-indicador"),
                html.Div([html.Strong(str(totais["ignorados"])), html.Small("Ignorados")],
                         className="teste-indicador"),
            ], className="teste-indicadores"),
            html.H4("Grupos de testes"),
            *[html.Div([html.Span(cat), html.Strong(
                f"{numeros['aprovados']}/{numeros['total']} aprovados")],
                className="teste-linha") for cat, numeros in agrupados.items()],
            html.H4("Integridade referencial"),
            *itens_destaque,
            html.Details([
                html.Summary("Ver todos os testes (" + str(len(detalhes)) + ")"),
                html.Div([html.Div(
                    [html.Span(nome), html.Strong(estado, className=(
                        "teste-ok" if estado == "APROVADO" else "teste-alerta"))],
                    className="teste-linha") for nome, _, estado in detalhes],
                    className="teste-lista-completa")
            ]),
            html.P("Resultados registrados pelo pytest; esta tela não executa testes.",
                   className="teste-data"),
        ])
    except (ET.ParseError, OSError, ValueError) as erro:
        return html.P(f"Não foi possível ler o relatório: {erro}",
                      className="teste-alerta")


def listar_opcoes_equipes():
    """Consulta equipes reais sem modificar o banco."""
    conexao = conectar_banco()
    cursor = None
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT id_equipe, nome_equipe FROM equipe ORDER BY nome_equipe")
        return [
            {"label": f"{linha['nome_equipe']} (ID {linha['id_equipe']})",
             "value": int(linha["id_equipe"])}
            for linha in cursor.fetchall()
        ]
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def consultar_desempenho(id_equipe):
    """Executa a procedure original: CALL sp_desempenho_equipe(?)."""
    if isinstance(id_equipe, bool) or not isinstance(id_equipe, int) or id_equipe <= 0:
        raise ValueError("Selecione uma equipe válida.")

    conexao = conectar_banco()
    cursor = None
    try:
        cursor = conexao.cursor()
        cursor.callproc("sp_desempenho_equipe", (id_equipe,))
        registros = []
        for resultado in cursor.stored_results():
            colunas = [coluna[0] for coluna in resultado.description]
            registros.extend(dict(zip(colunas, linha)) for linha in resultado.fetchall())
        return registros[0] if registros else None
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def montar_resultado_desempenho(registro):
    if not registro:
        return html.P("A procedure não encontrou dados para a equipe selecionada.",
                      className="teste-alerta")

    indicadores = [
        ("Robôs", registro.get("quantidade_robos")),
        ("Participações", registro.get("participacoes")),
        ("Pontuação total", registro.get("pontuacao_total")),
        ("Pontuação média", registro.get("pontuacao_media")),
        ("Maior pontuação", registro.get("maior_pontuacao")),
    ]

    def formatar(valor):
        if valor is None:
            return "Sem resultados"
        if isinstance(valor, (int, float)):
            return str(valor) if isinstance(valor, int) else f"{valor:.2f}"
        try:
            from decimal import Decimal
            if isinstance(valor, Decimal):
                return f"{valor:.2f}"
        except ImportError:
            pass
        return str(valor)

    return html.Div([
        html.H4(f"{registro.get('nome_equipe', 'Equipe')} — ID {registro.get('id_equipe', '')}"),
        html.Div([
            html.Div([html.Strong(formatar(valor)), html.Small(rotulo)],
                     className="teste-indicador")
            for rotulo, valor in indicadores
        ], className="teste-indicadores"),
        html.P("Dados retornados diretamente por CALL sp_desempenho_equipe(id_equipe). "
               "Consulta somente leitura; nenhuma alteração é feita no banco.",
               className="teste-data"),
    ])


app = Dash(__name__)
app.title = "Painel Geral | Torneio de Robótica"

app.layout = html.Div(
    [
        html.Header(
            [
                html.Div(
                    [
                        html.Div("🤖", className="painel-logo"),
                        html.Div(
                            [
                                html.H1("Painel Geral"),
                                html.P("Torneio de Robótica"),
                            ]
                        ),
                    ],
                    className="painel-brand",
                ),
                html.Div(
                    [
                        html.Details(
                            [
                                html.Summary("🧪 Testes", className="painel-testes-botao"),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H3("Testes e Integridade"),
                                                html.Button("Atualizar relatório",
                                                            id="btn-atualizar-testes",
                                                            n_clicks=0,
                                                            className="painel-conectar"),
                                            ],
                                            className="teste-cabecalho",
                                        ),
                                        html.Div(id="resumo-testes"),
                                    ],
                                    className="painel-testes-conteudo",
                                ),
                            ],
                            className="painel-testes",
                        ),
                        html.Details(
                            [
                                html.Summary("📊 Desempenho da equipe",
                                             className="painel-testes-botao"),
                                html.Div(
                                    [
                                        html.H3("Stored procedure — Desempenho da equipe"),
                                        html.P("Selecione uma equipe e consulte a procedure "
                                               "sp_desempenho_equipe diretamente no MySQL.",
                                               className="teste-data"),
                                        dcc.Dropdown(
                                            id="equipe-procedure",
                                            options=[],
                                            placeholder="Conecte ao MySQL para listar equipes",
                                            clearable=False,
                                            className="procedure-seletor",
                                        ),
                                        html.Button(
                                            "Executar procedure",
                                            id="btn-procedure",
                                            n_clicks=0,
                                            className="painel-conectar",
                                        ),
                                        html.Div(id="resultado-procedure"),
                                    ],
                                    className="painel-testes-conteudo",
                                ),
                            ],
                            className="painel-testes",
                        ),
                        dcc.Input(
                            id="senha-mysql",
                            type="password",
                            placeholder="Senha do MySQL",
                            className="painel-senha",
                            debounce=True,
                        ),
                        html.Button(
                            "Conectar",
                            id="btn-conectar",
                            n_clicks=0,
                            className="painel-conectar",
                        ),
                    ],
                    className="painel-conexao",
                ),
            ],
            className="painel-topbar",
        ),
        html.Div(
            id="status-conexao",
            className="painel-status-mensagem",
        ),
        dcc.Tabs(
            id="abas-gerais",
            value="ranking",
            className="painel-tabs",
            children=[
                dcc.Tab(
                    label=titulo,
                    value=identificador,
                    className="painel-tab",
                    selected_className="painel-tab-selecionada",
                )
                for identificador, (titulo, _, _) in APLICACOES.items()
            ],
        ),
        html.Div(
            id="conteudo-geral",
            className="painel-conteudo",
        ),
    ],
    className="painel-geral",
)


@app.callback(
    Output("resumo-testes", "children"),
    Input("btn-atualizar-testes", "n_clicks"),
)
def atualizar_relatorio_testes(_):
    return carregar_resultados_testes()


@app.callback(
    Output("equipe-procedure", "options"),
    Output("equipe-procedure", "placeholder"),
    Input("status-conexao", "children"),
    prevent_initial_call=True,
)
def carregar_equipes_procedure(_):
    try:
        opcoes = listar_opcoes_equipes()
        return opcoes, ("Selecione a equipe" if opcoes else "Nenhuma equipe cadastrada")
    except Exception:
        return [], "Não foi possível listar equipes; confira a conexão MySQL"


@app.callback(
    Output("resultado-procedure", "children"),
    Input("btn-procedure", "n_clicks"),
    State("equipe-procedure", "value"),
    prevent_initial_call=True,
)
def executar_procedure(_, id_equipe):
    if id_equipe is None:
        return html.P("Selecione uma equipe antes de executar.", className="teste-alerta")
    try:
        registro = consultar_desempenho(id_equipe)
        return montar_resultado_desempenho(registro)
    except Exception as erro:
        # Não exibimos mensagens SQL detalhadas (que podem conter informações internas).
        return html.P("Falha ao consultar a procedure. Verifique se ela existe "
                      "e se o usuário MySQL tem permissão EXECUTE.",
                      className="teste-alerta")


@app.callback(
    Output("conteudo-geral", "children"),
    Input("abas-gerais", "value"),
)
def alterar_tela(tela):
    _, url, _ = APLICACOES[tela]
    return html.Iframe(
        src=url,
        title=APLICACOES[tela][0],
        className="painel-frame",
    )


@app.callback(
    Output("status-conexao", "children"),
    Output("status-conexao", "className"),
    Input("btn-conectar", "n_clicks"),
    State("senha-mysql", "value"),
    prevent_initial_call=True,
)
def conectar_painel(_, senha):
    global processos

    if not senha:
        return "Digite a senha do MySQL.", "painel-status-mensagem painel-status-erro"

    encerrar_aplicacoes()
    os.environ["MYSQL_PASSWORD"] = senha

    try:
        processos = iniciar_aplicacoes()
        return (
            "Conectando às telas... aguarde alguns segundos.",
            "painel-status-mensagem painel-status-sucesso",
        )
    except Exception as erro:
        return (
            f"Não foi possível iniciar as telas: {erro}",
            "painel-status-mensagem painel-status-erro",
        )


app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * { box-sizing: border-box; }
            body {
                margin: 0;
                overflow: hidden;
                background: #0b1120;
                color: #f8fafc;
                font-family: Inter, Segoe UI, sans-serif;
            }
            .painel-geral { min-height: 100vh; }
            .painel-topbar {
                height: 82px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 14px 24px;
                border-bottom: 1px solid #1e293b;
                background: #0f172a;
            }
            .painel-brand {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            .painel-brand h1 { margin: 0; font-size: 22px; }
            .painel-brand p {
                margin: 4px 0 0;
                color: #94a3b8;
                font-size: 13px;
            }
            .painel-logo {
                width: 48px;
                height: 48px;
                display: grid;
                place-items: center;
                border-radius: 14px;
                background: linear-gradient(135deg, #2563eb, #06b6d4);
                font-size: 24px;
            }
            .painel-status {
                padding: 8px 12px;
                border: 1px solid #334155;
                border-radius: 999px;
                color: #94a3b8;
                font-size: 12px;
            }
            .painel-conexao {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .painel-senha {
                width: 190px;
                height: 40px;
                padding: 10px 12px;
                border: 1px solid #334155;
                border-radius: 8px;
                outline: none;
                background: #111827;
                color: #f8fafc;
            }
            .painel-senha:focus {
                border-color: #22d3ee;
            }
            .painel-conectar {
                height: 40px;
                padding: 0 16px;
                border: 0;
                border-radius: 8px;
                background: #0891b2;
                color: white;
                font-weight: 700;
                cursor: pointer;
            }
            .painel-status-mensagem {
                min-height: 34px;
                padding: 9px 24px;
                background: #111827;
                color: #94a3b8;
                font-size: 12px;
            }
            .painel-status-sucesso { color: #86efac; }
            .painel-status-erro { color: #fca5a5; }
            .painel-tabs {
                height: 54px;
                background: #111827;
            }
            .painel-tab {
                height: 54px !important;
                padding: 16px 24px !important;
                border: 0 !important;
                border-right: 1px solid #1e293b !important;
                background: #111827 !important;
                color: #94a3b8 !important;
                font-weight: 600;
            }
            .painel-tab-selecionada {
                border-bottom: 3px solid #22d3ee !important;
                background: #172033 !important;
                color: #22d3ee !important;
            }
            .procedure-seletor { margin: 12px 0; color: #0f172a; }
            .procedure-seletor .Select-control { background: #f8fafc; }
            .procedure-seletor .Select-menu-outer { background: #f8fafc; }
            .painel-testes { position: relative; z-index: 100; }
            .painel-testes-botao {
                cursor: pointer; padding: 9px 12px; border: 1px solid #334155;
                border-radius: 8px; color: #e2e8f0; font-weight: 600;
                list-style: none; white-space: nowrap;
            }
            .painel-testes-botao::-webkit-details-marker { display: none; }
            .painel-testes[open] .painel-testes-botao { border-color: #22d3ee; }
            .painel-testes-conteudo {
                position: fixed; right: 20px; top: 75px; width: min(580px, 95vw);
                max-height: calc(100vh - 95px); overflow-y: auto;
                background: #0f172a; border: 1px solid #334155;
                border-radius: 12px; box-shadow: 0 20px 50px #0008;
                padding: 18px; z-index: 1000;
            }
            .teste-cabecalho {
                display: flex; align-items: center; justify-content: space-between;
                gap: 12px; margin-bottom: 12px;
            }
            .teste-cabecalho h3 { margin: 0; font-size: 17px; }
            .teste-data { font-size: 12px; color: #94a3b8; }
            .teste-indicadores {
                display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
                margin: 16px 0;
            }
            .teste-indicador {
                background: #172033; border: 1px solid #334155;
                padding: 10px; border-radius: 8px; text-align: center;
                display: flex; flex-direction: column; gap: 4px;
            }
            .teste-indicador strong { font-size: 22px; color: #f8fafc; }
            .teste-indicador small { color: #94a3b8; }
            .painel-testes-conteudo h4 { margin-bottom: 6px; }
            .teste-linha {
                display: flex; justify-content: space-between; gap: 16px;
                padding: 8px 0; border-bottom: 1px solid #243047;
                font-size: 12px; overflow-wrap: anywhere;
            }
            .teste-ok { color: #86efac; white-space: nowrap; }
            .teste-alerta { color: #fca5a5; white-space: nowrap; }
            .teste-lista-completa { max-height: 240px; overflow-y: auto; }
            .painel-testes-conteudo summary { cursor: pointer; margin: 14px 0; }
            .painel-conteudo {
                height: calc(100vh - 170px);
                background: #0b1120;
            }
            .painel-frame {
                width: 100%;
                height: 100%;
                border: 0;
                display: block;
                background: #0b1120;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>
"""


if __name__ == "__main__":
    try:
        app.run(debug=False, port=8054, use_reloader=False)
    finally:
        encerrar_aplicacoes()

