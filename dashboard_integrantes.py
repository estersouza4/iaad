import os
import dash
from dash import html, dcc, Input, Output, State, dash_table
import crud_integrantes
from componentes import CORES

# Pegando a senha da variável de ambiente, conforme o README do grupo
SENHA_MYSQL = os.environ.get("MYSQL_PASSWORD", "")

app = dash.Dash(__name__)

estilo_input = {
    "backgroundColor": CORES["painel_claro"], "color": CORES["texto"],
    "border": "1px solid " + CORES["texto_secundario"], "padding": "10px", 
    "margin": "5px", "borderRadius": "5px"
}

app.layout = html.Div(style={"backgroundColor": CORES["painel"], "color": CORES["texto"], "padding": "20px", "fontFamily": "sans-serif", "minHeight": "100vh"}, children=[
    html.H1("Gestão de Integrantes", style={"color": CORES["azul"]}),
    
    # Formulário de Cadastro/Edição
    html.Div(style={"backgroundColor": CORES["painel_claro"], "padding": "20px", "borderRadius": "8px", "marginBottom": "20px"}, children=[
        html.H3("Cadastrar / Editar Integrante"),
        dcc.Input(id="inp-id", type="number", placeholder="ID (Só p/ Editar/Excluir)", style=estilo_input),
        dcc.Input(id="inp-nome", type="text", placeholder="Nome do Integrante", style=estilo_input),
        dcc.Input(id="inp-funcao", type="text", placeholder="Função (Ex: Piloto)", style=estilo_input),
        dcc.Input(id="inp-data", type="text", placeholder="Data Nasc (YYYY-MM-DD)", style=estilo_input),
        dcc.Input(id="inp-equipe", type="number", placeholder="ID da Equipe (Vínculo)", style=estilo_input),
        html.Br(), html.Br(),
        html.Button("Cadastrar", id="btn-cadastrar", n_clicks=0, style={"backgroundColor": CORES["verde"], "padding": "10px 20px", "border": "none", "cursor": "pointer", "marginRight": "10px", "fontWeight": "bold"}),
        html.Button("Atualizar", id="btn-atualizar", n_clicks=0, style={"backgroundColor": CORES["amarelo"], "padding": "10px 20px", "border": "none", "cursor": "pointer", "marginRight": "10px", "fontWeight": "bold"}),
        html.Button("Excluir", id="btn-excluir", n_clicks=0, style={"backgroundColor": "red", "color": "white", "padding": "10px 20px", "border": "none", "cursor": "pointer", "fontWeight": "bold"}),
        html.Div(id="mensagem-alerta", style={"marginTop": "15px", "color": CORES["amarelo"]})
    ]),

    # Tabela de Listagem
    html.Button("Recarregar Lista", id="btn-listar", n_clicks=0, style={"backgroundColor": CORES["azul"], "padding": "10px 20px", "border": "none", "cursor": "pointer", "marginBottom": "15px", "fontWeight": "bold"}),
    html.Div(id="tabela-container")
])

@app.callback(
    Output("mensagem-alerta", "children"),
    Output("tabela-container", "children"),
    Input("btn-cadastrar", "n_clicks"),
    Input("btn-atualizar", "n_clicks"),
    Input("btn-excluir", "n_clicks"),
    Input("btn-listar", "n_clicks"),
    State("inp-id", "value"), State("inp-nome", "value"),
    State("inp-funcao", "value"), State("inp-data", "value"), State("inp-equipe", "value"),
    prevent_initial_call=True
)
def gerenciar_integrantes(btn_cad, btn_atualizar, btn_excluir, btn_list, id_int, nome, funcao, data, id_equipe):
    ctx = dash.callback_context
    botao_clicado = ctx.triggered[0]["prop_id"].split(".")[0]
    msg = ""

    try:
        if botao_clicado == "btn-cadastrar" and nome:
            crud_integrantes.cadastrar_integrante(SENHA_MYSQL, nome, funcao, data, id_equipe)
            msg = "Integrante cadastrado com sucesso!"
        elif botao_clicado == "btn-atualizar" and id_int:
            crud_integrantes.atualizar_integrante(SENHA_MYSQL, id_int, nome, funcao, data, id_equipe)
            msg = "Integrante atualizado com sucesso!"
        elif botao_clicado == "btn-excluir" and id_int:
            crud_integrantes.excluir_integrante(SENHA_MYSQL, id_int)
            msg = "Integrante excluído com sucesso!"
        
        # Recarrega a tabela sempre (Read)
        lista = crud_integrantes.listar_integrantes(SENHA_MYSQL)
        tabela = dash_table.DataTable(
            data=lista,
            style_header={"backgroundColor": CORES["painel_claro"], "color": CORES["texto_secundario"]},
            style_cell={"backgroundColor": CORES["painel"], "color": CORES["texto"], "textAlign": "left"}
        )
        return msg, tabela

    except Exception as e:
        return f"Erro: {str(e)} (Verifique se o ID da Equipe existe!)", dash.no_update

if __name__ == "__main__":
    # Seguindo o padrão do grupo de usar portas diferentes, rodando na 8053
    app.run_server(debug=True, port=8053)