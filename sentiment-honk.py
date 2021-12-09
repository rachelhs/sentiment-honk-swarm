# import speech to text module
import speech_recognition as sr
# import natural language for sentiment analysis module
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# initialize the recognizer
r = sr.Recognizer()

def main():
    with sr.Microphone() as source:
        # read the audio data from the default microphone
        print('listening...')
        # records mic audio for 5 seconds
        audio_data = r.record(source, duration=5)
        print('converting...')
        # try to convert speech to text
        try:
            text = r.recognize_google(audio_data)
            # get sentiment of words
            sentiment_analysis(text)
        # print error if no speech detected
        except sr.UnknownValueError as e:
            print('speech not recognised', str(e))

def sentiment_analysis(text):
    print(text)
    # initialise sentiment analyser
    sia = SentimentIntensityAnalyzer()
    # get negativity score as a percentage
    negativity = (sia.polarity_scores(text)["neg"])*100
    # round to 1 decimal place
    negativity_score = round(negativity, 1)
    print(negativity_score)

while True:
    main()