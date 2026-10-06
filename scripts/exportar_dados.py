import csv
import json
import os
import urllib.parse
import urllib.request


SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]

TABELA = "respostas_pesquisa"

PASTA_SAIDA = "exports"

os.makedirs(PASTA_SAIDA, exist_ok=True)


# ============================================================
# BAIXAR TODAS AS RESPOSTAS
# ============================================================

def buscar_respostas():

    todas = []

    inicio = 0
    tamanho_pagina = 1000

    while True:

        fim = inicio + tamanho_pagina - 1

        url = (
            f"{SUPABASE_URL}/rest/v1/{TABELA}"
            "?select=id,criado_em,escola,trajeto_ida,trajeto_volta"
            "&order=id.asc"
        )

        request = urllib.request.Request(url)

        request.add_header(
            "apikey",
            SUPABASE_SECRET_KEY
        )

        request.add_header(
            "Range",
            f"{inicio}-{fim}"
        )

        request.add_header(
            "Range-Unit",
            "items"
        )

        with urllib.request.urlopen(request) as response:

            pagina = json.loads(
                response.read().decode("utf-8")
            )

        todas.extend(pagina)

        if len(pagina) < tamanho_pagina:
            break

        inicio += tamanho_pagina

    return todas


# ============================================================
# GEOJSON
# ============================================================

def criar_geojson(respostas, campo, sentido):

    features = []

    for resposta in respostas:

        geometria = resposta.get(campo)

        if not geometria:
            continue

        feature = {

            "type": "Feature",

            "geometry": geometria,

            "properties": {

                "id":
                    resposta.get("id"),

                "escola":
                    resposta.get("escola"),

                "criado_em":
                    resposta.get("criado_em"),

                "sentido":
                    sentido

            }

        }

        features.append(feature)

    return {

        "type":
            "FeatureCollection",

        "features":
            features

    }


# ============================================================
# EXECUÇÃO
# ============================================================

respostas = buscar_respostas()


with open(
    f"{PASTA_SAIDA}/respostas.json",
    "w",
    encoding="utf-8"
) as arquivo:

    json.dump(
        respostas,
        arquivo,
        ensure_ascii=False,
        indent=2
    )


geojson_ida = criar_geojson(
    respostas,
    "trajeto_ida",
    "ida"
)


with open(
    f"{PASTA_SAIDA}/trajetos_ida.geojson",
    "w",
    encoding="utf-8"
) as arquivo:

    json.dump(
        geojson_ida,
        arquivo,
        ensure_ascii=False,
        indent=2
    )


geojson_volta = criar_geojson(
    respostas,
    "trajeto_volta",
    "volta"
)


with open(
    f"{PASTA_SAIDA}/trajetos_volta.geojson",
    "w",
    encoding="utf-8"
) as arquivo:

    json.dump(
        geojson_volta,
        arquivo,
        ensure_ascii=False,
        indent=2
    )

# ============================================================
# CSV CONSOLIDADO
# ============================================================

with open(
    f"{PASTA_SAIDA}/respostas.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as arquivo:

    campos = [
        "id",
        "criado_em",
        "escola",
        "trajeto_ida",
        "trajeto_volta"
    ]

    escritor = csv.DictWriter(
        arquivo,
        fieldnames=campos,
        delimiter=";"
    )

    escritor.writeheader()

    for resposta in respostas:

        escritor.writerow({

            "id":
                resposta.get("id"),

            "criado_em":
                resposta.get("criado_em"),

            "escola":
                resposta.get("escola"),

            "trajeto_ida":
                json.dumps(
                    resposta.get("trajeto_ida"),
                    ensure_ascii=False
                ) if resposta.get("trajeto_ida") else "",

            "trajeto_volta":
                json.dumps(
                    resposta.get("trajeto_volta"),
                    ensure_ascii=False
                ) if resposta.get("trajeto_volta") else ""

        })

print(
    f"Exportação concluída: "
    f"{len(respostas)} respostas."
)
