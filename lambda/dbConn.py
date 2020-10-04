import psycopg2
import os


def getTrails_sql(long, lat, rad):
    """
    query trails from new postGIS db
    """
    conn = psycopg2.connect(user = os.environ['POST_USER'],
                                    password = os.environ['POST_PASSWORD'],
                                    port = '5432',
                                    database = 'trails',
                                    host= 'trails.ctluwc1bi2yb.us-east-2.rds.amazonaws.com')
    cursor = conn.cursor()
    select_query = "SELECT name, wkb_geometry FROM geom WHERE ST_DWithin(wkb_geometry, ST_MakePoint({}, {})::geography, {});".format(long, lat, rad)
    cursor.execute(select_query)
    trails = cursor.fetchall()
    return trails