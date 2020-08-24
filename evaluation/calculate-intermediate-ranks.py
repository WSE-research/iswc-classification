#!/bin/python3

import json
from pprint import pprint 
from collections import Counter
import logging 


# configure here the files that should be merged

configuration0 = [
    ("faketest_dbpedia_pred_8.json", 0.5),
    ("faketest_dbpedia_pred_10.json", 0.5)
]

configuration1 = [
    ("faketest_dbpedia_pred_8.json", 0.33),
    ("faketest_dbpedia_pred_10.json", 0.67)
]

configuration2 = [
    ("faketest_dbpedia_pred_8.json", 0.67),
    ("faketest_dbpedia_pred_10.json", 0.33)
]

configurations = [configuration0, configuration1, configuration2]
maxQuestions=100000 # reduce for test run purpose
outfilenameprefix = "output_merged_data/merged_predicted_answertypes_of_"




logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def loadData(filename):
    with open(filename, 'r') as f:
        return json.load(f)
    return None

def saveDataToJsonFile(filename, jsonData):
    with open(filename, 'w') as f:
        f.write(json.dumps(jsonData, indent=4))
        f.close()

class DataSet(object):
    def __init__(self, filename, weight):
        super().__init__()
        self._filename = filename
        self._weight = weight
        self._dataArray = loadData(filename)
        self.validatePredictedTypes()

    def validatePredictedTypes(self):
        for i, data in enumerate(self._dataArray):
            types = data.get("type")
            typesCount = Counter(types)
            typesCountMoreThanOnce = [(type, typesCount[type]) for type in typesCount.keys() if typesCount[type] > 1]
            if len(typesCountMoreThanOnce) > 0:
                logger.warn("WARNING: data set '%s' for question: '%s' --> predicted types exist more than once: %s" % (self._filename, data.get("id"), typesCountMoreThanOnce))

    def keys(self):
        return [ dataitem.get("id") for dataitem in self._dataArray ] 

    def get(self, key):
        for i,dataitem in enumerate(self._dataArray, start=1):
            if dataitem.get("id") == key:
                return dataitem

    def getRankOfQuestionId(self, questionId, type):
        predefinedRank = 10 # fallback if type was not found in list of predicted -> TODO: move to configuration
        rankedTypes = self.get(questionId).get("type")
        for rank, rankedType in enumerate(rankedTypes, start=1):
            if rankedType == type:
                return self._weight * rank
        return self._weight * predefinedRank

    def __str__(self):
        return "file: %s, weight: %f" % (self._filename, self._weight)


def computeNewRanks(configuration, maxQuestions, outfilenameprefix):
    ##################################################################
    # init 
    dataArrayObjects = []
    for conf in configuration:
        inputfile = conf[0]
        weight = conf[1]
        dataArrayObjects.append(DataSet(inputfile, weight))
        outfilenameprefix += "__%s_weight%s" % (inputfile, round(weight * 100))
    ##################################################################
    outfilename = outfilenameprefix + '.json'


    outputData = []

    # pprint(dataArrayObjects)
    questionIds = dataArrayObjects[0].keys()

    countProcessedQuestions = 0

    for i,questionId in enumerate(questionIds, start=1): 
        if i <= maxQuestions:
            countProcessedQuestions += 1
            questionCategory = dataArrayObjects[0].get(questionId).get("category")
            pprint((i, questionId))
            allTypesOfQuestionId = []
            for j, dataArrayObject in enumerate(dataArrayObjects):
                types = dataArrayObject.get(questionId).get("type")
                allTypesOfQuestionId.extend(types)
            #pprint(allTypesOfQuestionId)
            uniqueTypes = Counter(allTypesOfQuestionId).keys()
            #pprint(uniqueTypes)

            allNewlyTypesRank = {}
            for currentType in uniqueTypes:
                rankSum = 0
                #print("currentType: %s" % (currentType,))
                for j, dataArrayObject in enumerate(dataArrayObjects):
                    rankSum += dataArrayObject.getRankOfQuestionId(questionId, currentType)
            
                #print("computedRank for questionId '%s' and type '%s': %s" % (questionId, currentType, rankSum))
                allNewlyTypesRank[currentType] = rankSum
            allNewlyRankedTypesWithRank = sorted(allNewlyTypesRank.items(), reverse=True)
            allNewlyRankedTypes = [i[0] for i in allNewlyRankedTypesWithRank]
            pprint(("new rank of categories: ",allNewlyRankedTypes))
            outputData.append({"id": questionId, "category": questionCategory, "type": allNewlyRankedTypes})

    #pprint(outputData)
    saveDataToJsonFile(outfilename, outputData)

    print("output: %s" % (outfilename,))
    print("questions processed: %d, used data: %s" % (countProcessedQuestions, [i.__str__() for i in dataArrayObjects]))




# start
for configuration in configurations:
    computeNewRanks(configuration, maxQuestions, outfilenameprefix)
