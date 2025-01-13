#!/usr/bin/env python3
import datetime
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from inky.auto import auto
from inky.inky_uc8159 import CLEAN
import inky
from PIL import Image, ImageDraw, ImageFont, ImageOps
from font_source_sans_pro import SourceSansProSemibold
import configparser
import requests
from io import BytesIO
import numpy as np

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

normal_font = ImageFont.truetype(SourceSansProSemibold, 24)
small_font = ImageFont.truetype(SourceSansProSemibold, 18)
large_font = ImageFont.truetype(SourceSansProSemibold, 48)

def getLabelFromText(txt):
  splitted = txt.split(':')
  if (len(splitted)>1):
    return splitted[0], splitted[1]
  else:
    return None, txt

 # ImageDraw.textbbox(xy, text, font=None, anchor=None, spacing=4, align='left', direction=None, features=None, language=None, stroke_width=0, embedded_color=False, font_size=None)



def drawEvent(canvas, disp, event, offset):
  start = event["start"].get("dateTime", event["start"].get("date"))
  dt = datetime.datetime.fromisoformat(start).strftime('%a %-d %b %Y, %H:%M')
  lbl, summary = getLabelFromText(event["summary"])
  if lbl:
    canvas.rounded_rectangle([(10, offset+3),(20+canvas.textlength(lbl, normal_font), offset+28)], radius=3, fill=disp.BLUE)
    canvas.text((15, offset), lbl, disp.WHITE, normal_font)
  canvas.text((100, offset), dt + " " + summary, disp.BLACK, normal_font)
  if "location" in event.keys():
    canvas.text((100, offset+24), event["location"], disp.BLACK,small_font)

def getLatestEventsFromGoogleCalendar(maxEvents, cal_id):
  creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  try:
    service = build("calendar", "v3", credentials=creds)

    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    events_result = (
        service.events()
        .list(
            calendarId=cal_id,
            timeMin=now,
            maxResults=maxEvents,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
  except HttpError as error:
    print(f"An error occurred: {error}")
    return []
  return events_result.get("items", [])

def getWeather(api_key, lat, lon):
  url = 'https://api.openweathermap.org/data/3.0/onecall?units=metric&lat=' + lat + '&lon=' + lon +'&appid=' + api_key + '&exclude=minutely,hourly,alerts'
  info=requests.get(url).json()
  daily=info["daily"][0]
  weather = daily["weather"][0]
  return {
          "temp": daily["temp"]["day"], 
          "feel": daily["feels_like"]["day"], 
          "pressure": daily["pressure"], 
          "humidity": daily["humidity"], 
          "main": weather["main"],
          "desc": weather["description"],
          "icon": weather["icon"]
         }

def getIcon(icon):
  icon_url = "http://openweathermap.org/img/w/" + icon + ".png";
  return requests.get(icon_url).content

def getQuote():
  quote = requests.get('https://zenquotes.io?api=random').json()[0]
  return f'"{quote["q"]}" - {quote["a"]}'

def split_line(line, split_at):
  words = line.split()
  lines = [' '.join(words[i:i + split_at]) for i in range(0, len(words), split_at)]
  return '\n'.join(lines)

def updateDisplay(config, weather, quote, events):
  disp = auto(ask_user=True, verbose=True)
  for _ in range(2):  
    for y in range(disp.height - 1):
      for x in range(disp.width - 1):
          disp.set_pixel(x, y, CLEAN)
  
  TOPBAR_LOWER_Y = 100
  BOTTOMBAR_UPPER_Y = 438
  MARGIN = 10
  WEATHER_NAMES_X = 450
  WEATHER_VALUES_X = 560
  ICON_LEFT = 700
  EVENT_HEIGHT = 50
  img = Image.new("P", disp.resolution, disp.WHITE)

  img.paste(disp.BLUE, (0, 0, disp.width-1, TOPBAR_LOWER_Y))
  img.paste(disp.BLUE, (0, BOTTOMBAR_UPPER_Y, disp.width-1, disp.height-1))
  icon_data = BytesIO(getIcon(weather["icon"]))
  icon_img = Image.open(icon_data).convert("RGBA").resize((100,100))
  img.paste(icon_img, (ICON_LEFT,MARGIN), mask=icon_img)

  canvas = ImageDraw.Draw(img)
  
  canvas.text((MARGIN, 0), datetime.date.today().strftime("%a %d %b"), disp.WHITE, large_font)
  canvas.text((MARGIN, 68), f"Last updated: {datetime.datetime.today().strftime('%H:%M')}", disp.WHITE, small_font)
  
  canvas.text((ICON_LEFT, 2), f'{weather["main"]}', disp.WHITE, small_font)

  canvas.text((WEATHER_NAMES_X, 2),  'Temperature',        disp.WHITE, small_font)
  canvas.text((WEATHER_NAMES_X, 18), 'Feels like ',        disp.WHITE, small_font)
  canvas.text((WEATHER_NAMES_X, 34), 'Pressure',           disp.WHITE, small_font)
  canvas.text((WEATHER_NAMES_X, 50), 'Humidity',           disp.WHITE, small_font)
 
  canvas.text((WEATHER_VALUES_X, 2),  f'{round(weather["temp"],0)} °C',    disp.YELLOW, small_font)
  canvas.text((WEATHER_VALUES_X, 18), f'{round(weather["feel"],0)} °C',    disp.YELLOW, small_font)
  canvas.text((WEATHER_VALUES_X, 34), f'{weather["pressure"]} P',          disp.YELLOW, small_font)
  canvas.text((WEATHER_VALUES_X, 50), f'{round(weather["humidity"],0)} %', disp.YELLOW, small_font)
  canvas.text((WEATHER_VALUES_X, 68), f'{weather["desc"]}',                disp.YELLOW, small_font)
  
  y = TOPBAR_LOWER_Y
  for event in events:
    drawEvent(canvas, disp, event, y)
    y += EVENT_HEIGHT

  canvas.multiline_text((MARGIN,BOTTOMBAR_UPPER_Y), quote, disp.WHITE, small_font)
 
# outputimg = Image.fromarray(img*255)
# outputimg.save("/home/gertjan/frame/screenshot.png", "png")
  saveImage(img)

  disp.set_image(img)
  disp.show()

def saveImage(img):
  in_array = np.full((1, 1), 300)
  multiplier  = lambda t: t * 255
  vfunc = np.vectorize(multiplier)
  out_array = vfunc(in_array)
  outputImage = Image.fromarray(out_array, mode="RGB")
  outputImage.save("/home/gertjan/frame/screenshot.png", "png")

def main():
  config=configparser.ConfigParser()
  try:
    config.read_file(open(os.getcwd() + '/config.txt'))
    lat = config.get('openweathermap', 'LAT', raw=False)
    lon = config.get('openweathermap', 'LON', raw=False)
    api_key = config.get('openweathermap', 'API_KEY', raw=False)
    cal_id =  config.get('googlecalendar', 'CALENDAR_ID', raw=False)
  except:
    print('Error getting config values')
  
  weather = getWeather(api_key, lat, lon)

  quote = split_line(getQuote(),20)

  events = getLatestEventsFromGoogleCalendar(6, cal_id)
  if not events:
    print("No upcoming events found.")
    return

  updateDisplay(config, weather, quote, events)

if __name__ == "__main__":
  main()
