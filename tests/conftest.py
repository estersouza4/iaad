"""Fixtures dos testes de integração do Torneio de Robótica.

Os testes nunca executam COMMIT. As operações dos módulos da aplicação
são redirecionadas para a mesma transação, revertida ao término de cada teste.
"""

import os
import sys
from pathlib import Path

import pytest

# Permite importar os módulos que ficam na raiz do repositório.
RAIZ_PROJETO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROJETO))


class ConexaoSemCommit:
    """Adaptador de testes que impede COMMIT e CLOSE dos CRUDs."""

    def __init__(self, conexao_real):
        self._conexao = conexao_real

    def cursor(self, *args, **kwargs):
        return self._conexao.cursor(*args, **kwargs)

    def commit(self):
        # Não persistir os registros que os CRUDs criarem durante o teste.
        pass

    def rollback(self):
        self._conexao.rollback()

    def close(self):
        # Só a fixture fecha a conexão depois do rollback final.
        pass


@pytest.fixture
def mysql_db():
    """Conexão real ao MySQL; alterações sempre revertidas no final."""
    if os.getenv("IAAD_TESTAR_MYSQL") != "SIM":
        pytest.skip(
            "Teste de integração desabilitado. "
            "Defina IAAD_TESTAR_MYSQL=SIM para habilitar."
        )

    if "MYSQL_PASSWORD" not in os.environ:
        pytest.fail("Configure MYSQL_PASSWORD antes de executar a integração.")

    from crud_equipes import conectar_banco

    try:
        conexao = conectar_banco()
    except Exception as erro:
        pytest.fail(f"Não foi possível conectar ao MySQL: {erro}")

    try:
        if conexao.database != "torneio_robotica":
            pytest.fail(
                "Por segurança, os testes exigem o banco torneio_robotica."
            )
        conexao.autocommit = False
        yield conexao
    finally:
        try:
            conexao.rollback()
        finally:
            conexao.close()


@pytest.fixture
def crud_protegido(mysql_db, monkeypatch):
    """Executa os CRUDs reais sem permitir commits permanentes."""
    import crud_equipes
    import crud_robos_resultados

    protegida = ConexaoSemCommit(mysql_db)
    monkeypatch.setattr(crud_equipes, "conectar_banco", lambda: protegida)
    monkeypatch.setattr(
        crud_robos_resultados,
        "conectar_banco",
        lambda: protegida,
    )
    return mysql_db
