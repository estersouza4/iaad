"""Validações puras: testes que NÃO acessam o banco de dados."""

from datetime import date
from decimal import Decimal

import pytest

from crud_equipes import validar_equipe
from crud_robos_resultados import (
    inteiro_positivo,
    texto_obrigatorio,
    validar_data,
    validar_pontuacao,
)


def test_equipe_valida_remove_espacos():
    assert validar_equipe(" Robótica ", " Escola A ", " Recife ") == (
        "Robótica", "Escola A", "Recife"
    )


@pytest.mark.parametrize("campo", [0, 1, 2])
def test_equipe_exige_todos_os_campos(campo):
    valores = ["Equipe A", "Escola A", "Recife"]
    valores[campo] = "   "
    with pytest.raises(ValueError, match="obrigatório"):
        validar_equipe(*valores)


def test_equipe_respeita_tamanho_maximo():
    with pytest.raises(ValueError, match="no máximo"):
        validar_equipe("E" * 101, "Escola", "Recife")


def test_nome_robo_nao_pode_ser_vazio():
    with pytest.raises(ValueError, match="obrigatório"):
        texto_obrigatorio("   ", "Nome do robô", 100)


def test_nome_robo_nao_pode_ultrapassar_limite():
    with pytest.raises(ValueError, match="máximo"):
        texto_obrigatorio("X" * 101, "Nome do robô", 100)


@pytest.mark.parametrize("invalido", [None, "", 0, -2, "2.5", "abc"])
def test_identificadores_precisam_ser_inteiros_positivos(invalido):
    with pytest.raises(ValueError, match="inteiro positivo"):
        inteiro_positivo(invalido, "ID")


def test_identificador_valido():
    assert inteiro_positivo("3", "ID") == 3


def test_data_valida_e_opcional():
    assert validar_data("2026-11-17") == date(2026, 11, 17)
    assert validar_data(None) is None


def test_data_invalida():
    with pytest.raises(ValueError, match="data válida"):
        validar_data("2026-02-30")


@pytest.mark.parametrize("valor", ["-1", "abc", "NaN", "Infinity", "0.001", "10000"])
def test_pontuacao_rejeita_valores_invalidos(valor):
    with pytest.raises(ValueError):
        validar_pontuacao(valor)


def test_pontuacao_aceita_zeros_e_duas_casas():
    assert validar_pontuacao("0") == Decimal("0")
    assert validar_pontuacao("97.75") == Decimal("97.75")
