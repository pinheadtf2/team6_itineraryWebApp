from os import getenv
from urllib import request

import aiohttp
from dotenv import load_dotenv
from quart import Quart, session, redirect, request, url_for, render_template

app = Quart(__name__)
# required to have this, so you get to deal with it now too
app.secret_key = "sigma sigma on the wall, who is the skibidiest of them all"

load_dotenv()
weather_key = getenv("WEATHERAPI_KEY")
google_places_key = getenv("GOOGLE_PLACES_KEY")


class LocationNotFound(Exception):
    pass


class UnknownError(Exception):
    pass


async def get_weather(client_session: aiohttp.ClientSession, location: str):
    async with client_session.get('https://api.weatherapi.com/v1/forecast.json',
                                  params={"key": weather_key,
                                          "q": location
                                          }) as response:
        if response.status != 200:
            error = await response.json()
            if error["error"]["code"] == 1006:
                raise LocationNotFound("The location entered wasn't found. Please enter a valid location.")
            raise UnknownError(
                f"Something went wrong when getting the weather!\n"
                f"  |->  Status: {response.status}\n"
                f"  |->  Headers: {response.headers}\n"
                f"  |->  Response: {await response.json()}\n")
        return await response.json()


async def get_attractions(client_session: aiohttp.ClientSession, latitude, longitude, radius=1000):
    async with client_session.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json',
                                  params={
                                      'location': f"{latitude},{longitude}",
                                      'radius': radius,
                                      'type': 'tourist_attraction',
                                      "key": google_places_key
                                  }) as response:
        return await response.json()


@app.route("/itinerary")
async def itinerary():
    if 'location' in session and 'radius' in session:
        location = session['location']
        radius = session['radius']
        try:
            async with aiohttp.ClientSession() as client_session:
                weather = await get_weather(client_session, location)
                latitude, longitude = weather["location"]["lat"], weather["location"]["lon"]
                attractions = await get_attractions(client_session, latitude, longitude)
                print(attractions)
            return await render_template("/itinerary/index.html", weather=weather, attractions=attractions)
        except Exception as error:
            session['error'] = f"{error.__class__.__name__}: {str(error)}"
            return redirect(url_for('index'))
    else:
        return redirect(url_for("index"))


@app.route("/", methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        form = await request.form
        session['location'] = form['location']
        session['radius'] = form['radius']
        return redirect(url_for('itinerary'))

    error = session.pop('error', "").split('\n')
    return await render_template("index.html", error=error)


if __name__ == "__main__":
    app.run()
