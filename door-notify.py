#!/usr/bin/python

import RPi.GPIO as GPIO
import time
import logging
import sys
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import requests

#config
LOG_FILE="/home/pi/projects/door-notify/logs/door-notify.log"
NOTIFY_INTERVAL=180    # 180 seconds / 3 mins
EMAIL_TO="padmin@rabbitsky.com"
EMAIL_FROM=EMAIL_TO
EMAIL_SERVER="smtp.gmail.com:587"
EMAIL_LOGIN=EMAIL_FROM
EMAIL_PASSWORD="password"
GPIO_SENSOR=37
LIGHT_URL="http://host:port/api/light/"

def send_email(subj):
  msg = MIMEText("eom")
  msg['Subject'] = subj
  msg['To'] = EMAIL_TO
  msg['From'] = EMAIL_FROM
  s = smtplib.SMTP(EMAIL_SERVER)
  s.ehlo()
  s.starttls()
  s.login(EMAIL_LOGIN, EMAIL_PASSWORD)
  s.sendmail(EMAIL_FROM, [ EMAIL_TO ], msg.as_string())
  s.quit()
  logging.info("Email sent: %s" % msg['Subject'])

def notify(state, since_time, len):
  msg = ""
  if (len == 0):
    msg = "Garage door just " + state
  else :
    since_time_str = since_time.strftime("%Y%m%d %H:%M:%S")
    msg = "Garage door %s for %d mins since %s" % (state, len/60, since_time_str)

  logging.info("Going to notify with msg: %s" % msg)
  param = "on" if state == "OPEN" else "off"
  try:
    requests.get(LIGHT_URL+param)
  except Exception as ex:
    logging.exception("Failed to turn lights on", exc_info=True)

  #try:
  #  send_email(msg)
  #except Exception as ex:
  #  logging.info("Failed to send email", exc_info=True )

def door_opened(channel):
  open_since = datetime.now()
  time.sleep(0.5)
  if not GPIO.input(GPIO_SENSOR): # close
    logging.debug("Error signal detected, skipped.")
    return

  notify("OPEN", open_since, 0)
  last_notify_time = datetime.now()

  while True:
    if GPIO.input(GPIO_SENSOR): # open
      t = (datetime.now() - last_notify_time).total_seconds()
      total = (datetime.now() - open_since).total_seconds()
      logging.debug("Door OPEN since last notify: %d seconds, since open: %d seconds..." % (t, total))
      if t > NOTIFY_INTERVAL:
        notify("OPEN", open_since, total)
        last_notify_time = datetime.now()
      time.sleep(1)
    else:
      logging.info("Door CLOSED")
      notify("CLOSE", datetime.now(), 0)
      break

def main():
  logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
  logger = logging.getLogger()
  ch = logging.StreamHandler(sys.stdout)
  logger.addHandler(ch)

  #init GPIO
  GPIO.setmode(GPIO.BOARD)
  GPIO.setup(GPIO_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)

  GPIO.add_event_detect(GPIO_SENSOR, GPIO.RISING, callback=door_opened, bouncetime=1000)
  if GPIO.input(GPIO_SENSOR):      # if already open
    door_opened(GPIO_SENSOR)

  try:
    logging.info("Garage Door Detector Started...")
    while True:
      time.sleep(10)
    logging.info("Shutting down...")
  except KeyboardInterrupt:
    logging.info("Interrupted")
  finally:
    GPIO.cleanup()
  GPIO.cleanup()
  logging.info("DONE.")

if __name__ == '__main__':
  main()
