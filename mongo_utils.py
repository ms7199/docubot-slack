import json
from datetime import datetime
from typing import Any
from pymongo import MongoClient
import os

client = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017"))
db = client["salesInfo"]

def run_mongo_query(raw: str):
    try:
        q = json.loads(raw)
        if "aggregate" in q:
            cursor = db[q["aggregate"]].aggregate(q["pipeline"])
        elif "find" in q:
            cursor = db[q["find"]].find(q.get("filter", {}))
        else:
            return {"error": "Invalid query format"}

        results = []
        for doc in cursor:
            clean = {}
            for k,v in doc.items():
                if isinstance(v, datetime):
                    clean[k] = v.isoformat()
                elif k == "_id":
                    clean[k] = str(v)
                else:
                    clean[k] = v
            results.append(clean)
        return results if results else "No results found."
    except Exception as e:
        return {"error": str(e)}
