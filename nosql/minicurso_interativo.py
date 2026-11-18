"""Minicurso interativo MongoDB + PyMongo — Torneio de Robótica (IAAD).

Versão de apresentação baseada em nosql/nosql_exemplos.py.
Usa um banco exclusivo de demonstração e não apaga coleções inteiras.
"""

import os
import uuid
from pprint import pprint

from pymongo import MongoClient
from pymongo.errors import PyMongoError


BANCO_DEMO = "torneio_robotica_nosql_apresentacao"


def conectar_mongodb():
    uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
    cliente = MongoClient(uri, serverSelectionTimeoutMS=5000)
    cliente.admin.command("ping")  # Confirma que o servidor responde.
    return cliente, cliente[BANCO_DEMO]


def titulo(texto):
    print("\n" + "=" * 65)
    print(texto)
    print("=" * 65)


def pausa(mensagem):
    input(f"\n[PAUSA] {mensagem}\nPressione ENTER para continuar...")


def mostrar_documento(rotulo, documento):
    print(f"\n{rotulo}")
    pprint(documento, sort_dicts=False)


def executar_minicurso():
    cliente, db = conectar_mongodb()
    execucao_id = uuid.uuid4().hex[:8]

    try:
        titulo("MINICURSO IAAD — MONGODB + PYMONGO")
        print(f"Banco exclusivo desta demonstração: {BANCO_DEMO}")
        print(f"Identificador desta execução: {execucao_id}")
        print("Abra o MongoDB Compass em mongodb://127.0.0.1:27017")
        print(f"Abra o banco {BANCO_DEMO} quando ele aparecer.")
        print("Cada execução cria novos registros de exemplo; nenhuma coleção é apagada.")

        pausa("Vamos criar as equipes, os integrantes e os robôs.")

        # ETAPA 1 — CREATE
        titulo("1. CREATE — Documentos embutidos e referências")
        res_equipes = db.equipes.insert_many(
            [
                {
                    "execucao_id": execucao_id,
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
                    "execucao_id": execucao_id,
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
        id_automatos, id_circuito = res_equipes.inserted_ids

        res_robos = db.robos.insert_many(
            [
                {
                    "execucao_id": execucao_id,
                    "nome_robo": "Titan",
                    "categoria": "Sumô",
                    "data_criacao": "2026-02-10",
                    "equipe_id": id_automatos,
                    "resultados": [
                        {
                            "nome_prova": "Sumô de Robôs",
                            "classificacao": 2,
                            "pontuacao": 90.0,
                        }
                    ],
                },
                {
                    "execucao_id": execucao_id,
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
                    "execucao_id": execucao_id,
                    "nome_robo": "Mandacaru",
                    "categoria": "Sumô",
                    "data_criacao": "2026-04-12",
                    "equipe_id": id_automatos,
                    "resultados": [],
                },
            ]
        )
        id_titan, _, id_mandacaru = res_robos.inserted_ids

        print("\nCREATE confirmado: 2 equipes e 3 robôs cadastrados.")
        mostrar_documento(
            "Equipe com integrantes incorporados:",
            db.equipes.find_one({"_id": id_automatos}, {"_id": 0, "nome_equipe": 1, "integrantes": 1}),
        )
        print("No Compass, veja as coleções 'equipes' e 'robos'.")
        print(f"Filtro opcional no Compass: {{\"execucao_id\": \"{execucao_id}\"}}")

        pausa("Confira os documentos no Compass. Agora vamos fazer consultas.")

        # ETAPA 2 — READ
        titulo("2. READ — Consultas e relacionamento com $lookup")
        pipeline_join = [
            {"$match": {"execucao_id": execucao_id}},
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
        print("\nRobôs associados às equipes ($lookup):")
        for documento in db.robos.aggregate(pipeline_join):
            pprint(documento, sort_dicts=False)

        print("\nRobôs sem resultados:")
        for documento in db.robos.find(
            {"execucao_id": execucao_id, "resultados": {"$size": 0}},
            {"_id": 0, "nome_robo": 1, "categoria": 1},
        ):
            pprint(documento, sort_dicts=False)

        pausa("Observe que Mandacaru ainda não tem resultados. Vamos atualizar.")

        # ETAPA 3 — UPDATE
        titulo("3. UPDATE — $push para arrays e $set para campos")
        resultado = db.robos.update_one(
            {"_id": id_mandacaru},
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
        print(f"Resultado do Mandacaru incluído? {resultado.modified_count == 1}")

        resultado = db.equipes.update_one(
            {"_id": id_automatos},
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
        print(f"Danielle incluída na equipe? {resultado.modified_count == 1}")

        resultado = db.equipes.update_one(
            {"_id": id_circuito}, {"$set": {"cidade": "Paulista"}}
        )
        print(f"Cidade de Circuito Veloz alterada com $set? {resultado.modified_count == 1}")

        mostrar_documento(
            "Mandacaru depois do $push:",
            db.robos.find_one({"_id": id_mandacaru}, {"_id": 0, "nome_robo": 1, "resultados": 1}),
        )
        mostrar_documento(
            "Os Autômatos depois do $push:",
            db.equipes.find_one({"_id": id_automatos}, {"_id": 0, "nome_equipe": 1, "integrantes": 1}),
        )
        mostrar_documento(
            "Circuito Veloz depois do $set:",
            db.equipes.find_one({"_id": id_circuito}, {"_id": 0, "nome_equipe": 1, "cidade": 1}),
        )

        pausa("Confira as mudanças no Compass. Agora vamos excluir dados.")

        # ETAPA 4 — DELETE
        titulo("4. DELETE — $pull em arrays e delete_one em documentos")
        resultado = db.equipes.update_one(
            {"_id": id_automatos},
            {"$pull": {"integrantes": {"nome_integrante": "Carlos Eduardo Lima"}}},
        )
        print(f"Carlos removido do array? {resultado.modified_count == 1}")

        resultado = db.robos.delete_one({"_id": id_titan})
        print(f"Documento Titan excluído? {resultado.deleted_count == 1}")

        mostrar_documento(
            "Integrantes restantes de Os Autômatos:",
            db.equipes.find_one({"_id": id_automatos}, {"_id": 0, "nome_equipe": 1, "integrantes": 1}),
        )
        print(f"Titan ainda existe? {db.robos.find_one({'_id': id_titan}) is not None}")
        print(f"Equipes desta execução: {db.equipes.count_documents({'execucao_id': execucao_id})}")
        print(f"Robôs desta execução: {db.robos.count_documents({'execucao_id': execucao_id})}")

        titulo("FIM — CREATE, READ, UPDATE e DELETE demonstrados")
        print("No Compass, atualize a visualização para conferir os dados finais.")
        print("Observação: equipe_id é uma referência; não é uma FK automática do MySQL.")
        pausa("Apresentação finalizada. Os documentos restantes ficam salvos para consulta.")

    finally:
        cliente.close()


if __name__ == "__main__":
    try:
        executar_minicurso()
    except (PyMongoError, OSError) as erro:
        print(f"\nErro ao acessar o MongoDB: {erro}")
        print("Verifique se o serviço MongoDB está ativo em localhost:27017.")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nApresentação interrompida pelo usuário.")
