#!/bin/python3
"""[summary]

execute test using:
python3 calculate-intermediate-ranks.py  --test

execure current configuration (see variable 'configurations')
python3 calculate-intermediate-ranks.py
"""


import json
from pprint import pprint, pformat
from collections import Counter
import logging 
import unittest
import argparse


# configure here the files that should be merged

configuration0 = [
    ("faketest_dbpedia_pred_10_unique.json", 0.33),
    ("faketest_dbpedia-ml-maxlen64_pred_unique.json", 0.33),
    ("faketest_dbpedia_pred_unique.json", 0.33)
]

configuration1 = [
    ("faketest_dbpedia_pred_10_unique.json", 0.5),
    ("faketest_dbpedia-ml-maxlen64_pred_unique.json", 0.3),
    ("faketest_dbpedia_pred_unique.json", 0.2)
]

configuration2 = [
    ("faketest_dbpedia_pred_10_unique.json", 0.3),
    ("faketest_dbpedia-ml-maxlen64_pred_unique.json", 0.5),
    ("faketest_dbpedia_pred_unique.json", 0.2)
]

configurations = [configuration0, configuration1, configuration2]
maxQuestions=100000 # reduce for test run purpose
outfilenameprefix = "output_merged_data/merged_predicted_answertypes_of_"


loglevel = logging.INFO
# loglevel = logging.DEBUG

logger = logging.getLogger()
logging.basicConfig(level=loglevel, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
    
    def getWeight(self):
        return self._weight

    def validatePredictedTypes(self):
        for i, data in enumerate(self._dataArray):
            types = data.get("type")
            typesCount = Counter(types)
            typesCountMoreThanOnce = [(type, typesCount[type]) for type in typesCount.keys() if typesCount[type] > 1]
            if len(typesCountMoreThanOnce) > 0:
                logger.warn("data set '%s' for question: '%s' --> predicted types exist more than once: %s" % (self._filename, data.get("id"), typesCountMoreThanOnce))

    def keys(self):
        return [ dataitem.get("id") for dataitem in self._dataArray ] 

    def get(self, key):
        for i,dataitem in enumerate(self._dataArray, start=1):
            if dataitem.get("id") == key:
                return dataitem

    def getRankOfQuestionId(self, questionId, type):
        offset = 2 # TODO: move offset to configuration section
        rankedTypes = self.get(questionId).get("type")
        weight = 1 - self.getWeight() # need to be inverted
        
        rank = 0
        for rank, rankedType in enumerate(rankedTypes, start=1):
            if rankedType == type:
                computedRank = weight * rank
                logger.debug("rank for question '%s', rankedType '%s', rank '%f', weight '%f': %f" % (questionId, rankedType, rank, self._weight, computedRank))
                return computedRank
        
        rank = rank * offset 
        # fallback if type was not found in list of predicted -> TODO: move to configuration
        computedRank = weight * rank
        logger.debug("rank for question '%s', rankedType '%s', rank '%f' (fallback), weight '%f': %f" % (questionId, rankedType, computedRank, self._weight, computedRank))
        return computedRank

    def __str__(self):
        return "file: %s, weight: %f" % (self._filename, self._weight)


def filterTypesOfQuestionId(questionId, dataArrayObjects):
    global logger
    # find categories we will trust
    weightedCategories = {}
    for j, dataArrayObject in enumerate(dataArrayObjects):
        category = dataArrayObject.get(questionId).get("category")
        if not category in weightedCategories:
            weightedCategories[category] = 0
        
        # add weight to category
        weightedCategories[category] += dataArrayObject.getWeight()

    logger.debug("weightedCategories; %s" % weightedCategories)

    # search for category with highest weight
    highestvalue = 0
    mostTrustedCategory = ""
    for category in weightedCategories:
        computedWeight = weightedCategories[category]
        if computedWeight > highestvalue:
            mostTrustedCategory = category
            highestvalue = computedWeight

    logger.info("selected trusted category: %s" % (mostTrustedCategory,))

    allTypesOfQuestionId = []
    for j, dataArrayObject in enumerate(dataArrayObjects):
        category = dataArrayObject.get(questionId).get("category")
        types = dataArrayObject.get(questionId).get("type")

        if category == mostTrustedCategory:
            allTypesOfQuestionId.extend(types)
        else:
            logger.info("passed category %s with types %s" % (category, types))
    
    uniqueTypes = Counter(allTypesOfQuestionId).keys()
    logger.info("compted unique types: %s" % (uniqueTypes,))
    return mostTrustedCategory, uniqueTypes


def computeNewRanks(configuration, maxQuestions):
    ##################################################################
    # init 
    dataArrayObjects = []
    for conf in configuration:
        inputfile = conf[0]
        weight = conf[1]
        dataArrayObjects.append(DataSet(inputfile, weight))
    ##################################################################
    # pprint(dataArrayObjects)

    outputData = []
    questionIds = dataArrayObjects[0].keys()

    countProcessedQuestions = 0

    for i,questionId in enumerate(questionIds, start=1): 
        if i <= maxQuestions:
            countProcessedQuestions += 1
            questionCategory = dataArrayObjects[0].get(questionId).get("category")
            logger.info("%d. question: %s" % (i, questionId))
            
            allTypesOfQuestionId = [] # available types in all input files
            allCategoriesOfQuestionId = [] # available categories, typically there is only 1

            for j, dataArrayObject in enumerate(dataArrayObjects):
                if dataArrayObject.getWeight() > 0: # if weight is 0, then ignore types of the current dataset
                    types = dataArrayObject.get(questionId).get("type")
                    allTypesOfQuestionId.extend(types)
                    category = dataArrayObject.get(questionId).get("category")
                    allCategoriesOfQuestionId.append(category)
            #pprint(allTypesOfQuestionId)
            uniqueTypes = Counter(allTypesOfQuestionId).keys()
            uniqueCategories = Counter(allCategoriesOfQuestionId).keys()
            #pprint(uniqueTypes)

            # we need to filter incompatible types, e.g., a "number" cannot be merged with "resource"
            if len(uniqueCategories) != 1:
                logger.warn("several incompatible categories found for question %s: %s" % (questionId, uniqueCategories))
                questionCategory, uniqueTypes = filterTypesOfQuestionId(questionId, dataArrayObjects)

            allNewlyTypesRank = {}
            for currentType in uniqueTypes:
                rankSum = 0
                #print("currentType: %s" % (currentType,))
                for j, dataArrayObject in enumerate(dataArrayObjects):
                    rankAtCurrentPosition = dataArrayObject.getRankOfQuestionId(questionId, currentType)
                    logger.debug("rankAtCurrentPosition for %s and type '%s': %f" % (questionId, currentType, rankAtCurrentPosition))
                    rankSum += rankAtCurrentPosition
            
                #print("computedRank for questionId '%s' and type '%s': %s" % (questionId, currentType, rankSum))
                allNewlyTypesRank[currentType] = rankSum
            
            logger.debug("allNewlyTypesRank: %s" % (allNewlyTypesRank,))
            allNewlyRankedTypesWithRank = {k: v for k, v in sorted(allNewlyTypesRank.items(), key=lambda item: item[1])}
            logger.debug("allNewlyRankedTypesWithRank: %s" % (allNewlyRankedTypesWithRank,))
            allNewlyRankedTypes = [key for key in allNewlyRankedTypesWithRank]
            logger.debug("new ranking of categories: %s" % allNewlyRankedTypes)
            outputData.append({"id": questionId, "category": questionCategory, "type": allNewlyRankedTypes})
    
    logger.info("questions processed: %d, used data: %s" % (countProcessedQuestions, [i.__str__() for i in dataArrayObjects]))
    return outputData


def main(configuration, maxQuestions, predefinedFilePrefix):
    for configuration in configurations:
        outfilenameprefix = predefinedFilePrefix
        ##################################################################
        for conf in configuration:
            inputfile = conf[0]
            weight = conf[1]
            outfilenameprefix += "__%s_weight%s" % (inputfile, round(weight * 100))
        ##################################################################
        outfilename = outfilenameprefix + '.json'

        outputData = computeNewRanks(configuration, maxQuestions)
        #pprint(outputData)
        saveDataToJsonFile(outfilename, outputData)

        logger.info("output: %s" % (outfilename,))



class TestMergingProcess(unittest.TestCase):
    """
        see always the corresponding files in the directory 'testfiles'    
    """

    def compareWithExtendedFailResponse(self, configuration, computedResult, expectedResult):
        try:
            self.assertEquals(expectedResult, computedResult, "failed for for given configuration: %s" % (configuration,))
        except AssertionError as e:
            for filename, weight in configuration:
                print("### input: %s (weight: %f)" % (filename,weight))
                pprint(loadData(filename))
            print("### computed result:")
            pprint(computedResult)
            print("### expected result:")
            pprint(expectedResult)
            raise e

    def checkResults(self, configuration, expectedDatafile):
        computedResult = computeNewRanks(configuration, 1)
        expectedResult = loadData(expectedDatafile)
        self.compareWithExtendedFailResponse(configuration, computedResult, expectedResult)

    # @unittest.skip
    def test_boolean_boolean(self):
        testfile1 = "testfiles/boolean1.json"
        testfile2 = "testfiles/boolean1.json"
        expectedDatafile = "testfiles/boolean1.json"
        configuration = [
            (testfile1, 0.5),
            (testfile2, 0.5)
        ]
        self.checkResults(configuration, expectedDatafile)

    # @unittest.skip
    def test_boolean_literal(self):
        testfile1 = "testfiles/boolean1.json"
        testfile2 = "testfiles/string1.json"
        expectedDatafile = "testfiles/boolean1.json"
        configuration = [
            (testfile1, 0.51),
            (testfile2, 0.49)
        ]
        self.checkResults(configuration, expectedDatafile)

    # @unittest.skip
    def test_boolean_resource_boolean_wins(self):
        testfile1 = "testfiles/boolean1.json"
        testfile2 = "testfiles/resource1.json"
        expectedDatafile = "testfiles/boolean1.json"
        configuration = [
            (testfile1, 0.51),
            (testfile2, 0.49)
        ]
        self.checkResults(configuration, expectedDatafile)

    # @unittest.skip
    def test_boolean_resource_resource_wins(self):
        testfile1 = "testfiles/boolean1.json"
        testfile2 = "testfiles/resource1.json"
        expectedDatafile = "testfiles/resource1.json"
        configuration = [
            (testfile1, 0.49),
            (testfile2, 0.51)
        ]
        self.checkResults(configuration, expectedDatafile)

    # @unittest.skip
    def test_resource_resource_1(self):
        testfile1 = "testfiles/resource1.json"
        testfile2 = "testfiles/resource2.json"
        expectedDatafile = "testfiles/resource1.json"
        # the result has to be the same despite the weight
        for i in range(0, 10):
            configuration = [
                (testfile1, i / 10),
                (testfile2, 1 - i / 10)
            ]
        self.checkResults(configuration, expectedDatafile)

    # @unittest.skip
    def test_resource_resource_2(self):
        testfile1 = "testfiles/resource2.json"
        testfile2 = "testfiles/resource3.json"
        expectedDatafile0 = "testfiles/resource3.json"
        expectedDatafile1 = "testfiles/resource1.json"
        expectedDatafile2 = "testfiles/resource6.json"
        expectedDatafile3 = "testfiles/resource2.json"

        # the result has to be the same despite the weight
        for i in range(0, 11):
            logger.debug("--------------------- %d" % i)
            weight1 = i / 10
            weight2 = 1 - i / 10
            configuration = [
                (testfile1, weight1),
                (testfile2, weight2)
            ]

            computedResult = computeNewRanks(configuration, 1)
            if i == 0:
                expectedResult = loadData(expectedDatafile0)
            elif i <= 5:
                expectedResult = loadData(expectedDatafile1)
            elif i < 10:
                expectedResult = loadData(expectedDatafile2)
            else:
                expectedResult = loadData(expectedDatafile3)

            self.compareWithExtendedFailResponse(configuration, expectedResult, computedResult)

    # @unittest.skip
    def test_resource_resource_3(self):
        testfile1 = "testfiles/resource1.json"
        testfile2 = "testfiles/resource4.json"
        expectedDatafile = "testfiles/resource5.json"
        weight1 = 0.5
        weight2 = 0.5
        configuration = [
            (testfile1, weight1),
            (testfile2, weight2)
        ]
        self.checkResults(configuration, expectedDatafile)

    # @unittest.skip
    def test_resource_resource_4(self):
        testfile1 = "testfiles/resource4.json"
        testfile2 = "testfiles/resource5.json"
        expectedDatafile1 = "testfiles/resource4.json"
        expectedDatafile2 = "testfiles/resource5.json"

        # the result has to be the same despite the weight
        for i in range(0, 11):
            weight1 = i / 10
            weight2 = 1 - i / 10
            configuration = [
                (testfile1, weight1),
                (testfile2, weight2)
            ]

            computedResult = computeNewRanks(configuration, 1)
            if i <= 5:
                expectedResult = loadData(expectedDatafile1)
            else:
                expectedResult = loadData(expectedDatafile2)

            self.compareWithExtendedFailResponse(configuration, expectedResult, computedResult)




# start
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='for tests use: -t or --test')
    parser.add_argument('-t', '--test', action='store_true', 
                        help='if given, just the unittests are executed, other parameters are ignored')
    args = parser.parse_args()

    if args.test:
        # python3 connectfour.py --test
        suite = unittest.TestLoader().loadTestsFromTestCase(TestMergingProcess)
        unittest.TextTestRunner().run(suite)
    else:
        main(configurations, maxQuestions, outfilenameprefix)
