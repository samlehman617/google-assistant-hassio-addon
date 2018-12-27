#!/usr/bin/env python
# Needs actions.py, config.yaml, indicator.py, pushbutton.py, snowboydecoder.py, snowboydetect.py
try:
    import RPi.GPIO as GPIO
except Exception as e:
    if str(e) == 'No module named \'RPi\'':
        GPIO = None
import argparse
import json
import os.path
import pathlib2 as pathlib
import os
import subprocess
import re
import psutil
import logging
import time
import random
import snowboydecoder
import sys
import signal
import requests
import google.oauth2.credentials
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
from google.assistant.library.device_helpers import register_device
from actions import say, trans, Action, configuration, custom_action_keyword, gender
from threading import Thread

if GPIO != None:
    from indicator import assistantindicator
    from indicator import stoppushbutton
    GPIOcontrol = True
else:
    GPIOcontrol = False

from pathlib import Path

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

# Webserver
import click
import google.auth.transport.grpc
from google.auth.transport import requests as grequest
from google_assistant.embedded.v1alpha2 import embedded_assistant_pb2, embedded_assistant_pb2_grpc
from flask import Flask, request, jsonify
from flask_restful import Resource, Api

from webserver.assistant_webserver import GoogleTextAssistant

WARNING_NOT_REGISTERED = """
    This device is not registered. This means you will not be able to use Device Actions or see your device in Assistant Settings. In order to register this device follow instructions at: 
        
    https://developers.google.com/assistant/sdk/guides/library/python/embed/register-device        
"""
logging.basicConfig(filename="/tmp/gassistant.log", level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

mutestopbutton = True

# Magic Mirror Remote Control
mmip = configuration['Mmmip']

# Custom Wakeword
if configuration['Wakewords']['Custom_Wakeword'] == 'Enabled':
    custom_wakeword = True
else:
    custom_wakeword = False
models = configuration['Wakewords']['Custom_wakeword_models']

# Custom conversation
num_ques = len(configuration['Conversation']['question'])
num_ans = len(configuration['Conversation']['answer'])


class MyAssistant():
    def __init__(self):
        self.interrupted = False
        self.assistant = None
        self.sensitivity = [0.5]*len(models)
        self.detector = snowboydecoder.HotwordDetector(models, sensitivity=self.sensitivity)
        self.t1 = Thread(target=self.start_detector)
        if GPIOcontrol:
            self.t2 = Thread(target=self.pushbutton)

    def signal_handler(self, signal, frame):
        self.interrupted = True

    def interrupt_callback(self, ):
        return self.interrupted

    def buttonSinglePress(self):
        if os.path.isfile("/.mute"):
            os.system("sudo rm /.mute")
            assistantindicator('unmute')
            # shivasiddharth/GassistPi...src/main.py
            if configuration['Wakewords']['Ok_Google'] == 'Disabled':
                self.assistant.set_mic_mute(True)
            else:
                self.assistant.set_mic_mute(False)
            if gender == 'Male':
                subprocess.Popen(['aplay', "{}/resources/sample-audio-files/Mic-On-Male.wav"], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.Popen(['aplay', "{}/resources/sample-audio-files/Mic-On-Female.wav"], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Turning on the microphone")
        else:
            open('/.mute', 'a').close()
            assistantindicator('mute')
            self.assistant.set_mic_mute(True)
            if gender == 'Male':
                subprocess.Popen(['aplay', "/resources/sample-audio-files/Mic-On-Male.wav"], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.Popen(['aplay', "/resources/sample-audio-files/Mic-On-Female.wav"], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Turning off the microphone")

    def buttondoublepress(self):
        print('Stopped')
        stop()

    def buttontriplepress(self):
        print("Create your own action for button triple press")

    def pushbutton(self):
        if GPIOcontrol:
            while mutestopbutton:
                time.sleep(.1)
                if GPIO.event_detected(stoppushbutton):
                    GPIO.remove_event_detect(stoppushbutton)
                    now = time.time()
                    count = 1
                    while time.time() < now + 1:
                        if GPIO.event_detected(stoppushbutton):
                            count += 1
                            time.sleep(.25)
                    if count == 2:
                        self.buttonSinglePress()
                        GPIO.remove_event_detect(stoppushbutton)
                        GPIO.add_event_detect(stoppushbutton, GPIO.FALLING)
                    elif count == 3:
                        self.buttonTriplePress()
                        GPIO.remove_event_detect(stoppushbutton)
                        GPIO.add_event_detect(stoppushbutton, GPIO.FALLING)

    def process_device_actions(self, event, device_id):
        if 'inputs' in event.args:
            for i in event.args['inputs']:
                if i['intent'] == 'action.devices.EXECUTE':
                    for c in i['payload']['commands']:
                        for device in c['devices']:
                            if device['id'] == device_id:
                                if 'execution' in c:
                                    for e in c['execution']:
                                        if 'params' in e:
                                            yield e['command'], e['params']
                                        else:
                                            yield e['command'], None


    def process_event(self, event):
        # Prettyprints events
        # Args: event(event.Event): The current event to process
        print(event)
        if event.type == EventType.ON_START_FINISHED:
            self.can_start_conversation = True
            if GPIOcontrol:
                self.t2.start()
            if os.path.isfile("/.mute"):
                assistantindicator('mute')
            if (configuration['Wakewords']['Ok_Google'] == 'Disabled' or os.path.isfile("/.mute")):
                self.assistant.set_mic_mute(True)
            if custom_wakeword:
                self.t1.start()

        if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
            self.can_start_conversation = False
            subprocess.Popen(["aplay", "/resources/sample-audio-files/Fb.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if GPIOcontrol:
                assistantindicator('listening')
            print()
        if (event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT or event.type == EventType.ON_NO_RESPONSE):
            self.can_start_conversation = True
            if GPIOcontrol:
                assistantindicator('off')
            if (configuration['Wakewords']['Ok_Google'] == 'Disabled' or os.path.isfile("/.mute")):
                self.assistant.set_mic_mute(True)
            if os.path.isfile("/.mute"):
                if GPIOcontrol:
                    assistantindicator('mute')
        if (event.type == EventType.ON_RESPONDING_STARTED and event.args and not event.args['is_error_response']):
            if GPIOcontrol:
                assistantindicator('speaking')
        if event.type == EventType.ON_RESPONDING_FINISHED:
            if GPIOcontrol:
                assistantindicator('off')
        if event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED:
            if GPIOcontrol:
                assistantindicator('off')
        print(event)
        if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and event.args and not event.args['with_follow_on_turn']):
            self.can_start_conversation = True
            if GPIOcontrol:
                assistantindicator('off')
            if (configuration['Wakewords']['Ok_Google'] == 'Disabled' or os.path.isfile("/.mute")):
                self.assistant.set_mic_mute(True)
            if os.path.isfile("/.mute"):
                if GPIOcontrol:
                    assistantindicator('mute')
            print()
        if event.type == EventType.ON_DEVICE_ACTION:
            for command, params in event.actions:
                print('Do command', command, 'with params', str(params))

    def register_device(self, project_id, credentials, device_model_id, device_id):
        # Register device if needed
        # Args:
        # project_id(str): The project ID used to register device instance.
        # credentials(google.oauth2.credentials.Credentials): Google OAuth2 credentials of the user to associate device instance with.
        # device_model_id: The registered device model ID.
        # device_id: The device ID of the new instance
        base_url = '/'.join([DEVICE_API_URL, 'projects', project_id, 'devices'])
        device_url = '/'.join([base_url, device_id])
        session = google.auth.transport.requests.AuthorizedSession(credentials)
        r = session.get(device_url)
        print(device_url, r.status_code)
        if r.status_code == 404:
            print('Registering...')
            r = session.post(base_url, data=json.dumps({
                'id': device_id,
                'model_id': device_model_id,
                'client_type': 'SDK_LIBRARY'
            }))
            if r.status_code != 200:
                raise Exception('Failed to register device: ' + r.text)
            print('\rDevice registered.')

    def detected(self):
        if self.can_start_conversation == True:
            self.assistant.set_mic_mute(False)
            self.assistant.start_conversation()
            print("Assistant is listening...")

    def start_detector(self):
        self.detector.start(detected_callback=self.callbacks, interrupt_check=self.interrupt_callback, sleep_time=0.03)

    def main(self):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('--device-model-id', '--device_model_id', type=str, metavar='DEVICE_MODEL_ID', required=False, help='the device model ID registered with Google')
        parser.add_argument('--project-id', '--project_id', type=str, metavar='PROJECT_ID', required=False, help="the project ID used to register this device")
        parser.add_argument('--nickname', type=str, metavar='NICKNAME', required=False, help="the nickname used to register this device")
        parser.add_argument('--device-config', '--device_config', type=str, metavar='DEVICE_CONFIG_FILE',
                            default="/data/client.json",
                            help="path to store and read OAuth2 credentials")
        parser.add_argument('--credentials', type=existing_file,
                            metavar='OAUTH2_CREDENTIALS_FILE',
                            default="/data/cred.json",
                            help="path to store and read OAuth2 credentials"
                            )
        parser.add_argument('--query', type=str, metavar='QUERY', help='query to send as soon as the Assistant starts')
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + Assistant.__version_str__())
        args = parser.parse_args()
        with open(args.credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None, **json.load(f))
        device_model_id = None
        last_device_id = None
        try:
            with open(args.device_config) as f:
                device_config = json.load(f)
                device_model_id = device_config['model_id']
                last_device_id = device_config.get('last_device_id', None)
        except FileNotFoundError:
            print("Device config file not found.")

        if not args.device_model_id and not device_model_id:
            raise Exception("Missing --device-model-id option")

        # Re-register if 'device_model_id" is given by the user and it differs from what we previously registered with.
        should_register = (args.device_model_id and args.device_model_id != device_model_id)
        device_model_id = args.device_model_id or device_model_id
        with Assistant(credentials, device_model_id) as assistant:
            self.assistant = assistant
            if gender == 'Male':
                subprocess.Popen(['aplay', "/resources/sample-audio-files/Startup-Male.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.Popen(['aplay', "/resources/sample-audio-files/Startup-Female.wav"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            events = assistant.start()
            device_id = assistant.device_id
            print('device_model_id: ', device_model_id)
            print('device_id: ', device_id + '\n')

            # Re-register if 'device_id' is different from the last 'device_id':
            if should_register or (device_id != last_device_id):
                if args.project_id:
                    register_device(args.project_id, credentials, device_model_id, device_id, args.nickname)
                    pathlib.Path(os.path.dirname(args.device_config)).mkdir(exist_ok=True)
                    with open(args.device_config, 'w') as f:
                        json.dump({
                            'last_device_id': device_id,
                            'model_id': device_model_id,
                        }, f)
                else:
                    print(WARNING_NOT_REGISTERED)
            for event in events:
                if event.type == EventType.ON_START_FINISHED and args.query:
                    assistant.send_text_query(args.query)
                self.process_event(event)
                usr_cmd = event.args
                if configuration['Conversation']['Conversation_Control'] == 'Enabled':
                    for i in range(1, num_ques+1):
                        try:
                            if str(configuration['Conversation']['question'][i][0]).lower() in str(usr_cmd).lower():
                                assistant.stop_conversation()
                                selected_ans = random.sample(configuration['Conversation']['answer'][i], 1)
                                say(selected_ans[0])
                                break
                        except KeyError:
                            say('Please check if the number of questions matches the number of answers in your config file')
                if (custom_action_keyword['Keywords']['Magic_mirror'][0]).lower() in str(usr_cmd).lower():
                    assistant.stop_conversation()
                    try:
                        mmcommand = str(usr_cmd).lower()
                        if 'weather'.lower() in mmcommand:
                            if 'show'.lower() in mmcommand:
                                mmreq1 = requests.get("http://"+mmip+":8080/remote?action=SHOW&module=module_2_currentweather")
                                mmreq2 = requests.get("http://"+mmip+":8080/remote?action=SHOW&module=module_3_currentweather")
                            if 'hide'.lower() in mmcommand:
                                mmreq1 = requests.get("http://"+mmip+":8080/remote?action=HIDE&module=module_2_currentweather")
                                mmreq2 = requests.get("http://"+mmip+":8080/remote?action=HIDE&module=module_3_currentweather")
                        if 'power off'.lower() in mmcommand:
                            mmreq = requests.get("http://"+mmip+":8080/remote?/action=SHUTDOWN")
                        if 'reboot'.lower() in mmcommand:
                            mmreq = requests.get('http://'+mmip+":8080/remote?action=REBOOT")
                        if 'restart'.lower() in mmcommand:
                            mmreq = requests.get('http://'+mmip+":8080/remote?action=RESTART")
                        if 'display on'.lower() in mmcommand:
                            mmreq = requests.get('http://'+mmip+":8080/remote?action=MONITORON")
                        if 'display off'.lower() in mmcommand:
                            mmreq = requests.get('http://'+mmip+":8080/remote?action=MONITOROFF")
                    except requests.exceptions.ConnectionError:
                        say("Magic Mirror is offline")
                if configuration['Raspberrypi_GPIO_Control']['GPIO_Control'] == 'Enabled':
                    if (custom_action_keyword['Keywords']['Pi_GPIO_control'][0]).lower() in str(usr_cmd).lower():
                        assistant.stop_conversation()
                        Action(str(usr_cmd).lower())

        if custom_wakeword:
            self.detector.terminate()

if __name__ == '__main__':
    try:
        MyAssistant().main()
    except Exception as error:
        logger.exception(error)

