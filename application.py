# Start with a basic flask app webpage.
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from random import random, sample
from time import sleep
from threading import Thread, Event

# import speech to text module
import speech_recognition as sr
# import natural language for sentiment analysis module
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

import RPi.GPIO as GPIO
import time
import signal
import sys
import os

# initialize the recognizer
r = sr.Recognizer()
#mic = sr.Microphone(device_index=2)
# for pi use mic as source

# clean up pins before exit
def onterm(*args):
    print("clean up pins")
    GPIO.cleanup()
    exit()

# if programme is terminated
signal.signal(signal.SIGTERM, onterm)
# if programme is aborted
signal.signal(signal.SIGABRT, onterm)
# if programme is terminated with ctrl + c
signal.signal(signal.SIGINT, onterm)

# set which pi pins trigger the relays
Relay_Ch1 = 5
Relay_Ch3 = 13
Relay_Ch5 = 19
Relay_Ch7 = 21

# set pin numbers for the LEDs
yellow_LED_pin = 7
red_LED_pin = 9
power_button = 12

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# set relay pins as output and set them to off - high signal is off
GPIO.setup(Relay_Ch1,GPIO.OUT)
GPIO.setup(Relay_Ch3,GPIO.OUT)
GPIO.setup(Relay_Ch5,GPIO.OUT)
GPIO.setup(Relay_Ch7,GPIO.OUT)
GPIO.output(Relay_Ch1,GPIO.HIGH)
GPIO.output(Relay_Ch3,GPIO.HIGH)
GPIO.output(Relay_Ch5,GPIO.HIGH)
GPIO.output(Relay_Ch7,GPIO.HIGH)

# set LED pins as output and initialise as off
GPIO.setup(yellow_LED_pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(red_LED_pin, GPIO.OUT, initial=GPIO.LOW)

# set power button pin as input so can determine when pressed and initialise to 3.3v
GPIO.setup(power_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# turn the flask app into a socketio app
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

# speech detection Thread
thread = Thread()
thread_stop_event = Event()

# turn green LED on to show programme is running
GPIO.output(yellow_LED_pin, GPIO.HIGH)

def Shutdown(gpio_pin):
    print("shutdown function")
    # os.system("sudo shutdown -h now")
    # make sure it is the button being pressed which has triggered the function
    if GPIO.input(power_button) == GPIO.LOW:
        print("button pressed")
        print("clean up pins")
        GPIO.cleanup()
        print("SHUTTING DOWN", file=sys.stderr)
        os.system("sudo shutdown -h now")


# Shutdown function executes when power button is pressed
GPIO.add_event_detect(power_button, GPIO.FALLING, callback=Shutdown, bouncetime=2000)

# change to alter number of seconds that microphone is recording for
listening_seconds = 5

def speechToText():
    #infinite loop of magical random numbers
    print("Making random numbers")
    while not thread_stop_event.isSet():
        with sr.Microphone() as source:
            # read the audio data from the default microphone
            print('listening...')
            # turn the 'listening' light on
            GPIO.output(red_LED_pin, GPIO.HIGH)
            # records mic audio for chosen number of seconds
            audio_data = r.record(source, duration=listening_seconds)
            # turn the 'listening' light off
            GPIO.output(red_LED_pin, GPIO.LOW)
            print('converting...')
            # try to convert speech to text
            try:
                text = r.recognize_google(audio_data, language="en-GB")
                socketio.emit('newspeech', {'speech': text}, namespace='/test')
                socketio.sleep(1)
                # get sentiment of words
                sentiment_analysis(text)
            # print error if no speech detected
            except sr.UnknownValueError as e:
                print('speech not recognised', str(e))
                socketio.emit('newspeech', {'speech': 'speech not recognised'}, namespace='/test')
                socketio.emit('newscore', {'score': 0}, namespace='/test')
                socketio.sleep(1)

def sentiment_analysis(text):
    print(text)
    # initialise sentiment analyser
    sia = SentimentIntensityAnalyzer()
    # get negativity score as a percentage
    negativity = (sia.polarity_scores(text)["neg"])*100
    # round to 1 decimal place
    negativity_score = round(negativity, 1)
    print(negativity_score)
    socketio.emit('newscore', {'score': negativity_score}, namespace='/test')
    socketio.sleep(1)
    # if the text is negative trigger the horns
    if negativity_score > 0:
        trigger_horns(negativity_score)

# amount of time horns are blowing for
honk_time = 1.5

def trigger_horns(negativity_score):
    print("NEGATIVE")
    horns = [Relay_Ch1, Relay_Ch3, Relay_Ch5, Relay_Ch7]
    # activate one horn
    if (negativity_score) <= 25:
        print("neg 1")
        random_horn = sample(horns, 1)
        # turn horn on
        GPIO.output(random_horn,GPIO.LOW)
        # wait for x seconds
        time.sleep(honk_time)
        # turn horn off
        GPIO.output(random_horn,GPIO.HIGH)
    # activate two horns    
    elif (negativity_score) <= 50:
        print("neg 2")
        random_horns = sample(horns, 2)
        print(random_horns)
        # turn horns on
        for horn in random_horns:
            GPIO.output(horn,GPIO.LOW)
        # wait for x seconds
        time.sleep(honk_time)
        # turn horn off
        for horn in random_horns:
            GPIO.output(horn,GPIO.HIGH)
    # activate three horns    
    elif (negativity_score) <= 75:
        print("neg 3")
        random_horns = sample(horns, 3)
        print(random_horns)
        # turn horns on
        for horn in random_horns:
            GPIO.output(horn,GPIO.LOW)
        # wait for x seconds
        time.sleep(honk_time)
        # turn horn off
        for horn in random_horns:
            GPIO.output(horn,GPIO.HIGH)
    # activate all four horns    
    elif (negativity_score) <= 100:
        print("neg 4")
        # turn horns on
        for horn in horns:
            GPIO.output(horn,GPIO.LOW)
        # wait for x seconds
        time.sleep(honk_time)
        # turn horn off
        for horn in horns:
            GPIO.output(horn,GPIO.HIGH)
    # little pause before the next round
    time.sleep(4)

@app.route('/')
def index():
    #only by sending this page first will the client be connected to the socketio instance
    return render_template('index.html')

@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    #Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        thread = socketio.start_background_task(speechToText)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)
