# loopgenie_server

This repo contains the server code for LoopGenie. The code is designed to run on AWS Lambda, but it also can be run locally with either command line execution or imported as a module. 

**Note**: To run this code locally, you will need access to certain environment variables for accessing our trail database and geoencoding api. Using our website is free though!


## Installation: 

The LoopGenie server code runs on python 3.6-3.8. There is a conda .yml file and a requirements.txt file to install dependencies with a virtualenv if preferred. 

## Running Locally: 

Until this code is packaged into a proper python library, running it locally simply requires installing the dependencies and importing our ```main.py``` file. 

```{python}
import mapper 

location = "Squaw Valley, CA"
distance, tripLength = 15, 15

network = mapper.main(location, distance, tripLength)

# save optimized network out to a gpx file
mapper.save_gpx(trip, os.getcwd() + "/saved_trips/Squaw_Valley.gpx")

# Get GeoJSON data from optimized network
geojson = trip.save_geojson(mapper.Path)
```

You can either load the geojson output directly into a mapping library or use the automatically save GPX file in the ```/save_trips``` directory. 

## Use Tips

### Location Tips: 

The geocoder we are currently using requires specificity. If you enter a location with multiple matches, we will choose the first result (most likely choice).

If I input ```location="Boulder"```, it will return every matching "Boulder" location: 

Note: This is a shortened result (There are 6 cities matching "Boulder" in the US), we would choose Boulder, CO since it is the more common request. 

```{json}
{
    "items": [
        {
            "title": "Boulder, CO, United States",
            "id": "here:cm:namedplace:21017115",
            "resultType": "locality",
            "localityType": "city",
            "address": {
                "label": "Boulder, CO, United States",
                "countryCode": "USA",
                "countryName": "United States",
                "stateCode": "CO",
                "state": "Colorado",
                "county": "Boulder",
                "city": "Boulder",
                "postalCode": "80302"
            },
            "position": {
                "lat": 40.01574,
                "lng": -105.27924
            },
            "mapView": {
                "west": -105.51671,
                "south": 39.89658,
                "east": -105.131,
                "north": 40.15981
            },
            "scoring": {
                "queryScore": 1,
                "fieldScore": {
                    "city": 1
                }
            }
        },
        {
            "title": "Boulder City, NV, United States",
            "id": "here:cm:namedplace:21010558",
            "resultType": "locality",
            "localityType": "city",
            "address": {
                "label": "Boulder City, NV, United States",
                "countryCode": "USA",
                "countryName": "United States",
                "stateCode": "NV",
                "state": "Nevada",
                "county": "Clark",
                "city": "Boulder City",
                "postalCode": "89005"
            },
            "position": {
                "lat": 35.97861,
                "lng": -114.83404
            },
            "mapView": {
                "west": -115.10262,
                "south": 35.67571,
                "east": -114.76978,
                "north": 36.01118
            },
            "scoring": {
                "queryScore": 1,
                "fieldScore": {
                    "city": 1
                }
            }
        },
        {
            "title": "Boulder, MT, United States",
            "id": "here:cm:namedplace:21040005",
            "resultType": "locality",
            "localityType": "city",
            "address": {
                "label": "Boulder, MT, United States",
                "countryCode": "USA",
                "countryName": "United States",
                "stateCode": "MT",
                "state": "Montana",
                "county": "Jefferson",
                "city": "Boulder",
                "postalCode": "59632"
            },
            "position": {
                "lat": 46.23689,
                "lng": -112.1191
            },
            "mapView": {
                "west": -112.13198,
                "south": 46.22808,
                "east": -112.10726,
                "north": 46.24534
            },
            "scoring": {
                "queryScore": 1,
                "fieldScore": {
                    "city": 1
                }
            }
        }
    ]
}
```

#### Simply including the state solves this issue: ```location = "Boulder, CO"```

```{json}
{
    "items": [
        {
            "title": "Boulder, CO, United States",
            "id": "here:cm:namedplace:21017115",
            "resultType": "locality",
            "localityType": "city",
            "address": {
                "label": "Boulder, CO, United States",
                "countryCode": "USA",
                "countryName": "United States",
                "stateCode": "CO",
                "state": "Colorado",
                "county": "Boulder",
                "city": "Boulder",
                "postalCode": "80302"
            },
            "position": {
                "lat": 40.01574,
                "lng": -105.27924
            },
            "mapView": {
                "west": -105.51671,
                "south": 39.89658,
                "east": -105.131,
                "north": 40.15981
            },
            "scoring": {
                "queryScore": 1,
                "fieldScore": {
                    "state": 1,
                    "city": 1
                }
            }
        }
    ]
}
```