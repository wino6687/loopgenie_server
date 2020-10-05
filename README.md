# loopgenie_server

This repo contains loopgenie code for three different platforms: 

- local
  - To be run on your own machine. Requires a config file with the needed access information to our PostGIS RDS database and our geolocater api. 

- lambda 
  - Production code that runs in our lambda function to support the website. 

- api 
  - Flask application version that is no longer in use. This is how we initially hosted the server code, but found lambda to be more cost efficient. 
