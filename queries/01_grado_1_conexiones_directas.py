# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 15:18:15 2025

@author: jvera
"""

import sys
import json
import os
from datetime import datetime
from SPARQLWrapper import SPARQLWrapper, JSON

endpoint_url = "https://query.wikidata.org/sparql"

query = """#title: Grado 2 - Conexiones expandidas (sin labels problemáticos)
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT ?dimension ?propiedadGrado1 ?entidadIntermedia ?propiedadGrado2 ?entidadGrado2
WHERE {
  # Usar las mismas propiedades del Grado 1
  VALUES (?dimension ?propiedadGrado1) {
    ("Identidad" wdt:P31)
    ("Identidad" wdt:P17)
    ("Identidad" wdt:P495)
    ("Geográfica" wdt:P131)
    ("Geográfica" wdt:P276)
    ("Geográfica" wdt:P625)
    ("Temporal" wdt:P580)
    ("Temporal" wdt:P582)
    ("Temporal" wdt:P585)
    ("Cultural" wdt:P135)
    ("Cultural" wdt:P361)
    ("Cultural" wdt:P921)
    ("Digital" wdt:P18)
    ("Digital" wdt:P373)
    ("Digital" wdt:P1617)
    ("Social" wdt:P112)
    ("Social" wdt:P710)
    ("Patrimonio" wdt:P1435)
    ("Patrimonio" wdt:P6104)
  }
  
  # Grado 1: Qoyllur Rit'i -> Entidad Intermedia
  wd:Q2408955 ?propiedadGrado1 ?entidadIntermedia.
  FILTER(STRSTARTS(STR(?entidadIntermedia), "http://www.wikidata.org/entity/"))
  
  # Grado 2: Entidad Intermedia -> Entidad Grado 2
  ?entidadIntermedia ?propiedadGrado2 ?entidadGrado2.
  FILTER(STRSTARTS(STR(?propiedadGrado2), "http://www.wikidata.org/prop/direct/"))
  FILTER(STRSTARTS(STR(?entidadGrado2), "http://www.wikidata.org/entity/"))
}
ORDER BY ?dimension ?propiedadGrado1
LIMIT 50"""


def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


results = get_results(endpoint_url, query)

# Estructurar datos para JSON
output_data = {
    "metadata": {
        "query_executed": query,
        "execution_date": datetime.now().isoformat(),
        "endpoint": endpoint_url,
        "total_results": len(results["results"]["bindings"])
    },
    "results": []
}

for result in results["results"]["bindings"]:
    processed_result = {}
    for key, value in result.items():
        processed_result[key] = value["value"]
        
        # Extraer IDs cortos para mejor legibilidad
        if "wikidata.org" in value["value"]:
            if "/entity/Q" in value["value"]:
                processed_result[f"{key}_short"] = value["value"].split("/entity/Q")[1].split("/")[0]
                processed_result[f"{key}_short"] = "Q" + processed_result[f"{key}_short"]
            elif "/prop/direct/P" in value["value"]:
                processed_result[f"{key}_short"] = value["value"].split("/prop/direct/P")[1].split("/")[0]
                processed_result[f"{key}_short"] = "P" + processed_result[f"{key}_short"]
    
    output_data["results"].append(processed_result)

# Crear directorio si no existe
os.makedirs("resultados_queries", exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = os.path.join("resultados_queries", f"qoyllur_riti_grado2_{timestamp}.json")

with open(filename, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Resultados guardados en: {filename}")
print(f"Total de registros: {len(output_data['results'])}")

# Mostrar preview en consola
print("\nPreview de los primeros 2 resultados:")
for i, result in enumerate(output_data["results"][:2]):
    print(f"\n{i+1}. {result}")