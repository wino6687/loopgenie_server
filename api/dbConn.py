#import pymongo
import psycopg2
import config


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
    


