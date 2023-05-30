from __future__ import print_function
import streamlit as st
import speech_recognition as sr
import openai
import re
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
import time 
import os



### defintion arguments
r = sr.Recognizer()
openai.api_key = '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'

# Function to display the quiz questions
def display_quiz(chatbot_response):
    quest = re.compile(r'^\d+(?:\)|\.|\-)(.+\?$)')
    opt = re.compile(r'^[a-zA-Z](?:\)|\.|\-)(.+$)')
    questions = []
    options=[]
    sub =[]
    answers =[]
    for line in chatbot_response.splitlines():
        if line == '':
            if sub:
                options.append(sub)
                sub=[]
        else:
            if quest.match(line):
                line_mod = line.strip()
                questions.append(line_mod)
            if opt.match(line):
                line_mod = line.strip()
                sub.append(line_mod)
    if sub:
        options.append(sub)


    return questions,options    


# Function to record speech and convert it to text
def record_speech():
    with sr.Microphone() as source:
        st.write("Please speak something...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.write("Sorry, could not understand audio.")
    except sr.RequestError as e:
        st.write("Sorry, could not request results from the Speech Recognition service; {0}".format(e))


def chat_with_gpt(text):
    # Define the prompt and the system message
    prompt = "User: {}\nAI:".format(text)
    # Generate a chat response using the ChatGPT API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract and return the chatbot's reply
    chatbot_reply = response['choices'][0]['message']['content']
    return chatbot_reply






def generate_Quiz(questions,options):
    SCOPES = "https://www.googleapis.com/auth/forms.body"
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

    store = file.Storage('token.json')
    creds = None
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        creds = tools.run_flow(flow, store)

    form_service = discovery.build('forms', 'v1', http=creds.authorize(
        Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)

    # Request body for creating a form
    NEW_FORM = {
        "info": {
            "title": "Quiz form",
        }
    }
    # Creates the initial form
    result = form_service.forms().create(body=NEW_FORM).execute()
    # Request body to add a multiple-choice question
    # JSON to convert the form into a quiz
    update = {
        "requests": [
            {
                "updateSettings": {
                    "settings": {
                        "quizSettings": {
                            "isQuiz": True
                        }
                    },
                    "updateMask": "quizSettings.isQuiz"
                }
            }
        ]
    }
    # Converts the form into a quiz
    question_setting = form_service.forms().batchUpdate(formId=result["formId"],body=update).execute()
    for i in range(len(questions)): 
        NEW_QUESTION = {
            "requests": [{
                "createItem": {
                    "item": {
                        "title": questions[i],
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [{"value":j} for j in options[i]],
                                    "shuffle": True
                                }
                            }
                        },
                    },
                    "location": {
                        "index": i
                    }
                }
            }]
        }
        question_setting = form_service.forms().batchUpdate(formId=result["formId"], body=NEW_QUESTION).execute()

    get_result = form_service.forms().get(formId=result["formId"]).execute()
    return get_result['responderUri']




# Streamlit app
def main():
    st.title("Quiz")
    if st.button('Start Recording'):
        text=record_speech()
        st.write(text)
        response=chat_with_gpt(text)
        link=generate_Quiz(questions=display_quiz(response)[0],options=display_quiz(response)[1])
        st.write(link)



if __name__ == "__main__":
    main()
