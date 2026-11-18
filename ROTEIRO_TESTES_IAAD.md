# IAAD — Testes de CRUD e integridade referencial (Integrante C)

**Projeto:** Torneio de Robótica — IAAD  
**Data da verificação:** 17/11/2026  
**Ambiente:** Windows, VS Code, Python 3.12.10, pytest 9.2.0, MySQL local (Workbench: Local instance MySQL80)  
**Escopo:** banco `torneio_robotica` e funções de CRUD da aplicação.

## 1. Resultado da execução

| Suíte | Quantidade | Resultado |
|---|---:|---|
| `tests/test_validacoes.py` | 23 | **23 aprovados** |
| `tests/test_integracao_mysql.py` | 12 | **12 aprovados** |
| **Total** | **35** | **35 aprovados; nenhuma falha relatada** |

**Evidência:** os resultados das suítes individuais foram apresentados no terminal do VS Code (`23 passed in 0.62s` e `12 passed in 2.37s`). A suíte completa foi executada com `python -m pytest -v` e sua conclusão bem-sucedida foi confirmada pelo responsável. Guardar uma captura do resumo final de `python -m pytest -q` como evidência anexável à apresentação.

Esses resultados dizem respeito ao ambiente local testado; não garantem funcionamento de instalações ou versões futuras sem repetir os testes.

## 2. O que os testes verificam

### Validação em Python — 23 casos

- Campos obrigatórios e remoção de espaços em dados de equipes.
- Tamanho máximo dos nomes de equipe e robô.
- Identificadores inteiros positivos.
- Data válida e campo de data opcional.
- Pontuações aceitas e rejeitadas, incluindo valores negativos, não numéricos, infinitos e excesso de casas decimais.

### Integração com MySQL — 12 casos

| Caso | Verificação | Resultado |
|---|---|---|
| 1 | CRUD de `equipe` pelas funções da aplicação | Aprovado |
| 2 | CRUD de `robo` pelas funções da aplicação | Aprovado |
| 3 | CRUD de `resultado` pelas funções da aplicação | Aprovado |
| 4 | CRUD de `integrante` via SQL | Aprovado |
| 5 | FK rejeita robô vinculado a equipe inexistente (`1452`) | Aprovado |
| 6 | `ON DELETE RESTRICT` protege equipe com robô (`1451`) | Aprovado |
| 7 | `ON DELETE CASCADE` exclui resultados de robô excluído | Aprovado |
| 8 | `ON DELETE CASCADE` exclui integrantes de equipe excluída | Aprovado |
| 9 | `ON UPDATE CASCADE` propaga alteração de ID de robô | Aprovado |
| 10 | PK composta em `resultado` rejeita duplicata (`1062`) | Aprovado |
| 11 | Trigger `trg_validar_pontuacao` rejeita `INSERT` negativo (`SQLSTATE 45000`) | Aprovado |
| 12 | Procedure `sp_desempenho_equipe` calcula indicadores esperados | Aprovado |

A procedure foi verificada com uma equipe temporária, dois robôs e pontuações 10,50 e 19,75. O teste conferiu dois robôs, duas participações, total de 30,25 e maior pontuação de 19,75.

## 3. Como reproduzir

Na raiz do projeto, instalar as dependências:

```powershell
python -m pip install pytest mysql-connector-python
```

Configurar as variáveis de ambiente no mesmo terminal PowerShell. **Não escrever credenciais nos arquivos enviados ao GitHub.**

```powershell
$env:MYSQL_USER = "SEU_USUARIO_MYSQL"
$senhaSegura = Read-Host "Senha do MySQL" -AsSecureString
$env:MYSQL_PASSWORD = [System.Net.NetworkCredential]::new("", $senhaSegura).Password
Remove-Variable senhaSegura
$env:MYSQL_DATABASE = "torneio_robotica"
$env:IAAD_TESTAR_MYSQL = "SIM"
```

Executar os testes:

```powershell
python -m pytest -v
# Resumo compacto para captura de tela:
python -m pytest -q
```

**Atenção:** `IAAD_TESTAR_MYSQL=SIM` é necessário para executar os 12 testes reais. Sem isso, eles serão ignorados (`SKIPPED`), e não aprovados. O usuário deve ter acesso de leitura e escrita às quatro tabelas e permissão de `EXECUTE` na procedure.

## 4. Proteção do banco de dados

- Os testes criam dados temporários em transações e as revertem com `ROLLBACK` ao final. A fixture `crud_protegido` intercepta o `COMMIT` das funções CRUD para não persistir alterações de teste.
- Evitar outras operações concorrentes no banco durante os testes; utilizar preferencialmente uma base local de demonstração e ter backup.
- `AUTO_INCREMENT` pode deixar lacunas após testes revertidos; isso não implica perda de registros.
- **Não reexecutar `torneio_robotica_completo.sql` para testar**: o script contém `DROP DATABASE IF EXISTS torneio_robotica`, que apaga e recria a base.

## 5. Roteiro técnico para apresentação

1. Apresentar as quatro tabelas: `equipe`, `integrante`, `robo` e `resultado`.
2. Mostrar a saída final do pytest: **35 testes aprovados** (23 de validação + 12 de integração).
3. Explicar a FK: impedir cadastro de robô ligado a equipe inexistente (erro `1452`).
4. Explicar `RESTRICT`: impedir excluir uma equipe que ainda possui robôs (erro `1451`).
5. Explicar `CASCADE`: excluir um robô temporário e verificar a exclusão de seus resultados; mencionar também a exclusão de integrantes ao apagar a equipe.
6. Mostrar que a PK composta (`nome_prova`, `classificacao`) impede registro duplicado (erro `1062`).
7. Explicar que `trg_validar_pontuacao` impede a inserção de pontuação negativa no próprio MySQL, independentemente do Dash (`SQLSTATE 45000`).
8. Apresentar `CALL sp_desempenho_equipe(id_da_equipe)` e o cálculo do desempenho (robôs, participações e pontuações).

Os testes automatizados complementam, mas não substituem eventuais demonstrações práticas exigidas pela professora. Para demonstrar operações de exclusão, **utilizar somente registros fictícios**.

## 6. Limitações e recomendações

- O teste de `integrante` utiliza SQL direto porque a versão do projeto analisada ainda não possuía um módulo de CRUD dessa tabela. A interface Dash e seus cliques não são cobertos pelos testes automatizados desta entrega.
- O SQL analisado contém trigger de pontuação negativa somente para `BEFORE INSERT`, não para `UPDATE`. A validação da aplicação impede entradas negativas nas funções testadas, mas atualizações diretas no SQL exigiriam uma regra adicional para a mesma garantia.
- A execução inicial da integração falhou por credenciais locais incorretas (`1045 Access denied`); após configurar a conta MySQL correta, todos os 12 testes de integração passaram. Isso foi um problema de ambiente, não uma reprovação funcional.
- Não incluir senhas, prints com credenciais, `__pycache__`, `*.pyc` ou `.pytest_cache` no commit.

## 7. Arquivos da entrega individual

```text
tests/
    conftest.py
    test_validacoes.py
    test_integracao_mysql.py
pytest.ini
ROTEIRO_TESTES_IAAD.md
```

**Sugestão de commit:** `test: valida CRUD, integridade referencial, trigger e procedure`