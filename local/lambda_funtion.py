import os
import boto3
import json
import mapper

# mapper runs the entire workflow with mapper.main(location, distance, tripLength)
# Convert optimized network to geojson with trip.save_geosjon(mapper.Path)

def send_to_wh(connection_id, data):
    print("Sending to webhook.")
    endpoint = os.environ['WEBSOCKET_API_ENDPOINT']
    gatewayapi = boto3.client("apigatewaymanagementapi",
                              endpoint_url=endpoint)
    return gatewayapi.post_to_connection(ConnectionId=connection_id,
                                         Data=data.encode('utf-8'))
def lambda_handler(event, context):
    connection_id = event["connectionId"]
    location = event['location']
    distance = int(event['distance'])*1000
    tripLength = int(event['tripLength'])

    trip = mapper.main(location, distance, tripLength)
    json_trip = trip.save_geojson(mapper.Path)
    send_to_wh(connection_id, json_trip)
    
    return {
        'statusCode': 200,
    }
