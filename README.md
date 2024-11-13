# Itinerary Planner Webapp
Displays Weather, restauants and attractions of a location of your choosing in a flask based WebApp. You can launch it on your system or pull the docker container.

# Usage:
Run the following command:
docker run -d -p 5000:5000 --volume $(pwd):/temp --name test rexanator96/team6_itinerarywebapp:latest
Put your API keys in a .env file in your current working directory.
