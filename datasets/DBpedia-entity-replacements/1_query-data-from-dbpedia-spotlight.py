#!/usr/bin/python3

import json
import urllib.request
from urllib.parse import urlencode, quote_plus
import sys
import os
from pprint import pprint
import requests
from pathlib import Path
import time
import urllib3
from lib import *

"""
    for each question fetch the annotations computed by DBpedia Spotlight 
    store them in a local cache: constant "outdir"
"""

smartInputFile="input/smarttask_dbpedia_train.txt"
outdir="output"
cachedir="cached-data/dbpedia-questions-spotlight-annotation"
maxQuestions = 100000

urllib3.disable_warnings() # deactivate warnings

def getAnnotationUrl(question):
    return("https://api.dbpedia-spotlight.org/en/annotate?text=%s" % (urllib.parse.quote(question),))

def fetchDataViaGET(url):
    headers = {'accept': 'application/json'}
    return requests.get(url, headers=headers, verify=False)



dataArray = loadData(smartInputFile)

countOk = 0
countFail = 0
countCached = 0
for i, data in enumerate(dataArray, start=1):
    id = data.get("id").encode('utf-8')
    question = data.get("question")
    outfile = getFileNameOfCachedWebServiceResponse(cachedir, id.decode('utf-8'))

    # problem with id: dbpedia_7042
    if question:
        question = question.encode('utf-8')
    else:
        continue
    
    print("%5d / %5d: %15s :: %s" % (i, len(dataArray), id.decode("utf-8"), question.decode("utf-8")))

    url = getAnnotationUrl(question)
    print("\t%s" % (url,))

    if os.path.isfile(outfile) and Path(outfile).stat().st_size > 0: # skip web service request if file already exists
        print("\tfile exists already: %s" % (outfile,))
        countCached += 1
        continue
    else:
        response = fetchDataViaGET(url)
        #pprint(dir(response))
        try:
            jsonData = response.json()
            with open(outfile, 'w') as f:
                f.write(json.dumps(jsonData, indent=4))
                f.close()
                countOk += 1
        except Exception as e:
            print(e)
            pprint(response.text)
            countFail += 1
        time.sleep(1) 

    if i == maxQuestions:
        sys.exit(1)

print("cached: %d, fetched ok: %d, failed: %s" % (countCached, countOk,countFail))
