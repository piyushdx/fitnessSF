from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import threading
import openai
import re
import os

from .utils.utils import attribute_validator, output_parser, format_prompt


class MembershipBot:
    def __init__(self, azure_openai_engine):
        self.azure_openai_engine = azure_openai_engine
        self.session_state = {}

        if "messages" not in self.session_state:
            self.session_state["messages"] = self.set_bot_persona()
            self.session_state["messages"].append(
                {"role": "assistant", "content": "Hi, Welcome to FitnessBot! How may I help you?"})

        self.cache_data = {"member_created": False,
                           "member_canceled": False}

    def set_bot_persona(self):
        messages = [
            {"role": "system", "content": """
    You are the gym-bot. You help people in buying gym memberships and canceling memberships. You talk to people like a human would talk to them. Start by greeting the user. Ask them about their workout preferences and certain other questions that should be asked to a beginner before starting the gym. Suggest a plan according to their preferences.
    
    Here are the pricing details:
    Basic -  $50 - Get access to essential gym facilities and equipment at an affordable price.
    Premium - $100 - Get exclusive benefits, personalized training, and access to premium amenities like sauna, steam room, and spa.
    Gold - $150 - VIP perks, advanced training programs, and top-of-the-line facilities
    Swimming Only - $75
    PT - $120 for 8 lessons per month
    
    bellow mentioned are few Task names with their description, which can help you in answering.
    
    ### Task : buy_membership
        If the user sounds uninterested, these are the required fields to buy the membership:
        1. First Name 
        2. Last Name 
        3. Contact City 
        4. Contact State 
        5. Contact Zip 
        6. Email
        7. Phone Number
        8. Emergency Contact Name 
        9. Emergency Contact Phone 
    
        Get the above details from the user in a natural flow with asking 2-3 fields at a time (STRICTLY FOLLOW THIS INFORMATION).
        If the user is not interested or if you don't know about something, tell the user to come for a free trial or visit to the gym. 
    
        In the subsequent conversations, remember your goal is to convince the user to buy the gym membership and get the above details from them.
        If any required fields's are still missing, ask them again in a natural flow with asking 2-3 fields at a time (STRICTLY FOLLOW THIS INFORMATION).
        Once you have all the required fields, generate a json for all the required fields. Ask for a final confirmation from the user to validate the given details with generated required fields json.
        If the user confirms, ask them to complete <amount> payment at 'http://18.144.92.141:7002/Payment'. 
        Then ask user, did they completed the payment?
        If user confirms the payment, tell them that they will receive Membership ID, invoice and other important documentations in e-mail, ask when they will come to the gym so that you can inform it to the front desk executive. Also let the user know about the gym address and the drive time from user's location.
    
    ### Task : cancel_membership
        if user asks for membership cancellation, first try to stop them from doing that by asking him/her the reasons for that.
        try to make them feel that they will be assured to be given best in the class services.
    
        if still user wants to cancel the membership, bellow are the required fields.
        1. Membership Id
        2. Cancellation Date
        3. Cancellation Reason
    
        Get the above details from the user in a natural flow with asking 2-3 fields at a time.
        In the subsequent conversations, remember your goal is to be polite and if user has issues with our services then try to convience them that we will improve our services soon.
        If any required fields's are still missing, ask them again.
        Once you have all the required fields's (STRICTLY FOLLOW THIS INFORMATION), generate a json for all the required fields. Ask for a final confirmation from the user to validate the given details.
        If the user confirms, write a kind message based on cancellationReason and cancellationDate.
        If the user do not confirms, ask them to provide conflicting information's.
    """}]
        return messages

    def generate_response(self):
        try:
            # response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=self.session_state['messages'],
            #                                         temperature=0.7)
            response = openai.ChatCompletion.create(engine=self.azure_openai_engine,
                                                    messages=self.session_state['messages'],
                                                    temperature=0.7)
            msg = response.choices[0].message
        except openai.error.APIError as e:
            # Handle API error here, e.g. retry or log
            msg = {"role": "assistant",
                   "content": "Error from OpenAI service --> API Error. Please try again after a few seconds."}
        except openai.error.APIConnectionError as e:
            # Handle connection error here
            msg = {"role": "assistant",
                   "content": "Error from OpenAI service --> Failed to connect to OpenAI API. Please try again after a few seconds."}
        except openai.error.RateLimitError as e:
            msg = {"role": "assistant",
                   "content": "Error from OpenAI service --> Rate Limit Error. Please try again after a few seconds."}
        except openai.error.ServiceUnavailableError as e:
            msg = {"role": "assistant",
                   "content": "Error from OpenAI service --> Service Unavailable Error. Please try again after a few seconds."}
        except Exception as e:
            print(f"Unexpected Error from OpenAI, {e}")
            msg = {"role": "assistant",
                   "content": "Error from OpenAI service --> Unexpected Error. Please try again after a few seconds."}
        return msg

    def clear_cache(self):
        self.cache_data = {}
        self.session_state = {}
        self.session_state["messages"] = self.set_bot_persona()
        self.session_state["messages"].append(
            {"role": "assistant", "content": "Hi, Welcome to FitnessBot! How may I help you?"})
        print("########################## I have cleared ecache from MembershipBot....")
        return jsonify({"status": "True"})

    def get_response(self, data):
        # try:
        # data = request.get_json()

        self.session_state['messages'].append({"role": "user", "content": f"{format_prompt} {data['query']}"})

        print("1111111111111111")
        msg = self.generate_response()
        print("2222222222222222")
        # session_state['messages'].append(msg)
        parsed_response = output_parser(msg["content"])

        max_parsing_try = 2
        total_parsing_tries = 1
        while parsed_response == "Parsing Error" and total_parsing_tries < max_parsing_try:
            print("going for trying again...")
            total_parsing_tries += 1
            msg = self.generate_response()
            print(msg)
            parsed_response = output_parser(msg["content"])

        if parsed_response == "Parsing Error":
            parsed_response = {"Task": "None", "response": "Could not understand, please try again...", "Attributes": {}}

        self.session_state['messages'].append(msg)
        # monitor attributes ======================================
        previous_attributes = {}
        try:
            del parsed_response['Attributes']['None']
        except:
            pass

        if parsed_response['Attributes'] not in ['None', None] and len(parsed_response['Attributes']) > 0:
            current_attributes, attribute_error, self.session_state = attribute_validator(previous_attributes,
                                                                                     parsed_response['Attributes'],
                                                                                     self.session_state)

            parsed_response['Attributes'] = current_attributes
            previous_attributes = parsed_response['Attributes']
            if attribute_error['Error']:
                return jsonify({"response": attribute_error['msg']})

        # check function ===========================================
        # buy_membership will be called form payment page.
        print(
            f"Attribute scores : {len([i for i in parsed_response['Attributes'].values() if i not in ['None', None]])} / {len(parsed_response['Attributes'])}")
        print(parsed_response['Attributes'])

        parsed_response['response'] = parsed_response['response'].split('. ')
        parsed_response['response_type'] = "txt"
        return jsonify(parsed_response)

