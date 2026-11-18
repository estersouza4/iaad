import os
import subprocess
import sys
import atexit
from pathlib import Path

from dash import Dash, Input, Output, State, dcc, html


PASTA_PROJETO = Path(__file__).resolve().parent

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
