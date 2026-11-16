
import os
import mysql.connector


def conectar_banco():
    """
    Abre uma conexão com o banco MySQL.
    Usa as configurações definidas no ambiente.
    """

    senha = os.getenv("MYSQL_PASSWORD")

    if senha is None:
        raise ValueError(
            "Configure a variável MYSQL_PASSWORD antes "
            "de iniciar o dashboard."
        )

    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        user=os.getenv("MYSQL_USER", "root"),
        password=senha,
        database=os.getenv(
            "MYSQL_DATABASE", "torneio_robotica"
        ),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        connection_timeout=5,
        use_pure=True,
    )


def validar_equipe(nome, escola, cidade):
    """
    Valida os dados de uma equipe antes
    do cadastro ou atualização.
    """

    campos = [
        ("Nome da equipe", nome, 100),
        ("Escola", escola, 100),
        ("Cidade", cidade, 80),
    ]

    valores = []

    for rotulo, valor, limite in campos:
        valor = (valor or "").strip()

        if not valor:
            raise ValueError(
                f"O campo {rotulo} é obrigatório."
            )

        if len(valor) > limite:
            raise ValueError(
                f"O campo {rotulo} permite no máximo "
                f"{limite} caracteres."
            )

        valores.append(valor)

    return tuple(valores)


# ==========================================
# READ - LISTAR EQUIPES
# ==========================================

def listar_equipes():
    """
    Retorna todas as equipes cadastradas,
    incluindo a quantidade de robôs e
    integrantes vinculados.
    """

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                e.id_equipe,
                e.nome_equipe,
                e.escola,
                e.cidade,

                (
                    SELECT COUNT(*)
                    FROM robo r
                    WHERE r.id_equipe = e.id_equipe
                ) AS quantidade_robos,

                (
                    SELECT COUNT(*)
                    FROM integrante i
                    WHERE i.id_equipe = e.id_equipe
                ) AS quantidade_integrantes

            FROM equipe e
            ORDER BY e.id_equipe
            """
        )

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()

        conexao.close()


# ==========================================
# READ - BUSCAR EQUIPE PELO ID
# ==========================================

def buscar_equipe(id_equipe):
    """
    Busca uma equipe específica pelo ID.
    """

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id_equipe,
                nome_equipe,
                escola,
                cidade
            FROM equipe
            WHERE id_equipe = %s
            """,
            (id_equipe,),
        )

        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()

        conexao.close()


# ==========================================
# CREATE - CADASTRAR EQUIPE
# ==========================================

def cadastrar_equipe(nome, escola, cidade):
    """
    Cadastra uma nova equipe no banco.
    Retorna o ID gerado automaticamente.
    """

    nome, escola, cidade = validar_equipe(
        nome,
        escola,
        cidade,
    )

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            INSERT INTO equipe (
                nome_equipe,
                escola,
                cidade
            )
            VALUES (%s, %s, %s)
            """,
            (nome, escola, cidade),
        )

        novo_id = cursor.lastrowid

        conexao.commit()

        return novo_id

    except Exception:
        conexao.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        conexao.close()


# ==========================================
# UPDATE - ATUALIZAR EQUIPE
# ==========================================

def atualizar_equipe(
    id_equipe,
    nome,
    escola,
    cidade,
):
    """
    Atualiza os dados de uma equipe existente.
    Retorna a quantidade de linhas alteradas.
    """

    nome, escola, cidade = validar_equipe(
        nome,
        escola,
        cidade,
    )

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE equipe
            SET
                nome_equipe = %s,
                escola = %s,
                cidade = %s
            WHERE id_equipe = %s
            """,
            (
                nome,
                escola,
                cidade,
                id_equipe,
            ),
        )

        linhas_afetadas = cursor.rowcount

        conexao.commit()

        return linhas_afetadas

    except Exception:
        conexao.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        conexao.close()


# ==========================================
# DELETE - EXCLUIR EQUIPE
# ==========================================

def excluir_equipe(id_equipe):
    """
    Exclui uma equipe pelo ID.

    O MySQL aplica automaticamente as
    restrições de chave estrangeira (FK).

    Equipes com robôs vinculados não podem
    ser excluídas devido ao ON DELETE RESTRICT.

    Integrantes vinculados podem ser excluídos
    em cascata, conforme a estrutura do banco.
    """

    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            DELETE FROM equipe
            WHERE id_equipe = %s
            """,
            (id_equipe,),
        )

        linhas_afetadas = cursor.rowcount

        conexao.commit()

        return linhas_afetadas

    except Exception:
        conexao.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        conexao.close()
