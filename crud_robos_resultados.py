
from datetime import date
from decimal import Decimal, InvalidOperation
import json

from crud_equipes import conectar_banco


# ============================================
# FUNÇÕES AUXILIARES DO BANCO
# ============================================

def consultar(sql, parametros=()):
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(sql, parametros)
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def modificar(sql, parametros):
    conexao = conectar_banco()
    cursor = None

    try:
        cursor = conexao.cursor()
        cursor.execute(sql, parametros)
        quantidade = cursor.rowcount
        novo_id = cursor.lastrowid
        conexao.commit()
        return quantidade, novo_id
    except Exception:
        conexao.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def texto_obrigatorio(valor, campo, limite):
    texto = str(valor or "").strip()

    if not texto:
        raise ValueError(f"O campo {campo} é obrigatório.")

    if len(texto) > limite:
        raise ValueError(
            f"{campo} permite no máximo {limite} caracteres."
        )

    return texto


def inteiro_positivo(valor, campo):
    try:
        numero = int(valor)
        if numero <= 0 or str(valor).strip() != str(numero):
            raise ValueError
        return numero
    except (TypeError, ValueError):
        raise ValueError(
            f"{campo} deve ser um número inteiro positivo."
        )


def validar_data(valor):
    if not valor:
        return None

    try:
        return date.fromisoformat(str(valor))
    except (TypeError, ValueError):
        raise ValueError("Informe uma data válida.")


def validar_pontuacao(valor):
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError):
        raise ValueError("Informe uma pontuação válida.")

    if not numero.is_finite():
        raise ValueError("A pontuação deve ser finita.")

    if numero < 0:
        raise ValueError(
            "A pontuação não pode ser negativa."
        )

    if numero > Decimal("9999.99"):
        raise ValueError(
            "A pontuação máxima é 9999,99."
        )

    if numero != numero.quantize(Decimal("0.01")):
        raise ValueError(
            "A pontuação permite no máximo duas casas decimais."
        )

    return numero


# ============================================
# EQUIPES - OPÇÕES DO FORMULÁRIO
# ============================================

def listar_opcoes_equipes():
    linhas = consultar(
        """
        SELECT id_equipe, nome_equipe
        FROM equipe
        ORDER BY nome_equipe
        """
    )

    return [
        {
            "label": f"{e['id_equipe']} - {e['nome_equipe']}",
            "value": e["id_equipe"],
        }
        for e in linhas
    ]


# ============================================
# ROBÔS - READ
# ============================================

def listar_robos():
    linhas = consultar(
        """
        SELECT
            r.id_robo,
            r.nome_robo,
            r.categoria,
            r.data_criacao,
            r.id_equipe,
            e.nome_equipe,
            (
                SELECT COUNT(*)
                FROM resultado res
                WHERE res.id_robo = r.id_robo
            ) AS quantidade_resultados
        FROM robo r
        INNER JOIN equipe e
            ON e.id_equipe = r.id_equipe
        ORDER BY r.id_robo
        """
    )

    for r in linhas:
        r["id"] = str(r["id_robo"])

        if r["data_criacao"]:
            r["data_criacao"] = (
                r["data_criacao"].isoformat()
            )

    return linhas


def listar_opcoes_robos():
    linhas = consultar(
        """
        SELECT
            r.id_robo,
            r.nome_robo,
            e.nome_equipe
        FROM robo r
        INNER JOIN equipe e
            ON e.id_equipe = r.id_equipe
        ORDER BY r.nome_robo
        """
    )

    return [
        {
            "label": (
                f"{r['id_robo']} - {r['nome_robo']} "
                f"({r['nome_equipe']})"
            ),
            "value": r["id_robo"],
        }
        for r in linhas
    ]


# ============================================
# ROBÔS - CREATE
# ============================================

def cadastrar_robo(nome, categoria, data_criacao, id_equipe):
    nome = texto_obrigatorio(
        nome, "Nome do robô", 100
    )
    categoria = texto_obrigatorio(
        categoria, "Categoria", 50
    )
    data_criacao = validar_data(data_criacao)
    id_equipe = inteiro_positivo(
        id_equipe, "Equipe"
    )

    _, novo_id = modificar(
        """
        INSERT INTO robo
            (nome_robo, categoria, data_criacao, id_equipe)
        VALUES (%s, %s, %s, %s)
        """,
        (nome, categoria, data_criacao, id_equipe),
    )

    return novo_id


# ============================================
# ROBÔS - UPDATE
# ============================================

def atualizar_robo(
    id_robo, nome, categoria, data_criacao, id_equipe
):
    id_robo = inteiro_positivo(id_robo, "ID do robô")
    nome = texto_obrigatorio(
        nome, "Nome do robô", 100
    )
    categoria = texto_obrigatorio(
        categoria, "Categoria", 50
    )
    data_criacao = validar_data(data_criacao)
    id_equipe = inteiro_positivo(id_equipe, "Equipe")

    linhas, _ = modificar(
        """
        UPDATE robo
        SET nome_robo = %s,
            categoria = %s,
            data_criacao = %s,
            id_equipe = %s
        WHERE id_robo = %s
        """,
        (
            nome, categoria, data_criacao,
            id_equipe, id_robo,
        ),
    )

    return linhas


# ============================================
# ROBÔS - DELETE
# ============================================

def excluir_robo(id_robo):
    id_robo = inteiro_positivo(id_robo, "ID do robô")

    linhas, _ = modificar(
        "DELETE FROM robo WHERE id_robo = %s",
        (id_robo,),
    )

    return linhas


# ============================================
# RESULTADOS - READ
# ============================================

def listar_resultados():
    linhas = consultar(
        """
        SELECT
            res.nome_prova,
            res.classificacao,
            res.pontuacao,
            res.id_robo,
            r.nome_robo,
            e.nome_equipe
        FROM resultado res
        INNER JOIN robo r
            ON r.id_robo = res.id_robo
        INNER JOIN equipe e
            ON e.id_equipe = r.id_equipe
        ORDER BY
            res.nome_prova,
            res.classificacao
        """
    )

    for r in linhas:
        r["id"] = json.dumps(
            [r["nome_prova"], r["classificacao"]],
            ensure_ascii=False,
        )

        r["pontuacao"] = float(r["pontuacao"])

    return linhas


# ============================================
# RESULTADOS - CREATE
# ============================================

def cadastrar_resultado(
    nome_prova, classificacao, pontuacao, id_robo
):
    nome_prova = texto_obrigatorio(
        nome_prova, "Nome da prova", 100
    )
    classificacao = inteiro_positivo(
        classificacao, "Classificação"
    )
    pontuacao = validar_pontuacao(pontuacao)
    id_robo = inteiro_positivo(id_robo, "Robô")

    modificar(
        """
        INSERT INTO resultado
            (nome_prova, classificacao, pontuacao, id_robo)
        VALUES (%s, %s, %s, %s)
        """,
        (
            nome_prova, classificacao,
            pontuacao, id_robo,
        ),
    )


# ============================================
# RESULTADOS - UPDATE
# ============================================

def atualizar_resultado(
    prova_anterior,
    classificacao_anterior,
    nome_prova,
    classificacao,
    pontuacao,
    id_robo,
):
    nome_prova = texto_obrigatorio(
        nome_prova, "Nome da prova", 100
    )
    classificacao = inteiro_positivo(
        classificacao, "Classificação"
    )
    pontuacao = validar_pontuacao(pontuacao)
    id_robo = inteiro_positivo(id_robo, "Robô")

    linhas, _ = modificar(
        """
        UPDATE resultado
        SET nome_prova = %s,
            classificacao = %s,
            pontuacao = %s,
            id_robo = %s
        WHERE nome_prova = %s
          AND classificacao = %s
        """,
        (
            nome_prova,
            classificacao,
            pontuacao,
            id_robo,
            prova_anterior,
            classificacao_anterior,
        ),
    )

    return linhas


# ============================================
# RESULTADOS - DELETE
# ============================================

def excluir_resultado(nome_prova, classificacao):
    linhas, _ = modificar(
        """
        DELETE FROM resultado
        WHERE nome_prova = %s
          AND classificacao = %s
        """,
        (
            nome_prova,
            inteiro_positivo(
                classificacao, "Classificação"
            ),
        ),
    )

    return linhas
