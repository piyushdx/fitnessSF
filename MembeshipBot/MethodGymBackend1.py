from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import threading
import openai
import re
import os
from geopy.distance import geodesic
from .utils.utils import attribute_validator, output_parser, format_prompt, NER_prompt
from .information_extraction import *
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer

prompt1 = [{"role": "system", "content": """You are the gym agent employed at Fitness SF gym. You help people in buying gym memberships and canceling memberships. 
You talk to people like a human would talk to them.
1. Suggest the location of gym based on user's purpose of joining the gym: 
If user's purpose is to train for olympics or he is an athelete then suggest that Transbay is the best gym for him. It has following amenties:15 Olympic Lifting Platforms, Three Group Fitness Studios, Athletic Training Center and Turf Zone,Stretching and Recovery Area.
If user's purpose is for fitness, wellness or strength training then you can suggest following gyms : Mid Market, Soma, Marin, Oakland, Castro, Embarcadero. These gyms have following amenities: Cardio, Weight training, Turf Zone, Stretching Area, Olympic Lifting Platfroms.
If user wants to do swimming then suggest Fillmore is the best gym for him. It has following amenties: Full Weight Floor and Cardio Deck, Functional Training and Turf Zone,Olympic Lifting Platforms,Swimming Pool,Hot Tub.
"""}]
    
prompt2 = [{"role": "system", "content": """You are the gym agent employed at Fitness SF gym. You help people in buying gym memberships and canceling memberships. 
You talk to people like a human would talk to them. Get following details for buying online membership:
3. Full name 
4. DOB
5. Email
6. Phone Number
7. Full Address
8. City
9. State 
10. ZIP code
11. Emergency Contact Name
12. Emergency Contact Phone

Get the above details from the user in a natural flow with asking 1 field at a time.
In the subsequent conversations, remember your goal is to be polite and if user has issues with our services then try to convience them that we will improve our services soon.
If any required fields's are still missing, ask them again in a natural flow with asking 1 field at a time (STRICTLY FOLLOW THIS INFORMATION).

Once you have all the required fields's, ask for a final confirmation from the user to validate the given details (STRICTLY FOLLOW THIS INFORMATION).
"""}]

class MembershipBot:

    def __init__(self, azure_openai_engine,memory):
        self.azure_openai_engine = azure_openai_engine
        self.state_memory = {}
        self.memory = memory
        self.latitude  = ""
        self.longitude  = ""
        self.closest_location = ""
        self.plan_flag = False


    def fetch_closest_location(self,lat,long):

        # Coordinates of San Francisco Bay
        # current_coords = (lat, long)
        current_coords = (37.901409, -122.322800)
        

        # Coordinates of the locations to choose from
        locations = {
            'Fillmore': (34.400669, -118.913757),
            'Mid Market': (50.352980, -4.453370),
            'Soma': (13.442380, -15.538710),  # San Francisco Bay (current location)
            'Transbay': (39.232630, -76.672260),
            'Marin': (38.083405, -122.763306),
            'Oakland': (37.804363, -122.271111),
            'Castro': (37.760906, -122.435005),
            'Embarcadero': (22.250080, -105.431442)
        }

        # Calculate distances to all locations and find the closest one
        # closest_location = None
        min_distance = float('inf')

        for location, coords in locations.items():
            distance = geodesic(current_coords, coords).kilometers
            if distance < min_distance:
                min_distance = distance
                self.closest_location = location

        print(f"The closest location to San Francisco Bay is {self.closest_location} ({min_distance} km).")

    def set_bot_persona(self):
        messages = [
            {"role": "system", "content": """You are the gym agent employed at Fitness SF gym. You help people in buying gym memberships and canceling memberships. 
You talk to people like a human would talk to them. Like, start conversation by greeting the user, Ask them about their purpose to join the gym.        
""".replace("<location>",self.closest_location)}]
        return messages

    def ask_function_Calling(self, prompt):
        try:

            response = openai.ChatCompletion.create(engine=self.azure_openai_engine,
                                                    messages=prompt,
                                                    temperature=0.7)
            # msg = response.choices[0].message
            msg = response
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
    def generate_response(self, messages):
        try:
            functions=[
                {
                    "name": "provide_plan",
                    "description": "This function is for buying membership. it should be called when user provides plan for the joining the gym.",
                    "parameters": {
                        "type": "object",
                        "properties": {"plan": {"type": "string",
                                                    "description": "it will be a number or name of the plan for the gym."},
                                        },
                        "required": ["plan"],
                    }
                },
                {
                    "name": "provide_location",
                    "description": "This function is for buying membership. it should be called when user provides purpose for the joining the gym.",
                    "parameters": {
                        "type": "object",
                        "properties": {"purpose": {"type": "string",
                                                    "description": "it will be purpose of the gym joining the gym."},
                                        },
                        "required": ["purpose"],
                    }
                },
                
            ]
            response = openai.ChatCompletion.create(engine=self.azure_openai_engine,
                                                    messages=messages,
                                                    temperature=0.7,
                                                    functions = functions,
                                                    function_call="auto")
            # msg = response.choices[0].message
            msg = response
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

    def clear_cache(self,data):
        # user = data['email']
        
        user= "test"
        if any(self.state_memory):
            print(self.memory.store_to_database(str(user),"MethodGym",str(self.state_memory[user])))
        
        if user in self.state_memory:
            self.state_memory.pop(user)

        print(f"############## I have cleared everything from Membership Joining Bot for user {user} .....")
        return jsonify({"status": "True"})

    def get_response(self, data):
        # user = data['email']
        user= "test"
        # user = data['user']
        if data['location'] == True:
            location = data['query']
            self.latitude = data['query'].split("+")[0]
            self.longitude = data['query'].split("+")[1]
            # print(self.latitude,self.longitude)
            self.fetch_closest_location(self.latitude,self.longitude)

        if user not in self.state_memory:
            # self.memory.store_to_chatdb(str(user),"MethodGym")
            
            self.state_memory[user] = self.set_bot_persona()
            self.state_memory[user].append(
                {"role": "assistant", "content": "Hi, Welcome to Fitness SF Bot! What is your purpose to join the gym?"})
            
            self.state_memory[user].append({"role": "user", "content": f"{data['query']}"})
                    
        response = self.generate_response(self.state_memory[user])
        response1 = response.choices[0].message
            
        if response.choices[0].finish_reason == "function_call": 
            if response.choices[0].message.function_call.name == "provide_location":
                self.state_memory[user] = prompt1
                response = self.ask_function_Calling(self.state_memory[user])
                self.state_memory[user].append({"role": "user", "content": f"{data['query']}"})
                
                
          
          
        # if not self.plan_flag:
        #     self.state_memory[user].append({"role": "user", "content": f"{data['query']}"})    
        #     response = self.generate_response(self.state_memory[user])
        #     print(response)
        #     if response.choices[0].finish_reason == "stop":
        #         response1 = response.choices[0].message
        #         self.state_memory[user].append({"role": "user", "content": f"{data['query']}"})
        #         self.state_memory[user].append({"role": "assistant", "content": f"{response1['content']}"})
        #     return jsonify({'response': response1['content'], 'response_type': 'txt'})
          
        # if response.choices[0].finish_reason == "function_call":
        #     self.plan_flag = True
        #     self.state_memory[user] = prompt  
            
        # if self.plan_flag == True :
        #     # if response.choices[0].message.function_call.name == "join_membership":
        #     print("buy membership")
        #     self.plan_flag = True
        #     # response1 = response.choices[0].message
        #     response = self.ask_function_Calling(self.state_memory[user])
        #     print(response)
        #     response1 = response.choices[0].message
        #     return jsonify({'response': response1['content'], 'response_type': 'txt'})
            
                
        
            
            
        
            
        
        
        
        
        
        # data = main(data['query'])
        
        # anonymizer = PresidioReversibleAnonymizer(analyzed_fields=["PERSON","EMAIL_ADDRESS"])
        # anonymizer.anonymize(data['query'])
        # ppi_data = anonymizer.deanonymizer_mapping
        # print(ppi_data)

        # if ppi_data:
        #     if ppi_data['PERSON']:
        #         full_name = next(iter(ppi_data['PERSON'].values()), None)
        #         first_name = full_name.split(" ")[0]
        #         last_name = full_name.split(" ")[1]
        #         fake_info = ppi_data['PERSON']
        #         fake_name = [name for name in fake_info.keys()][0]
        #         fake_first_name = fake_name.split(" ")[0]
        #         fake_last_name = fake_name.split(" ")[1]
        #         print("full_name:",first_name,last_name,fake_first_name,fake_last_name)
                
        #         self.state_memory[user].append({"role": "user", "content": f"{'user provided its full name.'}"})
        #         response = self.generate_response(self.state_memory[user])
                
                
                
        #     elif ppi_data['EMAIL_ADDRESS']:
        #         email = next(iter(ppi_data['EMAIL_ADDRESS'].values()), None)
        #         print("email",email)
    
        # else:

        
        
        # print("******")
        # print(response)
        # if response.choices[0].finish_reason == "function_call":
        #     if response.message.function_call.name == "join_membership":
        #         print("buy membership")
        #         self.plan_flag = True
                
        # if self.plan_flag == True:
                
                            # anonymizer = PresidioReversibleAnonymizer(analyzed_fields=["PERSON","EMAIL_ADDRESS"])
            # anonymizer.anonymize(text)
            # ppi_data = anonymizer.deanonymizer_mapping
            
            # if ppi_data['PERSON']:
            #     full_name = next(iter(ppi_data['PERSON'].values()), None)
            #     first_name = full_name.split(" ")[0]
            #     last_name = full_name.split(" ")[1]
            #     print("full_name:",first_name,last_name)
              
            # elif ppi_data['EMAIL_ADDRESS']:
            #     email = next(iter(ppi_data['EMAIL_ADDRESS'].values()), None)
            #     print("email",email)
        # else:
        #     response = response.choices[0].message
        #     self.state_memory[user].append({"role": "assistant", "content": f"{response['content']}"})
            

                
            # elif find_DOB(text)
    

        if "http://18.144.92.141:7002/Payment" in response:
            print("Going for function call.....")
            state_tmp = self.state_memory[user].copy()
            state_tmp.append({"role": "user", "content": f"{NER_prompt}"})
            ner_attributes = self.generate_response(state_tmp)
            ner_attributes = output_parser(ner_attributes['content'])
            if ner_attributes != "Parsing Error":
                if len([i for i in ner_attributes.values() if i not in ['None', None]]) == len(ner_attributes):
                    print(f"Function called to buy membership : {ner_attributes}")

        return jsonify({'response': response1['content'], 'response_type': 'txt'})
