import plotly.graph_objects as go
from dash import dash_table, dcc, html


CORES = {
    "painel": "#111827",
    "painel_claro": "#172033",
    "texto": "#f8fafc",
    "texto_secundario": "#94a3b8",
    "azul": "#22d3ee",
    "roxo": "#a78bfa",
    "verde": "#34d399",
    "amarelo": "#fbbf24",
}


def card(titulo, valor, detalhe):
    return html.Div(
        [
            html.P(titulo, className="card-title"),
            html.H2(valor, className="card-value"),
            html.P(detalhe, className="card-detail"),
        ],
        className="metric-card",
    )


def grafico_vazio():
    figura = go.Figure()
    figura.update_layout(
        paper_bgcolor=CORES["painel"],
        plot_bgcolor=CORES["painel"],
        font={"color": CORES["texto_secundario"]},
        annotations=[
            {
                "text": "Digite a senha e atualize os dados",
                "showarrow": False,
                "font": {"size": 16},
            }
        ],
    )
    return figura


def tabela_robos():
    return dash_table.DataTable(
        id="tabela-robos",
        columns=[
            {"name": "Equipe", "id": "equipe"},
            {"name": "Quantidade de robôs", "id": "quantidade_robos"},
        ],
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": CORES["painel_claro"],
            "color": CORES["texto_secundario"],
            "border": "none",
            "fontWeight": "600",
        },
        style_cell={
            "backgroundColor": CORES["painel"],
            "color": CORES["texto"],
            "border": "none",
            "padding": "16px 10px",
            "textAlign": "left",
        },
    )


def grafico_robos(robos):
    equipes = [item["equipe"] for item in reversed(robos)]
    quantidades = [item["quantidade_robos"] for item in reversed(robos)]
    paleta = [CORES["azul"], CORES["roxo"], CORES["verde"], CORES["amarelo"]]

    figura = go.Figure(
        go.Bar(
            x=quantidades,
            y=equipes,
            orientation="h",
            marker={"color": [paleta[i % 4] for i in range(len(equipes))]},
            text=[f"{quantidade} robô(s)" for quantidade in quantidades],
            textposition="outside",
            hovertemplate="%{y}<br>%{x} robô(s)<extra></extra>",
        )
    )
    figura.update_layout(
        paper_bgcolor=CORES["painel"],
        plot_bgcolor=CORES["painel"],
        font={"color": CORES["texto"]},
        margin={"l": 20, "r": 130, "t": 20, "b": 30},
        xaxis={
            "showgrid": False,
            "zeroline": False,
            "showticklabels": False,
            "range": [0, max(quantidades) * 1.5],
            "dtick": 1,
        },
        yaxis={"showgrid": False},
        height=360,
    )
    return figura


def grafico_ranking(ranking):
    equipes = [item["equipe"] for item in reversed(ranking)]
    pontuacoes = [float(item["pontuacao_total"]) for item in reversed(ranking)]
    paleta = [CORES["azul"], CORES["roxo"], CORES["verde"], CORES["amarelo"]]

    figura = go.Figure(
        go.Bar(
            x=pontuacoes,
            y=equipes,
            orientation="h",
            marker={"color": [paleta[i % 4] for i in range(len(equipes))]},
            text=[f"{pontuacao:.2f} pts" for pontuacao in pontuacoes],
            textposition="outside",
            hovertemplate="%{y}<br>%{x:.2f} pontos<extra></extra>",
        )
    )
    figura.update_layout(
        paper_bgcolor=CORES["painel"],
        plot_bgcolor=CORES["painel"],
        font={"color": CORES["texto"]},
        margin={"l": 20, "r": 155, "t": 20, "b": 30},
        xaxis={
            "showgrid": False,
            "zeroline": False,
            "showticklabels": False,
            "range": [0, max(pontuacoes) * 1.3],
        },
        yaxis={"showgrid": False},
        height=330,
    )
    return figura


def tabela_ranking():
    return dash_table.DataTable(
        id="tabela",
        columns=[
            {"name": "Posição", "id": "posicao"},
            {"name": "Equipe", "id": "equipe"},
            {"name": "Pontos", "id": "pontuacao"},
            {"name": "Participações", "id": "participacoes"},
        ],
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": CORES["painel_claro"],
            "color": CORES["texto_secundario"],
            "border": "none",
            "fontWeight": "600",
        },
        style_cell={
            "backgroundColor": CORES["painel"],
            "color": CORES["texto"],
            "border": "none",
            "padding": "14px 10px",
            "textAlign": "left",
        },
        style_data_conditional=[
            {
                "if": {"row_index": 0},
                "color": CORES["amarelo"],
                "fontWeight": "700",
            }
        ],
    )
