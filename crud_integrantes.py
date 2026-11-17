import mysql.connector

def obter_conexao(senha):
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=senha,
        database="torneio_robotica"
    )

def cadastrar_integrante(senha, nome, funcao, data_nasc, id_equipe):
    conexao = obter_conexao(senha)
    cursor = conexao.cursor()
    try:
        # A validação do vínculo (FK) ocorre naturalmente pelo MySQL
        query = """
            INSERT INTO integrante (nome_integrante, funcao, data_nascimento, id_equipe) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (nome, funcao, data_nasc, id_equipe))
        conexao.commit()
    finally:
        cursor.close()
        conexao.close()

def listar_integrantes(senha):
    conexao = obter_conexao(senha)
    cursor = conexao.cursor(dictionary=True)
    try:
        query = """
            SELECT i.id_integrante, i.nome_integrante, i.funcao, 
                   i.data_nascimento, e.nome_equipe, i.id_equipe
            FROM integrante i
            JOIN equipe e ON i.id_equipe = e.id_equipe
            ORDER BY i.nome_integrante
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexao.close()

def atualizar_integrante(senha, id_integrante, nome, funcao, data_nasc, id_equipe):
    conexao = obter_conexao(senha)
    cursor = conexao.cursor()
    try:
        query = """
            UPDATE integrante 
            SET nome_integrante = %s, funcao = %s, data_nascimento = %s, id_equipe = %s
            WHERE id_integrante = %s
        """
        cursor.execute(query, (nome, funcao, data_nasc, id_equipe, id_integrante))
        conexao.commit()
    finally:
        cursor.close()
        conexao.close()

def excluir_integrante(senha, id_integrante):
    conexao = obter_conexao(senha)
    cursor = conexao.cursor()
    try:
        cursor.execute("DELETE FROM integrante WHERE id_integrante = %s", (id_integrante,))
        conexao.commit()
    finally:
        cursor.close()
        conexao.close()