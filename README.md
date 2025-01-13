Small application to show calender events, today's weather and a quote on the [Piromoni Inky Impression 7.3" 7 color e-ink display](https://shop.pimoroni.com/products/inky-impression-7-3?variant=40512683376723)

# Requirements

* A Inky Impression display
* A Raspberry PI

# Usage

Setup a virtual environment with and activate it (I used python 3.11)

Follow the google calendar quickstart and copy/run the python file to the root directory and follow the instructions to get a credentials and a token.json

this includes installing the dependencies in the current virtualenv

Install the dependencies:

```
pip install inky requests font_source_sans_pro configparser
```
Copy `config.default.txt` to  `config.txt`

Goto https://openweathermap.org, subscribe, create an api key and add it with the latitude and longitude of your location to the configuration in the config.txt

Get the Calender ID of the google calendar you want to show and fill that in (right click the calendar -> Sharing & Settings scroll down to integration) 

now you can run the inky_app.py

I've crontabbed run.sh to make it update each morning
