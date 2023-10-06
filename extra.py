import spacy
import pyap
from uszipcode import SearchEngine
import re
import phonenumbers
import us
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
from nameparser import HumanName
from geotext import GeoText
import geograpy
nlp = spacy.load("en_core_web_sm")

def find_address(text):
    addresses = pyap.parse(text, country='US')
    print(addresses)
    for address in addresses:
            info = address.as_dict()
            address_info = info['full_street']
            postal_code = info['postal_code']
    if len(addresses) > 0:
        print(address_info,postal_code)
        return address_info,postal_code
    else:
        return "",""
            
def is_valid_zip_code(zip_code):
    search = SearchEngine()
    result = search.by_zipcode(zip_code)
    if result and result.zipcode:
        print("state:",result.state)
        return True,result.zipcode,result.state
    else:
        return False,"",""

def find_state_name(text):
    # doc = nlp(text)
    # state_names = ""
    # for ent in doc.ents:
    #     if ent.label_ == "GPE":
    #         state_names = ent.text
    # if not state_names:
    #     return None
    # else:
    #     print("State Names:", state_names)
    #     return state_names
    for state in us.STATES:
        # print(text.lower())
        # print(state.name.lower())
        if state.name.lower() in text.lower():
            state_names = state.name
            print(state.name.lower())
            return state_names
            
        # elif state.abbr.lower() in text:
        #     state_names = state.abbr
        #     return state_names
        
    return None
            
    
    
def find_phone(text,state_name,zip_flag,zip_state_name):
    x = None
 
    if state_name and text.isalpha():
        state = us.states.lookup(state_name)
        region = state.abbr
        x = phonenumbers.parse(text, region)
    elif zip_flag and text.isalpha():
        x = phonenumbers.parse(text, zip_state_name)
    if x is not None:
        if phonenumbers.is_possible_number(x):
            number = phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.NATIONAL)
            print("number:",number)
            return number
        else:
            return "Enter Valid phone number"
    else:
        phone_number_pattern = r'\b(?:\d{3}[-\s.]?)?\d{3}[-\s.]?\d{4}\b'
        numbers = re.findall(phone_number_pattern, text)
        if numbers:
            number = numbers[0]
            print("number:",number)
            return number
        else:
            return "Enter Valid phone number"
               
def find_email(text):
    try:
        emailinfo = validate_email(text,check_deliverability=False)
        email = emailinfo.normalized
        print("email:",email)
        return email 
    except EmailNotValidError as e:
        return "Enter Valid email address"

def find_DOB(text):
    try:
        # Attempt to parse the DOB string
        dob = datetime.strptime(text, "%d %B %Y")
        if dob.day is None or dob.month is None or dob.year is None:
            return "Enter Valid DOB",""
        else:
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            print("age:",age)
            dob = dob.date()
            return dob,age
    except ValueError:
        return "Enter Valid DOB",""
    
def find_name_info(text):
    name_info = HumanName(text)
    name = name_info.as_dict()
    first_name = name['first']
    last_name = name['last']
    print(first_name,last_name)
    return first_name,last_name


def find_city(text):
    
    places = geograpy.get_geoPlace_context(text = text.title())
    print("*****")
    print(places.cities)
    places = GeoText(text.title())
    print("citi:",places.cities)

def main(text):
    dob = ""
    age = ""
    address_info,postal_code = find_address(text)
    zip_flag,zip_code,zip_state_name = is_valid_zip_code(text)
    state_name = find_state_name(text)
    print("state_name***:",state_name)
    phone = find_phone(text,state_name,zip_flag,zip_state_name)
    email = find_email(text)
    city = find_city(text)
    if text.isalpha() and len(text) > 4:
        dob,age = find_DOB(text)

    first_name,last_name = find_name_info(text)
    
    print(address_info,city,zip_code,state_name,phone,email,dob,age,first_name,last_name)
    return address_info,city,zip_code,state_name,phone,email,dob,age,first_name,last_name
    
text = "i live in san diego"

# from presidio_anonymizer import AnonymizerEngine
# from presidio_anonymizer.entities import RecognizerResult, OperatorConfig
# from presidio_analyzer import AnalyzerEngine
# engine = AnonymizerEngine()

# result = engine.anonymize(
#     text="my name is john doe. I live at 2443 Sierra Nevada Road, Mammoth Lakes CA 93546. my number is 8232866. my email id is fpankti@gmail.com. my dob is 15/08/99.",
#     analyzer_results=[
#         RecognizerResult(entity_type="PERSON", start=11, end=15, score=0.8),
#         RecognizerResult(entity_type="LOCATION", start=17, end=27, score=0.8),
#         RecognizerResult(entity_type="PHONE_NUMBER", start=20, end=27, score=0.8),
#         RecognizerResult(entity_type="DATE_TIME", start=20, end=27, score=0.8),
#         RecognizerResult(entity_type="EMAIL_ADDRESS", start=20, end=27, score=0.8),
    
#     ],
#     # operators={"PERSON": OperatorConfig("replace", {"new_value": "PERSON"}),"LOCATION": OperatorConfig("replace", {"new_value": "LOCATION"})
#     # ,"PHONE_NUMBER": OperatorConfig("replace", {"new_value": "PHONE_NUMBER"}),"DATE_TIME": OperatorConfig("replace", {"new_value": "DATE_TIME"}),
#     # "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "EMAIL_ADDRESS"})}
    
    
# )

# print(result)

# configuration = {
#     "nlp_engine_name": "spacy",
#     "models": [{"lang_code": "en", "model_name": "en_core_web_md"}],
# }

# from presidio_analyzer import AnalyzerEngine
# from presidio_analyzer.nlp_engine import NlpEngineProvider
# # Create NLP engine based on configuration
# provider = NlpEngineProvider(nlp_configuration=configuration)
# nlp_engine = provider.create_engine()
# # the languages are needed to load country-specific recognizers 
# # for finding phones, passport numbers, etc.
# analyzer = AnalyzerEngine(nlp_engine=nlp_engine,
#                           supported_languages=["en"])


# example_text = "my name is john doe. I live at 2443 Sierra Nevada Road, Mammoth Lakes CA 93546. my number is 8232866. my email id is fpankti@gmail.com. my dob is 15/08/99"
# # language is a required parameter. So if you don't know 
# # the language of each particular text, use language detector
# results = analyzer.analyze(text=example_text,
#                            language='en')
# for res in results:
#     print(res)
    
    
# from presidio_anonymizer import AnonymizerEngine
# anonymizer = AnonymizerEngine()
# anonymized_text = anonymizer.anonymize(text=example_text, analyzer_results=results).text
# print(anonymized_text)

from langchain_experimental.data_anonymizer import PresidioAnonymizer
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer

anonymizer = PresidioReversibleAnonymizer(analyzed_fields=["PERSON","EMAIL_ADDRESS"])
# anonymizer = PresidioAnonymizer(analyzed_fields=["PERSON","LOCATION","PHONE_NUMBER","DATE_TIME","EMAIL_ADDRESS"])

text =  "doe"
a = anonymizer.anonymize(text)
# print(anonymizer.anonymizer_mapping)
# print(anonymizer.deanonymize(text))
print(anonymizer.deanonymizer_mapping)

ppi_data = anonymizer.deanonymizer_mapping
# print(ppi_data['PERSON'])
# print(ppi_data['PHONE_NUMBER'])
# print(ppi_data['DATE_TIME'])
# print(ppi_data['EMAIL_ADDRESS'])


