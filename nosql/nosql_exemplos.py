"""
MINICURSO NoSQL (MongoDB + PyMongo) — Torneio de Robótica (IAAD)

Demonstra:
1. Modelagem orientada a documentos (Embedded vs. Reference)
2. Operações CRUD completas (Create, Read, Update, Delete)
3. Relacionamentos ($lookup, $push,$pull) equivalentes aos JOINs do MySQL
"""

import os
from pprint import pprint
from pymongo import MongoClient


def conectar_mongodb():
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    cliente = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return cliente["torneio_robotica_nosql"]


def executar_minicurso():
    db = conectar_mongodb()

    # Limpa as coleções para permitir reexecução limpa do exemplo
    db.equipes.drop()
    db.robos.drop()

    print("\n=======================================================")
    print("1. CREATE — Documentos Embutidos (Embedded) e Referências")
    print("=======================================================")

    # Relacionamento 1:N EMBEDDED:
    # No MySQL, 'integrante' era uma tabela separada com ON DELETE CASCADE.
    # No NoSQL, embutimos os integrantes diretamente dentro do documento da equipe.
    res_equipes = db.equipes.insert_many(
        [
            {
                "nome_equipe": "Os Autômatos",
                "escola": "Escola Técnica Estadual Porto Digital",
                "cidade": "Recife",
                "integrantes": [
                    {
                        "nome_integrante": "Ana Beatriz Silva",
                        "funcao": "Programadora",
                        "data_nascimento": "2008-03-14",
                    },
                    {
                        "nome_integrante": "Carlos Eduardo Lima",
                        "funcao": "Mecânico",
                        "data_nascimento": "2007-11-02",
                    },
                ],
            },
            {
                "nome_equipe": "Circuito Veloz",
                "escola": "Colégio Municipal Clarice Lispector",
                "cidade": "Olinda",
                "integrantes": [
                    {
                        "nome_integrante": "Mariana Souza",
                        "funcao": "Piloto",
                        "data_nascimento": "2008-07-21",
                    },
                    {
                        "nome_integrante": "João Pedro Alves",
                        "funcao": "Programador",
                        "data_nascimento": "2007-05-30",
                    },
                ],
            },
        ]
    )

    id_automatos = res_equipes.inserted_ids[0]
    id_circuito = res_equipes.inserted_ids[1]
    print(f"Equipes inseridas com sucesso! IDs: {res_equipes.inserted_ids}")

    # Relacionamento 1:N REFERENCE + EMBEDDED:
    # O robô guarda 'equipe_id' (Referência à coleção 'equipes') e
    # embute a lista de 'resultados' das provas disputadas.
    db.robos.insert_many(
        [
            {
                "nome_robo": "Titan",
                "categoria": "Sumô",
                "data_criacao": "2026-02-10",
                "equipe_id": id_automatos,
                "resultados": [
                    {
                        "nome_prova": "Sumô de Robôs",
                        "classificacao": 2,
                        "pontuacao": 90.00,
                    }
                ],
            },
            {
                "nome_robo": "Mamute",
                "categoria": "Sumô",
                "data_criacao": "2026-02-28",
                "equipe_id": id_circuito,
                "resultados": [
                    {
                        "nome_prova": "Sumô de Robôs",
                        "classificacao": 1,
                        "pontuacao": 97.75,
                    }
                ],
            },
            {
                "nome_robo": "Mandacaru",
                "categoria": "Sumô",
                "data_criacao": "2026-04-12",
                "equipe_id": id_automatos,
                "resultados": [],  # Robô ainda sem participações
            },
        ]
    )
    print("Robôs e resultados inseridos com sucesso!")

    print("\n=======================================================")
    print("2. READ — Consultas e Relacionamento ($lookup = JOIN)")
    print("=======================================================")

    # Equivalente ao JOIN entre 'robo' e 'equipe' do MySQL
    pipeline_join = [
        {
            "$lookup": {
                "from": "equipes",
                "localField": "equipe_id",
                "foreignField": "_id",
                "as": "equipe_info",
            }
        },
        {"$unwind": "$equipe_info"},
        {
            "$project": {
                "_id": 0,
                "nome_robo": 1,
                "categoria": 1,
                "equipe": "$equipe_info.nome_equipe",
                "cidade": "$equipe_info.cidade",
                "qtd_resultados": {"$size": "$resultados"},
            }
        },
    ]

    print("-> Robôs vinculados às suas equipes ($lookup):")
    for doc in db.robos.aggregate(pipeline_join):
        pprint(doc)

    # Equivalente à consulta Q2 do SQL (Robôs que ainda não competiram)
    print("\n-> Robôs sem resultados registrados:")
    for doc in db.robos.find({"resultados": {"$size": 0}}, {"_id": 0, "nome_robo": 1, "categoria": 1}):
        pprint(doc)

    print("\n=======================================================")
    print("3. UPDATE — Atualizando campos e arrays ($push / $set)")
    print("=======================================================")

    # Adiciona um resultado ao robô 'Mandacaru' sem precisar alterar outras coleções
    db.robos.update_one(
        {"nome_robo": "Mandacaru"},
        {
            "$push": {
                "resultados": {
                    "nome_prova": "Desafio Nordeste",
                    "classificacao": 1,
                    "pontuacao": 95.50,
                }
            }
        },
    )
    print("Resultado adicionado ao robô Mandacaru!")

    # Adiciona uma nova integrante diretamente no array da equipe 'Os Autômatos'
    db.equipes.update_one(
        {"nome_equipe": "Os Autômatos"},
        {
            "$push": {
                "integrantes": {
                    "nome_integrante": "Danielle Victória",
                    "funcao": "Capitã",
                    "data_nascimento": "2007-11-09",
                }
            }
        },
    )
    print("Nova integrante adicionada à equipe Os Autômatos!")

    print("\n=======================================================")
    print("4. DELETE — Removendo subdocumento ($pull) e documento")
    print("=======================================================")

    # Remove um integrante específico de dentro do documento da equipe
    db.equipes.update_one(
        {"nome_equipe": "Os Autômatos"},
        {"$pull": {"integrantes": {"nome_integrante": "Carlos Eduardo Lima"}}},
    )
    print("Integrante Carlos Eduardo Lima removido do array da equipe.")

    # Remove um documento da coleção de robôs
    db.robos.delete_one({"nome_robo": "Titan"})
    print("Robô Titan removido da coleção 'robos'.")


if __name__ == "__main__":
    try:
        executar_minicurso()
    except Exception as erro:
        print(f"Erro ao executar exemplos NoSQL: {erro}")
        print("Certifique-se de que o servidor MongoDB está rodando em localhost:27017.")