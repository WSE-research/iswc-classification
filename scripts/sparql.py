from SPARQLWrapper import SPARQLWrapper, JSON


def get_hierarchy(ontology_type):
    query = f"""
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT DISTINCT ?parentClass WHERE {{
          {ontology_type} rdfs:subClassOf* ?parentClass .
          FILTER(?parentClass != {ontology_type} && CONTAINS(STR(?parentClass), 'dbpedia'))
        }}  
    """
    hierarchy = [ontology_type]

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        hierarchy.append(result["parentClass"]["value"].replace("http://dbpedia.org/ontology/", "dbo:"))
        
    return hierarchy