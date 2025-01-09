import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from inky.auto import auto
from inky.inky_uc8159 import CLEAN
import inky
from PIL import Image, ImageDraw, ImageFont
from font_source_sans_pro import SourceSansProSemibold

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

normal_font = ImageFont.truetype(SourceSansProSemibold, 24)
small_font = ImageFont.truetype(SourceSansProSemibold, 18)
large_font = ImageFont.truetype(SourceSansProSemibold, 48)

def drawEvent(canvas, disp, event, offset):
  start = event["start"].get("dateTime", event["start"].get("date"))
  dt = datetime.datetime.fromisoformat(start).strftime('%a %-d %b %Y, %H:%M')
  print(start, event["summary"])
  canvas.text((10,offset), dt + " " + event["summary"], disp.BLACK, normal_font)
  if "location" in event.keys():
    canvas.text((10, offset+24), event["location"], disp.BLACK,small_font)

def getLatestEventsFromGoogleCalendar(maxEvents):
  creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    cal_id = "f2580995446ab1540fa30e2e6193c19bb3dad048042dfef783d5e42fa8c7a853@group.calendar.google.com"
    # print("Getting the upcoming 10 events")
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

def main():
  print("Getting latest events")
  events = getLatestEventsFromGoogleCalendar(6)

  if not events:
    print("No upcoming events found.")
    return

  print(f"got {len(events)} events")

  print("init display")
  disp = auto(ask_user=True, verbose=True)

  print("Cleaning display")
  for _ in range(2):  
    for y in range(disp.height - 1):
      for x in range(disp.width - 1):
          disp.set_pixel(x, y, CLEAN)

  print("Create canvas")
  img = Image.new("P", disp.resolution, disp.WHITE)
  canvas = ImageDraw.Draw(img)

  canvas.text((10,10), datetime.date.today().strftime("%d %B %Y"), disp.BLACK, large_font)
  canvas.line([(0,94),(disp.width-1,94)],disp.BLACK, 2)

  y = 96
  for event in events:
    drawEvent(canvas, disp, event, y)
    y += 64

  last_updated = datetime.datetime.today().strftime('%a %-d %b %Y, %H:%M')
  canvas.text((10, disp.height-20), f"Last updated: {last_updated}", disp.BLACK, small_font)
  
  disp.set_image(img)

  disp.show()
  


if __name__ == "__main__":
  main()
