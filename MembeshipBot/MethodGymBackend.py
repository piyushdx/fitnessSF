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
        self.state_name=""
        self.zip_flag=""
        self.zip_state_name=""
        self.test_flag = False
        self.zip_code = ""
        self.first_name = ""
        self.last_name = ""
        self.email = ""
        self.address = "none"
        self.emergency_no = ""
        self.emergency_name = ""
        self.phone = ""
        self.dob= ""
        self.city =""
        self.person_flag = False
        self.phone_flag = False
        
        


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

    def fetch_details(self):
        print("fetching all details")
        return "fetching all details"
    def set_bot_persona(self):
        messages = [
            {"role": "system", "content": """You are the gym agent employed at Fitness SF gym. You help people in buying gym memberships. 
You talk to people like a human would talk to them. Like, start conversation by greeting the user, Ask them about their purpose to join the gym. 
 
To join online membership below fields are required:
Get the below details from the user in a natural flow with asking 1 field at a time.(STRICTLY FOLLOW THIS INFORMATION).
1. preferred Location: provide the gym location which best meets user's purpose of joining the gym.
        - Mid Market has amenitites: Full Weight Floor and Cardio Deck ,Olympic Lifting Platforms,Three Group Fitness Studios,Performance Training Center,Treadwall,Turf Zone.
        - Fillmore has amenitites: Full Weight Floor and Cardio Deck, Functional Training and Turf Zone, Olympic Lifting Platforms, Swimming Pool, Hot Tub.
        - Soma has amenitites:Large Weight and Cardio Floor, Olympic Lifting Platforms, Functional Training Area, Turf Zone.
        - Transbay has amenitites:15 Olympic Lifting Platforms, Three Group Fitness Studios, Athletic Training Center and Turf Zone, Stretching and Recovery Area.
        - Marin has amenitites: Indoor and Outdoor Gym, Functional Training Area and Turf Zone, Olympic Lifting Platforms, Large Weight Floor and Cardio Deck
        - Oakland has amenitites: Full Weight Floor and Cardio Deck, Olympic Lifting Platforms, Functional Training and Turf Area, Stretching Area, Group Fitness Studio
        - Castro has amenitites: Full Weight Floor and Cardio Deck, Functional Training and Turf Area, Olympic Lifting Platforms, Stretching/Recovery Area
        - Embarcadero has amenitites: Full Weight Floor and Cardio Deck, Olympic Lifting Platforms, Outdoor Turf, Functional Training Area, Stretching and Recovery Area

2. Ask user to select plan from below:
    If location is from: Embarcadero,Castro,Fillmore,mid market,soma,transbay then provide the plan as: 
            1. ALL GYM ACCESS - Access to all 8 Bay Area locations. Monthly recurring payment. price is $99.95 monthly.
    If location is Marin then provide the plan as:
            1. ALL GYM ACCESS (MARIN)-  Access to all 8 Bay Area locations. Monthly recurring payment. price is $99.95 monthly.
            2. MARIN ACCESS $69.95 - Single gym access. Monthly recurring membership. price is $69.95 monthly.
    If location is Oakland then provide the plan as:
            1. ALL GYM ACCESS (MARIN)-  Access to all 8 Bay Area locations. Monthly recurring payment. price is $99.95 monthly.
            2. Single gym access. Monthly recurring membership. price is $49.95 monthly.


3. Full Name 
4. Email
5. DOB
6. Resident Address 
7. City
8. State 
9. ZIP code
10. Phone Number
11. Emergency Contact Name
12. Emergency Contact Phone

Get the above details from the user in a natural flow with asking 1 field at a time. (STRICTLY FOLLOW THIS INFORMATION).
If any required fields's are still missing, ask them again in a natural flow with asking 1 field at a time (STRICTLY FOLLOW THIS INFORMATION).
At last Once the user provides all the necessary information, just respond with "I Got the info sending to DXARCIPIO".No need to ask for confirmation. (STRICTLY FOLLOW THIS Instruction).    
"""}]
        return messages

    def generate_response(self, prompt):
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
    def ask_function_Calling(self, messages):
        functions=[
            {
                "name": "provide_plan",
                "description": "This function should be called when user provides plan number or name of the plan or confirmation of the plan for the joining the gym.",
                "parameters": {
                    "type": "object",
                    "properties": {"plan": {"type": "string",
                                                "description": "it will be a confirmation or number or name of the plan for the gym."},
                                    },
                    "required": ["plan"],
                }
            },
        ]
        
        try:            
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
        self.plan_flag = False
        # if any(self.state_memory):
        #     print(self.memory.store_to_database(str(user),"MethodGym",str(self.state_memory[user])))
        
        if user in self.state_memory:
            self.state_memory.pop(user)

        print(f"############## I have cleared everything from Membership Joining Bot for user {user} .....")
        return jsonify({"status": "True"})

    def get_response(self, data):
        # locations = ["mid market","soma","marin","fillmore","oakland","castro","transbay","embarcadero"]
        
        user= "test"

        if user not in self.state_memory:
            self.test_flag = False           
            self.state_memory[user] = self.set_bot_persona()
            self.state_memory[user].append(
                {"role": "assistant", "content": "Hi, Welcome to Fitness SF Bot! What is your purpose to join the gym?"})
           
        print("history............................")
        print(self.state_memory[user])
        print("self.plan_flag:",self.plan_flag) 
        
        if self.plan_flag == False:
            self.state_memory[user].append({"role": "user", "content": f"{data['query']}"})
            
        print("self.state_memory[user]********************")
        print(self.state_memory[user])
        response = self.ask_function_Calling(self.state_memory[user])
        
        # print("*************************")
        # print(response)
        if response.choices[0].finish_reason == "stop":
            response1 = response.choices[0].message
            print("*************************")
            print(response1)
            if "dxarcipio" in response1['content'].lower():
                print("--------------------------------------------------------------")
                print(response1)
                self.first_name = str(self.first_name) if self.first_name is not None else ""
                self.last_name = str(self.last_name) if self.last_name is not None else ""
                self.email = str(self.email) if self.email is not None else ""
                self.dob = str(self.dob) if self.dob is not None else ""
                self.address = str(self.address) if self.address is not None else ""
                self.zip_code = str(self.zip_code) if self.zip_code is not None else ""
                self.phone  = str(self.phone ) if self.phone  is not None else ""
                
                data = "Name:" + self.first_name + self.last_name + " " +"Email:" + self.email + " " + "DOB:" + self.dob+ " " + "Address:" + self.address + " " + "Zip code:" + self.zip_code + " " + "Phone:"
                self.phone 
                return jsonify({'response': data, 'response_type': 'txt'})
            
        if self.plan_flag ==  True or response.choices[0].finish_reason == "function_call": 
            self.plan_flag = True
            
            if response.choices[0].finish_reason == "stop":
                anonymizer = PresidioReversibleAnonymizer(analyzed_fields=["PERSON","EMAIL_ADDRESS"])
                anonymizer.anonymize(data['query'])
                ppi_data = anonymizer.deanonymizer_mapping
                if ppi_data:
                        print(ppi_data)
                        if 'PERSON' in ppi_data and contains_numeric_value(data) == False:
                            
                            full_name = next(iter(ppi_data['PERSON'].values()), None)
                            if full_name:
                                if self.person_flag == False:
                                    self.first_name = full_name.split(" ")[0]
                                    self.last_name = full_name.split(" ")[1]
                                    self.person_flag = True
                                elif self.person_flag == True:
                                    self.emergency_name = full_name
                            
                            self.state_memory[user].append({"role": "user", "content": f"{'user has provided the name.'}"})
                            
                        elif 'EMAIL_ADDRESS' in ppi_data:
                            self.email = next(iter(ppi_data['EMAIL_ADDRESS'].values()), None)
                            self.state_memory[user].append({"role": "user", "content": f"{'user has provided the email adress.'}"})
                        else:
                            ppi_data = {}
                if not ppi_data :
                    self.dob,age = find_DOB(data['query'])
                    print("dob:",self.dob,age)
                    if self.dob is not None:
                        self.state_memory[user].append({"role": "user", "content": f"{f'User has provided the necessary information.'}"})
                    else:
                        AddressNumber,StreetName,StreetNamePostType,OccupancyType,OccupancyIdentifier,PlaceName,StateName,ZipCode,city = find_address(data['query'])
                        self.zip_state_name = StateName
                        self.zip_code = ZipCode
                        AddressNumber = str(AddressNumber) if AddressNumber is not None else ""
                        StreetName = str(StreetName) if StreetName is not None else ""
                        StreetNamePostType = str(StreetNamePostType) if StreetNamePostType is not None else ""
                        OccupancyType = str(OccupancyType) if OccupancyType is not None else ""
                        OccupancyIdentifier = str(OccupancyIdentifier) if OccupancyIdentifier is not None else ""
                        PlaceName = str(PlaceName) if PlaceName is not None else ""
                        if self.address == "none":
                            self.address = AddressNumber+StreetName+StreetNamePostType+OccupancyType+OccupancyIdentifier+PlaceName
                        print("city:",city)
                        print("address_info:",AddressNumber,StreetName,StreetNamePostType,OccupancyType,OccupancyIdentifier,PlaceName)
                        print("zip_code:",ZipCode)
                        print("self.zip_state_name :",self.zip_state_name)
                        
                        self.state_memory[user].append({"role": "user", "content": f"{'user has provided the resident adress.'}"})
                        
                        if city is not None:
                            self.state_memory[user].append({"role": "user", "content": f"{'user has provided the city name.'}"})
                        if self.zip_code is not None:
                            self.state_memory[user].append({"role": "user", "content": f"{'user has provided the zip code.'}"})
                        if self.zip_state_name is not None:
                            self.state_memory[user].append({"role": "user", "content": f"{'user has provided the state name.'}"})
                            
                        if self.zip_state_name is not None or self.state_name is not None :
          
                            phone = find_phone(data['query'],self.state_name,self.zip_flag,self.zip_state_name)
                            if phone is not None:
                                if self.phone_flag == False:
                                    self.phone = phone
                                elif self.phone_flag == True:
                                    self.emergency_no = phone
                                print("phone:",self.phone,self.emergency_no)
                                
                                self.state_memory[user].append({"role": "user", "content": f"{'user has provided the phone number.'}"})
                                self.phone_flag = True 
                                
                # else:
                #     self.state_memory[user].append({"role": "user", "content": f"{'user has provided the ne neccesary details.'}"})
                            
            if response.choices[0].finish_reason == "function_call":   
                if response.choices[0].message.function_call.name == "provide_plan":
                        self.state_memory[user].append({"role": "user", "content": f"{data['query']}"})
                        
            response = self.generate_response(self.state_memory[user])
            response1 = response.choices[0].message
            self.state_memory[user].append({"role": "assistant", "content": f"{response1['content']}"})  
            return jsonify({'response': response1['content'], 'response_type': 'txt'})
                                    
        if self.plan_flag == False:    
            response = self.generate_response(self.state_memory[user])
            response1 = response.choices[0].message
            self.state_memory[user].append({"role": "assistant", "content": f"{response1['content']}"})  
            return jsonify({'response': response1['content'], 'response_type': 'txt'})


