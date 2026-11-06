import mysql.connector


def buscar_ranking(senha):
    conexao = mysql.connector.connect(
        host="localhost",
        user="root",
        password=senha,
        database="torneio_robotica",
    )
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                e.nome_equipe AS equipe,
                COUNT(r.id_robo) AS participacoes,
                COALESCE(SUM(r.pontuacao), 0) AS pontuacao_total
            FROM equipe e
            LEFT JOIN robo ro ON ro.id_equipe = e.id_equipe
            LEFT JOIN resultado r ON r.id_robo = ro.id_robo
            GROUP BY e.id_equipe, e.nome_equipe
            ORDER BY pontuacao_total DESC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conexao.close()


def buscar_robos(senha):
    conexao = mysql.connector.connect(
        host="localhost",
        user="root",
        password=senha,
        database="torneio_robotica",
    )
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT e.nome_equipe AS equipe, COUNT(ro.id_robo) AS quantidade_robos
            FROM equipe e
            LEFT JOIN robo ro ON ro.id_equipe = e.id_equipe
            GROUP BY e.id_equipe, e.nome_equipe
            ORDER BY quantidade_robos DESC, e.nome_equipe
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conexao.close()


def buscar_equipes(senha):
    conexao = mysql.connector.connect(
        host="localhost",
        user="root",
        password=senha,
        database="torneio_robotica",
    )
    cursor = conexao.cursor()
    try:
        cursor.execute("SELECT * FROM equipe")
        return cursor.fetchall()
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    senha = input("Digite a senha do MySQL: ")

    try:
        equipes = buscar_equipes(senha)

        print("\nEquipes cadastradas:\n")
        for equipe in equipes:
            print(equipe)
    except mysql.connector.Error as erro:
        print(f"Erro ao conectar ao MySQL: {erro}")
