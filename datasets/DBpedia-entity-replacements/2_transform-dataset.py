#!/usr/bin/python3

"""
    get all entities computed by DBpedia Spotlight by and their DBO types 
"""

import json
import sys
from pprint import pprint
from lib import *
import requests
import urllib
import urllib3
import os
from pathlib import Path


smartInputFile="input/smarttask_dbpedia_train.txt"
outdir="output"
cachedir="cached-data/dbpedia-resources"
cachespotlightdir="cached-data/dbpedia-questions-spotlight-annotation"
maxQuestions = 100000
entityCacheFile = outdir+"/entitiesAndTypes.json"
urllib3.disable_warnings()



dataArray = loadData(smartInputFile)

knownEntities = None
try:
    knownEntities = loadData(entityCacheFile)
except:
    pass

if not knownEntities:
    knownEntities = {}

countProcessed = 0
countFoundResources = 0
countResourcesWithoutTypes = 0
countLoadedFromDBpedia = 0
countNoTypeFoundAtDBpedia = 0

for i, data in enumerate(dataArray, start=1):
    if i <= maxQuestions:
        id = data.get("id").encode('utf-8')
        question = data.get("question")

        spotlightDataFile = getFileNameOfCachedWebServiceResponse(cachespotlightdir, id.decode('utf-8'))
        
        # question 7042
        try:
            spotlightData = loadData(spotlightDataFile)
        except:
            continue

        resourcesArray = spotlightData.get("Resources")

        if resourcesArray:
            for resource in resourcesArray:
                countFoundResources += 1
                resourceURI = resource.get("@URI")
                types = resource.get("@types").split(',')

                if not resourceURI in knownEntities:
                    knownEntities[resourceURI] = {}
                    if len(types) == 1 and types[0] == '':
                        types = []
                    knownEntities[resourceURI]["types"] = types
                    knownEntities[resourceURI]["count"] = 1
                else:
                    knownEntities[resourceURI]["count"] = knownEntities[resourceURI]["count"] + 1

                if len(knownEntities[resourceURI]["types"]) == 0:
                    countResourcesWithoutTypes += 1

                    jsonData = getJsonDataFromDBpedia(cachedir, resourceURI)

                    try:
                        rawtypes = jsonData[resourceURI]["http://www.w3.org/1999/02/22-rdf-syntax-ns#type"]
                        types = [ rawtype.get("value").replace("http://dbpedia.org/ontology/", "DBpedia:") for rawtype in rawtypes ]
                        knownEntities[resourceURI]["types"] = types
                    except Exception as e:
                        print(jsonData)
                        print("resource: %s" % (resourceURI,))
                        countNoTypeFoundAtDBpedia += 1
                        

                    countLoadedFromDBpedia += 1


        countProcessed += 1

        # pprint(spotlightData)

        # pprint(resourcesArray)


pprint(knownEntities)

print("entityCacheFile: %s" % (entityCacheFile,))
print("processed files: %d, found resources: %d, unique resources: %d, resource without types: %d, countLoadedFromDBpedia: %d, countNoTypeFoundAtDBpedia: %d" 
        % (countProcessed, countFoundResources, len(knownEntities.keys()), countResourcesWithoutTypes, countLoadedFromDBpedia, countNoTypeFoundAtDBpedia))

saveDataToJsonFile(entityCacheFile, knownEntities)