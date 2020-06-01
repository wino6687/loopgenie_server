#import pymongo
import psycopg2
import config
'''
def getTrails(long, lat, rad):
    with pymongo.MongoClient("mongodb://public:public@104.196.106.157:27017/trails?authSource=trails") as client:
        geo = client["trails"]["geo"]
        json = client["trails"]["json"]
        # MongoDB query for nearby trails
        query = { "loc.coordinates": { "$near": { "$geometry": { "type": "Point", "coordinates": [long, lat] }, "$maxDistance": rad }}}
        results = json.find(query)
        toReturn = []
        for trail in results:
            # Put trail metadata and matching geojson data into a tuple and append the list
            try:
                toReturn.append((trail, geo.find({"_id": trail["_id"]})[0]))
            except IndexError as e:
                continue
        return toReturn
'''

def getTrails_sql(long, lat, rad):
    """
    query trails from new postGIS db
    """
    conn = psycopg2.connect(user = config.post_user,
                                    password = config.post_password,
                                    port = '5432',
                                    database = 'trails')
    cursor = conn.cursor()
    select_query = "SELECT name, wkb_geometry FROM geom WHERE ST_DWithin(wkb_geometry, ST_MakePoint({}, {})::geography, {});".format(long, lat, rad)
    cursor.execute(select_query)
    trails = cursor.fetchall()
    return trails
    


