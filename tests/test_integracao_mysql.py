"""Testes reais de CRUD, FK, CASCADE, trigger e procedure.

Todos os registros criados nestes testes são temporários: a fixture mysql_db
faz ROLLBACK no fim, e crud_protegido bloqueia os commits dos CRUDs reais.
"""

from decimal import Decimal
from uuid import uuid4

import mysql.connector
import pytest

import crud_equipes as equipes
import crud_robos_resultados as robos_resultados


def nome_teste(prefixo="TESTE_C"):
    return f"{prefixo}_{uuid4().hex[:12]}"


def executar(db, sql, parametros=()):
    cursor = db.cursor()
    try:
        cursor.execute(sql, parametros)
        return cursor.lastrowid
    finally:
        cursor.close()


def escalar(db, sql, parametros=()):
    cursor = db.cursor()
    try:
        cursor.execute(sql, parametros)
        return cursor.fetchone()[0]
    finally:
        cursor.close()


def criar_equipe(db):
    return executar(
        db,
        "INSERT INTO equipe (nome_equipe, escola, cidade) VALUES (%s,%s,%s)",
        (nome_teste("EQUIPE"), "Escola de testes", "Recife"),
    )


def criar_robo(db, id_equipe):
    return executar(
        db,
        "INSERT INTO robo (nome_robo,categoria,data_criacao,id_equipe) "
        "VALUES (%s,%s,%s,%s)",
        (nome_teste("ROBO"), "Sumô", "2026-11-17", id_equipe),
    )


def criar_resultado(db, id_robo, pontuacao="10.50"):
    nome_prova = nome_teste("PROVA")
    executar(
        db,
        "INSERT INTO resultado (nome_prova,classificacao,pontuacao,id_robo) "
        "VALUES (%s,%s,%s,%s)",
        (nome_prova, 1, pontuacao, id_robo),
    )
    return nome_prova


# ---- CRUD COMPLETO DAS QUATRO TABELAS ----

def test_crud_equipes_da_aplicacao(crud_protegido):
    id_equipe = equipes.cadastrar_equipe(
        nome_teste("EQUIPE"), "Escola inicial", "Recife"
    )
    assert equipes.buscar_equipe(id_equipe)["cidade"] == "Recife"
    assert equipes.atualizar_equipe(
        id_equipe, "Equipe editada", "Escola nova", "Olinda"
    ) == 1
    assert equipes.buscar_equipe(id_equipe)["cidade"] == "Olinda"
    assert any(e["id_equipe"] == id_equipe for e in equipes.listar_equipes())
    assert equipes.excluir_equipe(id_equipe) == 1
    assert equipes.buscar_equipe(id_equipe) is None


def test_crud_robos_da_aplicacao(crud_protegido):
    id_equipe = criar_equipe(crud_protegido)
    id_robo = robos_resultados.cadastrar_robo(
        nome_teste("ROBO"), "Sumô", "2026-11-17", id_equipe
    )
    assert any(r["id_robo"] == id_robo for r in robos_resultados.listar_robos())
    assert robos_resultados.atualizar_robo(
        id_robo, "Robô Editado", "Seguidor de Linha", "2026-11-16", id_equipe
    ) == 1
    registro = next(r for r in robos_resultados.listar_robos() if r["id_robo"] == id_robo)
    assert registro["nome_robo"] == "Robô Editado"
    assert robos_resultados.excluir_robo(id_robo) == 1
    assert not any(r["id_robo"] == id_robo for r in robos_resultados.listar_robos())


def test_crud_resultados_da_aplicacao(crud_protegido):
    id_equipe = criar_equipe(crud_protegido)
    id_robo = criar_robo(crud_protegido, id_equipe)
    prova = nome_teste("PROVA")
    prova_editada = nome_teste("PROVA_EDITADA")

    robos_resultados.cadastrar_resultado(prova, 1, "11.25", id_robo)
    assert any(r["nome_prova"] == prova for r in robos_resultados.listar_resultados())

    assert robos_resultados.atualizar_resultado(
        prova, 1, prova_editada, 2, "22.50", id_robo
    ) == 1
    registro = next(
        r for r in robos_resultados.listar_resultados()
        if r["nome_prova"] == prova_editada and r["classificacao"] == 2
    )
    assert registro["pontuacao"] == 22.5

    assert robos_resultados.excluir_resultado(prova_editada, 2) == 1
    assert not any(
        r["nome_prova"] == prova_editada for r in robos_resultados.listar_resultados()
    )


def test_crud_integrantes_sql(mysql_db):
    id_equipe = criar_equipe(mysql_db)
    id_integrante = executar(
        mysql_db,
        "INSERT INTO integrante (nome_integrante,funcao,data_nascimento,id_equipe) "
        "VALUES (%s,%s,%s,%s)",
        (nome_teste("INTEGRANTE"), "Programador", "2007-11-17", id_equipe),
    )
    assert escalar(
        mysql_db, "SELECT COUNT(*) FROM integrante WHERE id_integrante=%s",
        (id_integrante,),
    ) == 1
    executar(
        mysql_db,
        "UPDATE integrante SET funcao=%s WHERE id_integrante=%s",
        ("Piloto", id_integrante),
    )
    assert escalar(
        mysql_db, "SELECT funcao FROM integrante WHERE id_integrante=%s",
        (id_integrante,),
    ) == "Piloto"
    executar(mysql_db, "DELETE FROM integrante WHERE id_integrante=%s", (id_integrante,))
    assert escalar(
        mysql_db, "SELECT COUNT(*) FROM integrante WHERE id_integrante=%s",
        (id_integrante,),
    ) == 0


# ---- INTEGRIDADE REFERENCIAL ----

def test_fk_rejeita_robo_sem_equipe(mysql_db):
    id_inexistente = 2147483647
    assert escalar(
        mysql_db, "SELECT COUNT(*) FROM equipe WHERE id_equipe=%s",
        (id_inexistente,),
    ) == 0

    with pytest.raises(mysql.connector.IntegrityError) as erro:
        executar(
            mysql_db,
            "INSERT INTO robo (nome_robo,categoria,id_equipe) VALUES (%s,%s,%s)",
            (nome_teste("INVALIDO"), "Sumô", id_inexistente),
        )
    assert erro.value.errno == 1452


def test_fk_restrict_impede_excluir_equipe_com_robo(mysql_db):
    id_equipe = criar_equipe(mysql_db)
    criar_robo(mysql_db, id_equipe)
    with pytest.raises(mysql.connector.IntegrityError) as erro:
        executar(mysql_db, "DELETE FROM equipe WHERE id_equipe=%s", (id_equipe,))
    assert erro.value.errno == 1451
    assert escalar(
        mysql_db, "SELECT COUNT(*) FROM equipe WHERE id_equipe=%s", (id_equipe,)
    ) == 1


def test_cascade_exclui_resultados_ao_excluir_robo(mysql_db):
    id_equipe = criar_equipe(mysql_db)
    id_robo = criar_robo(mysql_db, id_equipe)
    prova = criar_resultado(mysql_db, id_robo)
    executar(mysql_db, "DELETE FROM robo WHERE id_robo=%s", (id_robo,))
    assert escalar(
        mysql_db, "SELECT COUNT(*) FROM resultado WHERE nome_prova=%s", (prova,)
    ) == 0
    assert escalar(
        mysql_db, "SELECT COUNT(*) FROM equipe WHERE id_equipe=%s", (id_equipe,)
    ) == 1


def test_cascade_exclui_integrantes_ao_excluir_equipe(mysql_db):
    id_equipe = criar_equipe(mysql_db)
    id_integrante = executar(
        mysql_db,
        "INSERT INTO integrante (nome_integrante,funcao,id_equipe) "
        "VALUES (%s,%s,%s)",
        (nome_teste("INTEGRANTE"), "Piloto", id_equipe),
    )
    executar(mysql_db, "DELETE FROM equipe WHERE id_equipe=%s", (id_equipe,))
    assert escalar(
        mysql_db, "SELECT COUNT(*) FROM integrante WHERE id_integrante=%s",
        (id_integrante,),
    ) == 0


def test_on_update_cascade_propaga_id_robo(mysql_db):
    id_equipe = criar_equipe(mysql_db)
    id_robo = criar_robo(mysql_db, id_equipe)
    prova = criar_resultado(mysql_db, id_robo)

    novo_id = 1_500_000_000 + int(uuid4().hex[:6], 16)
    assert escalar(mysql_db, "SELECT COUNT(*) FROM robo WHERE id_robo=%s", (novo_id,)) == 0

    executar(
        mysql_db, "UPDATE robo SET id_robo=%s WHERE id_robo=%s",
        (novo_id, id_robo),
    )
    assert escalar(
        mysql_db, "SELECT id_robo FROM resultado WHERE nome_prova=%s", (prova,)
    ) == novo_id


def test_chave_primaria_composta_impede_classificacao_duplicada(mysql_db):
    id_equipe = criar_equipe(mysql_db)
    id_robo = criar_robo(mysql_db, id_equipe)
    prova = criar_resultado(mysql_db, id_robo)
    with pytest.raises(mysql.connector.IntegrityError) as erro:
        executar(
            mysql_db,
            "INSERT INTO resultado (nome_prova,classificacao,pontuacao,id_robo) "
            "VALUES (%s,%s,%s,%s)",
            (prova, 1, "99.00", id_robo),
        )
    assert erro.value.errno == 1062


# ---- TRIGGER E STORED PROCEDURE ----

def test_trigger_impede_pontuacao_negativa_no_sql(mysql_db):
    id_equipe = criar_equipe(mysql_db)
    id_robo = criar_robo(mysql_db, id_equipe)
    prova = nome_teste("NEGATIVO")

    # SQL direto para provar que a regra é do banco, não do formulário Python.
    with pytest.raises(mysql.connector.Error) as erro:
        executar(
            mysql_db,
            "INSERT INTO resultado (nome_prova,classificacao,pontuacao,id_robo) "
            "VALUES (%s,%s,%s,%s)",
            (prova, 1, "-5.00", id_robo),
        )
    assert erro.value.sqlstate == "45000"
    assert escalar(
        mysql_db, "SELECT COUNT(*) FROM resultado WHERE nome_prova=%s", (prova,)
    ) == 0


def test_procedure_calcula_desempenho_da_equipe(mysql_db):
    id_equipe = criar_equipe(mysql_db)
    id_robo_1 = criar_robo(mysql_db, id_equipe)
    id_robo_2 = criar_robo(mysql_db, id_equipe)
    criar_resultado(mysql_db, id_robo_1, "10.50")
    criar_resultado(mysql_db, id_robo_2, "19.75")

    cursor = mysql_db.cursor(dictionary=True)
    try:
        cursor.execute("CALL sp_desempenho_equipe(%s)", (id_equipe,))
        linhas = cursor.fetchall()
        while cursor.nextset():
            if cursor.with_rows:
                cursor.fetchall()
    finally:
        cursor.close()

    assert len(linhas) == 1
    dados = linhas[0]
    assert dados["id_equipe"] == id_equipe
    assert dados["quantidade_robos"] == 2
    assert dados["participacoes"] == 2
    assert Decimal(dados["pontuacao_total"]) == Decimal("30.25")
    assert Decimal(dados["maior_pontuacao"]) == Decimal("19.75")
