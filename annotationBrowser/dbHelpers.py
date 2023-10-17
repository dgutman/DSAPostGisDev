import pymongo
from settings import dbConn
from pprint import pprint
import numpy as np
from joblib import Memory
from time import time
from functools import wraps

memory = Memory(".npCacheDir", verbose=0)


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        #        print("func:%r args:[%r, %r] took: %2.4f sec" % (f.__name__, args, kw, te - ts))
        print("func:%r  took: %2.4f sec" % (f.__name__, te - ts))
        return result

    return wrap


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def getAnnotationElementCount(annotationName):
    match_query = {}  ## Currently not filtering on anything..
    # Define the aggregation pipeline
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": "$annotation.name",
                "total": {"$sum": 1},
                "with_elements": {
                    "$sum": {
                        "$cond": [{"$ifNull": ["$annotation.elements", False]}, 1, 0]
                    }
                },
            }
        },
        {
            "$project": {
                "annotationName": "$_id",
                "count": "$total",
                "count_with_elements": "$with_elements",
                "_id": 0,
            }
        },
        {"$sort": {"count": -1}},
    ]

    results = list(dbConn["annotationData"].aggregate(pipeline))
    return results


def insertAnnotationData(annotationItems, debug=False):
    ### This will insert all of the annotations pulled from the DSA and
    #
    operations = []
    for a in annotationItems:
        operations.append(
            pymongo.UpdateOne({"_id": a["_id"]}, {"$set": a}, upsert=True)
        )
    for chunk in chunks(operations, 500):
        result = dbConn["annotationData"].bulk_write(chunk)
        if debug:
            pprint(result.bulk_api_result)
    return result
