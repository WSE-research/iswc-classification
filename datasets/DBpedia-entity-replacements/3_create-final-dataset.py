import json
import sys
from pprint import pprint
from lib import *
import requests
import urllib3
import os
from pathlib import Path
from copy import copy

""" 
    take pre-computed data and create new SMART dataset
"""

smartInputFile="input/smarttask_dbpedia_train.txt"
outdir="output"
outfile=outdir+"/smarttask_dbpedia_train---types-added.txt"
entityCacheFile = outdir+"/entitiesAndTypes.json"
cacheresourcesdir="cached-data/dbpedia-resources"
cachespotlightdir="cached-data/dbpedia-questions-spotlight-annotation"
maxQuestions = 100000
questionsToBeSkipped = ["dbpedia_4857"]
urllib3.disable_warnings()



dataArray = loadData(smartInputFile)

knownEntities = None
knownEntities = loadData(entityCacheFile)

newDataArray = []

for i, data in enumerate(dataArray, start=1):
    if i <= maxQuestions:
        id = data.get("id").encode('utf-8')
        question = data.get("question")
        newquestions = []
        

        pprint((i, id, question), width=250)

        # questions that seems to be broken will not be transformed
        if id.decode('utf-8') in questionsToBeSkipped:
            newquestions = [question] 
            print("%s skipped" % (id,))
        else:
            filenameSpotlight = getFileNameOfCachedWebServiceResponse(cachespotlightdir, id.decode('utf-8'))

            # questions like dbpedia_7042
            try:
                spotlightData = loadData(filenameSpotlight)
            except:
                continue

            resourcesArray = spotlightData.get("Resources", [])
            resourcesArray.reverse() # required for correct replacements in question

            # pprint(spotlightData)
            allcurrentquestions = [question]

            if resourcesArray:
                for j,resource in enumerate(resourcesArray, start=1):
                    resourceURI = resource.get("@URI")
                    startposition = int(resource.get("@offset"))
                    endposition = len(resource.get("@surfaceForm")) + startposition

                    types = knownEntities[resourceURI].get("types")
                    dbotypes = [ type for type in types if type.startswith("DBpedia") ]
                    # pprint((j, dbotypes))

                    # do nothing if no DBO type is available (kept current question untouched)
                    if len(dbotypes) == 0:
                        continue

                    changedquestions = []
                    for currentquestion in allcurrentquestions:
                        firstpart = currentquestion[0:startposition]
                        lastpart = currentquestion[endposition:]

                        for dbotype in dbotypes:
                            changedquestion = firstpart + dbotype + lastpart
                            changedquestions.append(changedquestion)

                    # replace original questions 
                    allcurrentquestions = changedquestions

                pprint(allcurrentquestions, width=250)
                assert(len(allcurrentquestions) > 0), "for question '%s' no question are available (should be at least the original surface form)" % (question,)
                newquestions.extend(allcurrentquestions)


        for number, newquestion in enumerate(newquestions, start=0):
            # pprint((question, newquestion), width=120)
            newdata = copy(data)
            newdata["id"] = "%s-%03d" % (newdata["id"], number)
            newdata["question"] = newquestion
            newdata["originalquestion"] = question
            newDataArray.append(newdata)
            
print("%d abstracted questions generated from given %d questions in the original data set (process was limited to first %d questions)." % (len(newDataArray), len(dataArray), maxQuestions))
saveDataToJsonFile(outfile, newDataArray)
