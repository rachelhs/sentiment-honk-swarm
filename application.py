# Start with a basic flask app webpage.
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, url_for, copy_current_request_context
from random import random
from time import sleep
from threading import Thread, Event

# import speech to text module
import speech_recognition as sr
# import natural language for sentiment analysis module
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# initialize the recognizer
r = sr.Recognizer()
#mic = sr.Microphone(device_index=2)
# for pi use mic as source

__author__ = 'slynn'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

#turn the flask app into a socketio app
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

#random number Generator Thread
thread = Thread()
thread_stop_event = Event()

def randomNumberGenerator():
    #infinite loop of magical random numbers
    print("Making random numbers")
    while not thread_stop_event.isSet():
        with sr.Microphone() as source:
            # read the audio data from the default microphone
            print('listening...')
            # records mic audio for 5 seconds
            audio_data = r.record(source, duration=8)
            print('converting...')
            # try to convert speech to text
            try:
                text = r.recognize_google(audio_data, language="en-GB")
                socketio.emit('newnumber', {'number': text}, namespace='/test')
                socketio.sleep(1)
                # get sentiment of words
                sentiment_analysis(text)
            # print error if no speech detected
            except sr.UnknownValueError as e:
                print('speech not recognised', str(e))
                socketio.emit('newnumber', {'number': 'speech not recognised'}, namespace='/test')
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
        thread = socketio.start_background_task(randomNumberGenerator)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)
