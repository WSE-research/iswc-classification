import json
import urllib
import os
from pathlib import Path
import requests


def loadData(filename):
    with open(filename, 'r') as f:
        return json.load(f)
    return None

def getFileNameOfCachedWebServiceResponse(dir, id):
    return("%s/%s.json" % (dir, id))

def saveDataToJsonFile(filename, jsonData):
    with open(filename, 'w') as f:
        f.write(json.dumps(jsonData, indent=4))
        f.close()

def getJsonDataFromDBpedia(cachedir, resourceURI):
    name = resourceURI.replace("http://dbpedia.org/resource/", "")
    url = "http://dbpedia.org/data/" + urllib.parse.quote(name) + ".json"
    
    filename = cachedir + "/" + name.replace('/','_') + ".json"

    if os.path.isfile(filename) and Path(filename).stat().st_size > 0:
        jsonData = loadData(filename)
    else:
        request = requests.get(url, verify=False)
        try:
            jsonData = request.json()
            saveDataToJsonFile(filename, jsonData)
        except Exception as e:
            print("resourceURI: %s, url: %s" % (resourceURI, url))
            print(request.text)
            raise(e)


    return jsonData

