import spacy
import pyap
from uszipcode import SearchEngine
import re
import phonenumbers
import us
from email_validator import validate_email, EmailNotValidError
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer
from datetime import datetime
from nameparser import HumanName
from geotext import GeoText
import geograpy
from spellchecker import SpellChecker
import dateparser
from datetime import datetime
import usaddress
from geotext import GeoText


nlp = spacy.load("en_core_web_sm")

# def find_address(text):
#     addresses = pyap.parse(text, country='US')
#     print(addresses)
#     for address in addresses:
#             info = address.as_dict()
#             address_info = info['full_street']
#             postal_code = info['postal_code']
#             city = info['city']
#     if len(addresses) > 0:
#         print(address_info,postal_code)
#         return address_info,postal_code,city
#     else:
#         return None,None,None


def find_address(text):

    data = usaddress.tag(text)
    print(data)
    inner_ordered_dict = data[0]

    AddressNumber = inner_ordered_dict.get("AddressNumber", None)
    StreetName = inner_ordered_dict.get("StreetName", None)
    StreetNamePostType = inner_ordered_dict.get("StreetNamePostType", None)
    OccupancyType = inner_ordered_dict.get("OccupancyType", None)
    OccupancyIdentifier = inner_ordered_dict.get("OccupancyIdentifier", None)
    PlaceName = inner_ordered_dict.get("PlaceName", None)
    StateName = inner_ordered_dict.get("StateName", None)
    ZipCode = inner_ordered_dict.get("ZipCode", None)
    places = GeoText(text.title())
    if len(places.cities) > 0:
        city = places.cities[0]
    else:
        city = None
    return AddressNumber,StreetName,StreetNamePostType,OccupancyType,OccupancyIdentifier,PlaceName,StateName,ZipCode,city
    
            
def is_valid_zip_code(zip_code):
    search = SearchEngine()
    result = search.by_zipcode(zip_code)
    if result and result.zipcode:
        # print("state:",result.state)
        return True,result.zipcode,result.state
    else:
        return False,None,None

def find_state_name(text):
    for state in us.STATES:
        if state.name.lower() in text.lower():
            state_names = state.name
            print(state.name.lower())
            return state_names
    return None
            
def find_phone(text,state_name,zip_flag,zip_state_name):
    x = None
    if state_name and text.isalpha():
        state = us.states.lookup(state_name)
        region = state.abbr
        try:
            x = phonenumbers.parse(text, region)
        except phonenumbers.phonenumberutil.NumberParseException as e:
            return None
    elif zip_flag and text.isalpha():
        try:
            x = phonenumbers.parse(text, zip_state_name)
        except phonenumbers.phonenumberutil.NumberParseException as e:
            return None
    if x is not None:
        if phonenumbers.is_possible_number(x):
            number = phonenumbers.format_number(x, phonenumbers.PhoneNumberFormat.NATIONAL)
            # print("number:",number)
            return number
        else:
            return None
    else:
        phone_number_pattern = r'\b(?:\d{3}[-\s.]?)?\d{3}[-\s.]?\d{4}\b'
        numbers = re.findall(phone_number_pattern, text)
        if numbers:
            number = numbers[0]
            # print("number:",number)
            return number
        else:
            return None
        
        
def find_DOB(text):
    # Define regular expression patterns for various date formats
    dob_patterns = [
        r"(\d{1,2}[-/ ]\d{1,2}[-/ ]\d{2,4})",  # Matches various date formats with different delimiters
        r"(\d{1,2} [A-Za-z]+ (?:\d{2,4}|\d{1,2}))",  # Matches "15 August 99" or "15 Aug 1999" or "15 Aug 9"
        r"(\d{1,2}/\d{1,2}/(?:\d{2,4}|\d{1,2}))",  # Matches "15/08/99" or "15/08/1999" or "15/8/9"
    ]

    for dob_pattern in dob_patterns:
        dob_match = re.search(dob_pattern, text)
        if dob_match:
            dob_text = dob_match.group(1)

            # Clean up the date text by replacing spaces with dashes
            dob_text = dob_text.replace(" ", "-")

            # Check if the year has two digits and determine the century
            date_parts = dob_text.split("-")
            print(date_parts)
            if len(date_parts) > 1 and len(date_parts[2]) == 2:
                # Determine the century based on a threshold (e.g., 70 as the cutoff year)
                current_year = datetime.today().year % 100  # Get the last two digits of the current year
                if int(date_parts[2]) <= current_year:
                    century = 2000  # Assume years between 00-70 belong to the 21st century
                else:
                    century = 1900  # Assume years between 71-99 belong to the 20th century

                # Reconstruct the date with the determined century in "dd-mm-yyyy" format
                dob_text = f"{date_parts[0]}-{date_parts[1]}-{century + int(date_parts[2])}"

            try:
                # Attempt to parse the matched DOB text
                parsed_date = dateparser.parse(dob_text)
                dob_text = parsed_date.strftime("%d-%m-%Y")
                dob = datetime.strptime(dob_text, "%d-%m-%Y")  # Assuming dd-mm-yyyy format
                today = datetime.today()

                # Calculate age based on the parsed DOB
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

                if today < dob.replace(year=today.year):
                    return None, None  # DOB in the future

                return dob.strftime("%d-%m-%Y"), age

            except ValueError:
                return None, None  # Not a valid DOB format or missing components

    return None, None  # No valid DOB format found in the text
               
# def find_email(text):
#     try:
#         emailinfo = validate_email(text,check_deliverability=False)
#         email = emailinfo.normalized
#         print("email:",email)
#         return email 
#     except EmailNotValidError as e:
#         return "Enter Valid email address"

# def find_DOB(text):
#     try:
#         # if dob.day is None or dob.month is None or dob.year is None:
#         #     return None, None

#         if not any(char.isdigit() for char in text):
#             return False,False
        
#         dob = datetime.strptime(text, "%d %B %Y")
#         print("dob")
#         print(dob)
#         today = datetime.today()
#         age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

#         if today < dob.replace(year=today.year):
#             return None, None
#         return  dob.date(), age

#     except ValueError:
#         return None,None
    
    
# def find_DOB(text):
#     try:
#         # Define regular expression patterns for various date formats
#         dob_patterns = [
#             r"(\d{1,2} [A-Za-z]+ \d{4})",  # Matches "15 August 1999"
#             r"(\d{1,2}-\d{1,2}-\d{4})",  # Matches "15-08-1999"
#             r"(\d{1,2} [A-Za-z]+ \d{2})",  # Matches "15 August 99"
#             r"(\d{1,2}-\d{1,2}-\d{2})",  # Matches "15 August 1999"
#         ]

#         for dob_pattern in dob_patterns:
#             dob_match = re.search(dob_pattern, text)
#             if dob_match:
#                 dob_text = dob_match.group(1)

#                 # Clean up the date text by replacing spaces with dashes
#                 dob_text = dob_text.replace(" ", "-")

#                 # Parse the matched DOB text
#                 dob = datetime.strptime(dob_text, "%d %B %Y")  # Assuming dd-mm-yyyy format
#                 today = datetime.today()

#                 # Calculate age based on the parsed DOB
#                 age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

#                 if today < dob.replace(year=today.year):
#                     return None, None  # DOB in the future

#                 return dob.date(), age

#         return None, None  # No valid DOB format found in the text

#     except ValueError:
#         return None, None  # Not a valid DOB format or missing components
    
# def find_DOB(text):
#     # Define regular expression patterns for various date formats
#     dob_patterns = [
#         r"(\d{1,2}[-/ ]\d{1,2}[-/ ]\d{2,4})",  # Matches various date formats with different delimiters
#         r"(\d{1,2} [A-Za-z]+ \d{4})", 
#         r"(\d{1,2} (?:\d{2,4}|\w+) \d{2,4})",# Matches "15 August 1999"
#     ]

#     for dob_pattern in dob_patterns:
#         dob_match = re.search(dob_pattern, text)
#         if dob_match:
#             dob_text = dob_match.group(1)

#             # Clean up the date text by replacing spaces with dashes
#             dob_text = dob_text.replace(" ", "-")

#             # Check if the year has two digits and determine the century
#             date_parts = dob_text.split("-")
#             if len(date_parts[2]) == 2:
#                 # Determine the century based on a threshold (e.g., 70 as the cutoff year)
#                 current_year = datetime.today().year % 100  # Get the last two digits of the current year
#                 if int(date_parts[2]) <= current_year:
#                     century = 2000  # Assume years between 00-70 belong to the 21st century
#                 else:
#                     century = 1900  # Assume years between 71-99 belong to the 20th century

#                 # Reconstruct the date with the determined century in "dd-mm-yyyy" format
#                 dob_text = f"{date_parts[0]}-{date_parts[1]}-{century + int(date_parts[2])}"

#             try:
#                 # Attempt to parse the matched DOB text
#                 dob = datetime.strptime(dob_text, "%d-%m-%Y")  # Assuming dd-mm-yyyy format
#                 today = datetime.today()

#                 # Calculate age based on the parsed DOB
#                 age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

#                 if today < dob.replace(year=today.year):
#                     return None, None  # DOB in the future

#                 return dob.strftime("%d-%m-%Y"), age

#             except ValueError:
#                 return None, None  # Not a valid DOB format or missing components

#     return None, None  # No valid DOB format found in the text
    
    
# def find_name_info(text):
#     name_info = HumanName(text)
#     name = name_info.as_dict()
#     first_name = name['first']
#     last_name = name['last']
#     print(first_name,last_name)
#     return first_name,last_name


def find_city(text):
    
    places = geograpy.get_geoPlace_context(text = text.title())
    print("*****")
    print(places.cities)
    places = GeoText(text.title())
    print("citi:",places.cities)
    
    
def find_spelling(text):
    correct_names = ["mid market", "soma", "marin", "fillmore", "oakland", "castro", "transbay", "embarcadero"]
    spell = SpellChecker()
    words = text.split()
    
    # Find and correct misspelled words
    corrected_words = []
    for word in words:
        # Check if the word is a correct name, if so, keep it as is
        if word.lower() in [name.lower() for name in correct_names]:
            corrected_words.append(word)
        else:
            # If not a correct name, use the spell checker to correct it
            corrected_word = spell.correction(word)
            if corrected_word is not None:
                corrected_words.append(corrected_word)  # Only append non-None corrections
    
    # Reconstruct the corrected user input
    corrected_input = " ".join(corrected_words)
    return corrected_input





def main(text):
    dob = ""
    age = ""
    anonymizer = PresidioReversibleAnonymizer(analyzed_fields=["PERSON","EMAIL_ADDRESS"])
    anonymizer.anonymize(text)
    ppi_data = anonymizer.deanonymizer_mapping

    if ppi_data['PERSON']:
        full_name = next(iter(ppi_data['PERSON'].values()), None)
        first_name = full_name.split(" ")[0]
        last_name = full_name.split(" ")[1]
        fake_info = ppi_data['PERSON']
        fake_name = [name for name in fake_info.keys()][0]
        fake_first_name = fake_name.split(" ")[0]
        fake_last_name = fake_name.split(" ")[1]
        
        print("full_name:",first_name,last_name,fake_first_name,fake_last_name)
        return 
    elif ppi_data['EMAIL_ADDRESS']:
        email = next(iter(ppi_data['EMAIL_ADDRESS'].values()), None)
        print("email",email)
    
    address_info,postal_code = find_address(text)
    zip_flag,zip_code,zip_state_name = is_valid_zip_code(text)
    state_name = find_state_name(text)
    phone = find_phone(text,state_name,zip_flag,zip_state_name)
    city = find_city(text)
    if text.isalpha() and len(text) > 4:
        dob,age = find_DOB(text)

    # email = find_email(text)
    # first_name,last_name = find_name_info(text)
    
    # print(address_info,city,zip_code,state_name,phone,dob,age,first_name,last_name)
    return address_info,city,zip_code,state_name,phone,dob,age,first_name,last_name
    
# text = "john doe n."

# dob,age = find_DOB(text)
# print(dob,age)

# if dob == None:
#     print("Enter valid DOB")
# elif dob:
#     print(dob,age)
# else:
#     pass
# main(text)


# phone = find_phone(text,state_name,zip_flag,zip_state_name)
# text = "8232866"
# if "+" not in text:
#     text = "+" + text
    
# x = phonenumbers.parse(text, None)
# print(phonenumbers.is_possible_number(x))
# print(x)

# print(ppi_data['PERSON'])
# print(ppi_data['PHONE_NUMBER'])
# print(ppi_data['DATE_TIME'])
# print(ppi_data['EMAIL_ADDRESS'])







# # Example usage:
# text = "my dob is 08/15/99"
# print(find_DOB(text))

# text = "john doe"
# print(len(text.split()))

# import usaddress
# addr='2443 Sierra Nevada Road,mclean, Mammoth Lakes CA 93546'
# AddressNumber,StreetName,StreetNamePostType,OccupancyType,OccupancyIdentifier,PlaceName,StateName,ZipCode,city = find_address(addr)
# print(AddressNumber,StreetName,StreetNamePostType,OccupancyType,OccupancyIdentifier,PlaceName,StateName,ZipCode,city)



def contains_numeric_value(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                # Recursively check nested dictionaries
                if contains_numeric_value(value):
                    return True
            elif isinstance(value, str) and any(char.isdigit() for char in value):
                return True
    return False

# Example data
# data = {'PERSON': {'Melissa Walker': '4439 Gale Street'}}

# # Check if the dictionary contains any numeric values
# if contains_numeric_value(data):
#     print("The dictionary contains numeric values.")
# else:
#     print("The dictionary does not contain numeric values.")


ppi_data = {'PERSON': {'Joseph Stone': 'Gale john'}}
full_name = next(iter(ppi_data['PERSON'].values()), None)
first_name = full_name.split(" ")[0]
last_name = full_name.split(" ")[1]




    