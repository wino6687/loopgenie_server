import psycopg2
import logging
import sys

def getTrails(long, lat, rad, secrets):
    """
    query trails from new postGIS db
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    try:
        conn = psycopg2.connect(user = secrets['POST_USER'],
                                        password = secrets['POST_PASSWORD'],
                                        port = '5432',
                                        database = 'trails',
                                        host= 'trails.ctluwc1bi2yb.us-east-2.rds.amazonaws.com')
    except:
        logger.error("ERROR: Could not connect to Postgres instance.")
        sys.exit()

    logger.info("SUCCESS: Connection to RDS Postgres instance succeeded.")

    select_query = "SELECT name, wkb_geometry FROM geom WHERE ST_DWithin(wkb_geometry, ST_MakePoint({}, {})::geography, {});".format(long, lat, rad)
    
    with conn.cursor() as cur:
        cur.execute(select_query)
        trails = cur.fetchall()
    return trails
    


