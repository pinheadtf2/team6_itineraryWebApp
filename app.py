import subprocess
import traceback
from os import getenv
from urllib import request

import aiohttp
from dotenv import load_dotenv
from quart import Quart, session, redirect, request, url_for, render_template

app = Quart(__name__)
# required to have this, so you get to deal with it now too
app.secret_key = "sigma sigma on the wall, who is the skibidiest of them all"

subprocess.run(['cp', 'temp/.env', '/team6_itinerarywebapp/.env'])

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
                                          "q": location,
                                          "days": 1
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
        weather = await response.json()
        rain_chance = weather["forecast"]["forecastday"][0]["day"]["daily_chance_of_rain"]
        snow_chance = weather["forecast"]["forecastday"][0]["day"]["daily_chance_of_snow"]
        direction = weather["current"]["wind_degree"]

        precipitation = {
            "chance": rain_chance,
            "type": "Rain"
        }

        if snow_chance > rain_chance:
            precipitation["chance"] = snow_chance
            precipitation["type"] = "Snow"

        if 337 < direction < 22:
            weather["current"]["wind_arrow"] = "↑"
        elif 292 < direction <= 337:
            weather["current"]["wind_arrow"] = "↖"
        elif 247 < direction <= 292:
            weather["current"]["wind_arrow"] = "←"
        elif 202 < direction <= 247:
            weather["current"]["wind_arrow"] = "↙"
        elif 157 < direction <= 202:
            weather["current"]["wind_arrow"] = "↓"
        elif 112 < direction <= 157:
            weather["current"]["wind_arrow"] = "↘"
        elif 67 < direction <= 112:
            weather["current"]["wind_arrow"] = "→"
        else:
            weather["current"]["wind_arrow"] = "↗"

        # fixes/additions
        weather["current"]["condition"]["icon"] = f'https:{weather["current"]["condition"]["icon"]}'  # fix up image url
        weather["current"]["precipitation"] = precipitation
        latitude, longitude = weather["location"]["lat"], weather["location"]["lon"]
        return weather, latitude, longitude


async def get_places(client_session: aiohttp.ClientSession, latitude, longitude, radius: 5000, search_type: str):
    async with client_session.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json',
                                  params={
                                      'location': f"{latitude},{longitude}",
                                      'radius': radius,
                                      'type': search_type,
                                      "key": google_places_key
                                  }) as response:
        results = await response.json()
        places = []
        for place in results["results"]:
            name = place["name"]
            address = place["vicinity"]

            rating = place.get("rating", 0)
            rating_color = ""
            if 1 <= rating <= 3.5:
                rating_color = "yellow"

            total_ratings = place.get("user_ratings_total", 0)
            total_rating_color = ""
            if total_ratings < 25:
                total_rating_color = "yellow"

            price_level = place.get("price_level")
            price_color = ""
            match price_level:
                case 0:
                    price_level = "Free"
                case 1:
                    price_level = "Inexpensive"
                case 2:
                    price_level = "Moderate"
                    price_color = "orange"
                case 3:
                    price_level = "Expensive"
                    price_color = "orange"
                case 4:
                    price_level = "Very Expensive"
                    price_color = "orange"
                case _:
                    price_level = "N/A"
                    price_color = "subtext0 italics"

            open_color = ""
            opening_hours = place.get("opening_hours")
            if opening_hours:
                if opening_hours.get("open_now"):
                    is_open = "Currently Open"
                else:
                    is_open = "Closed"
                    open_color = "red"
            elif place["business_status"] == "CLOSED_TEMPORARILY":
                is_open = "Temporarily Shut Down"
                open_color = "red"
            elif place["business_status"] == "CLOSED_PERMANENTLY":
                continue
            else:
                is_open = "N/A"
                open_color = "subtext0 italics"

            types = place["types"]
            link = f'https://www.google.com/maps/place/?q=place_id:{place["place_id"]}'

            if type(types) is not None:
                types.sort()
                types = ', '.join(map(str, types))

            places.append({
                'name': name,
                'address': address,
                'rating': rating,
                'rating_color': rating_color,
                'total_ratings': total_ratings,
                'total_rating_color': total_rating_color,
                'price_level': price_level,
                'price_color': price_color,
                'is_open': is_open,
                'open_color': open_color,
                'types': types,
                'link': link
            })

        sorted_places = sorted(places, reverse=True, key=lambda sort_key: sort_key['rating'])
        for entry in sorted_places:
            if entry["rating"] == 0:
                entry["rating"] = "N/A"
                entry["rating_color"] = "subtext0 italics"

        return sorted_places


@app.route("/itinerary")
async def itinerary():
    if 'location' in session and 'radius' in session:
        location = session.pop('location')
        radius = session.pop('radius')

        try:
            async with aiohttp.ClientSession() as client_session:
                weather, latitude, longitude = await get_weather(client_session, location)
                attractions = await get_places(client_session, latitude, longitude, radius, 'tourist_attraction')
                restaurants = await get_places(client_session, latitude, longitude, radius, 'restaurant')
            return await render_template("/itinerary/index.html", location=weather["location"], weather=weather,
                                         attractions=attractions, restaurants=restaurants)
        except Exception as error:
            # raise error  # used for when something is wrong
            session['error'] = '\n'.join([
                ''.join(traceback.format_exception_only(None, error)).strip(),
                ''.join(traceback.format_exception(None, error, error.__traceback__)).strip()])
            return redirect(url_for('index'))
    else:
        return redirect(url_for("index"))


@app.route("/", methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        form = await request.form
        session['location'] = form['location']
        session['radius'] = form['radius']

        try:
            radius = int(session['radius'])
            if 1000 > radius > 50000:
                session['error'] = "RadiusInvalid"
        except ValueError:
            session['error'] = "RadiusInvalid"
            return redirect(url_for("index"))

        return redirect(url_for('itinerary'))

    raised_error = session.pop('error', "")

    if "LocationNotFound" in raised_error:
        error = "The requested location could not be found. Please enter a valid location."
    elif "RadiusInvalid" in raised_error:
        error = "The entered radius is invalid. Please enter a valid radius between 1000 and 50000."
    else:
        error = raised_error
    return await render_template("index.html", error=error)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
