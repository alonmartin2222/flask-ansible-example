from flask import Flask, render_template, request, Response, redirect
import requests as http
from datetime import datetime
import pytz
from boto3 import client, resource


app = Flask(__name__)

weather = 0

@app.route('/')
def home():
    """Render base.html"""
    return render_template('base.html')


@app.route('/weather', methods=['POST'])
def weather():
    """Render the weather page"""
    city = request.form['city2']

    lon_lat_json = get_lon_lat(city)
    if lon_lat_json == 'error':
        return render_template('not_found.html')

    weather_json = get_weather(lon_lat_json["coord"]["lon"], lon_lat_json["coord"]["lat"])
    if weather_json == 'error':
        return render_template('not_found.html')

    display_data = display_weather(pytz.country_names[lon_lat_json["sys"]["country"]], city, weather_json)

    global weather
    weather = display_data

    return render_template('weather.html', data=display_data)


def get_lon_lat(city):
    """HTTP call to get longtitude and latitude for input city"""
    try:
        res = http.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid=4b44f96c1610177ef0954ca0f869b488")
        print(res.json())
        res.raise_for_status()
    except http.exceptions.HTTPError:
        return "error"

    return res.json()


def get_weather(lon, lat):
    """HTTP call to get the 7 days weather for input city"""
    api_key = '4b44f96c1610177ef0954ca0f869b488'
    exclude = 'current,minutely,hourly,alerts'
    url = 'https://api.openweathermap.org/data/2.5/onecall?'
    try:
        response = http.get(f"{url}lat={lat}&lon={lon}&units=metric&exclude={exclude}&appid={api_key}")
        response.raise_for_status()
    except http.exceptions.HTTPError:
        return "error"

    return response.json()


def display_weather(country, city, weather_data):
    """Get all the data so far and put it in a Dict"""
    dict1 = {0: country, 1: city.capitalize()}

    for n, e in enumerate(weather_data["daily"], 2):
        date = datetime.fromtimestamp(e["dt"])
        day = date.strftime("%A")
        day_cal = date.isoformat().split('T')[0]
        day_degree = e['temp']['day']
        night_degree = e['temp']['night']
        humidity = e['humidity']
        icon = e['weather'][0]['icon']
        dict1[n] = [day, day_cal, day_degree, night_degree, humidity, icon]
    return dict1


def create_user():
    iam = client("iam")
    response = iam.create_user(UserName="Alon")
    print(response)


def attach_user_policy():
    iam = client("iam")
    response = iam.attach_user_policy(
        UserName="Alon",
        PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess"
    )
    print(response)



# def download_image():
#     s3_client = resource('s3')
#     s3_client.Object("alon2222bucket", "test.txt").download_file(
#         f'{Path.home()}/Downloads/{"image.txt"}')


@app.route('/image', methods=['GET'])
def index():
    s3 = client('s3')
    file = s3.get_object(Bucket='alon2222bucket', Key='sky')
    return Response(
        file['Body'].read(),
        mimetype='image/jpeg',
        headers={"Content-Disposition": "attachment;filename=sky"}
    )

@app.route('/upload', methods=['GET'])
def upload_to_db():
    dynamodb = resource('dynamodb', region_name='eu-west-2')
    now = datetime.now()

    global weather

    table = dynamodb.Table('weather')
    table.put_item(
        Item={
            'id': f"{now}",
            'data': f"{weather}"
        }
    )
    return redirect("/")


if __name__ == '__main__':
    app.run(host='0.0.0.0')
