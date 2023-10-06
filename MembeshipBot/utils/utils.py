import phonenumbers
from email_validator import validate_email, EmailNotValidError
import json
import re


format_prompt = """The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "\`\`\`json" and "\`\`\`":
            ```json
            {
                "Task": string  // task to which it belongs to. keep it 'None' if it doesn't belong to any of the Task.
                "response": string  // it contains the bot response to the user.
                "Attributes" : JSON // give relevant answer for each required fields. keep the answer as 'None' if you don't find any relevant one.
            }
            ```
            user question :"""

NER_prompt = """Based on previous user conversation, extract following fields
The output should be a markdown code snippet formatted in the following schema, including the leading and trailing "\`\`\`json" and "\`\`\`":
```json
{    
    "preferred_location": string  // it can be one among [California, Leonardtown, Dale City]
    "membership_plan": string  // it can be one among [Free trial, METHOD 1, METHOD +, METHOD PREMIER]
    "first_name": string  // user first name
    "last_name": string  // user last name
    "email": string  // user email address
    "phone_number": string  // user phone number
    "how_did_you_hear_about_us": string  // it can be one among [Social Media, Online Search, Influencer, Referral, Community Event, Other]
}
```
Note : keep the answer as 'None' if you don't find any relevant one.
"""

def attribute_validator(previous_attributes, current_attributes, session_state):
    response = {"Error": False, "msg": ""}
    # phone validation
    phone_attributes = ['phoneNumber', 'emergencyContactPhone']
    for i in current_attributes:
        if i in phone_attributes and current_attributes[i] not in ['None', None] and \
                (i not in previous_attributes or previous_attributes[i] != current_attributes[i]):
            print("***** Phone validation is executed....")
            try:
                my_number = phonenumbers.parse(current_attributes[i])
                if phonenumbers.is_valid_number(my_number):
                    print(">>> Correct")
                    # return True
                else:
                    del session_state['messages'][-1]
                    session_state['messages'].append(
                        {"role": "assistant", "content": f"'{current_attributes[i]}' is invalid,"
                                                         f" please provide valid {i}."})
                    response['Error'] = True
                    response['msg'] = f"'{current_attributes[i]}' is invalid, please provide valid {i}. " \
                                      f"Please provide country code, if you haven't provided."
                    current_attributes[i] = 'None'
                    print(">>> In Correct")
                    # return False
            except:
                del session_state['messages'][-1]
                session_state['messages'].append(
                    {"role": "assistant", "content": f"'{current_attributes[i]}' is invalid,"
                                                     f" please provide valid {i}."})
                response['Error'] = True
                response['msg'] = f"'{current_attributes[i]}' is invalid, please provide valid {i}."
                current_attributes[i] = 'None'
                print(">>> In Correct")
                # return False

    # email validation
    email_attributes = ['email']
    for i in current_attributes:
        if i in email_attributes and current_attributes[i] not in ['None', None] and \
                (i not in previous_attributes or previous_attributes[i] != current_attributes[i]):
            print("***** Email validation is executed....")
            try:
                emailinfo = validate_email(current_attributes[i], check_deliverability=True)
                email = emailinfo.normalized
                print(">>> Correct")
            except EmailNotValidError as e:
                del session_state['messages'][-1]
                session_state['messages'].append({"role": "assistant",
                                                  "content": f"'{current_attributes[i]}' is invalid,"
                                                             f" please provide valid {i}. {e}"})
                response['Error'] = True
                response['msg'] = f"'{current_attributes[i]}' is invalid, please provide valid {i}. {e}"
                current_attributes[i] = 'None'
                print(">>> In Correct")

    return current_attributes, response, session_state


def output_parser_(string):
    # Remove the leading and trailing triple backticks and any additional whitespace
    if string == "The server is experiencing overload. Please try again after a few seconds.":
        return {"Task": "None", "response": "The server is experiencing overload. Please try again after a few seconds.",
                "Attributes": {}}
    try:
        try:
            occurance = [m.start() for m in re.finditer('```', string)]
            string = string[occurance[0]:occurance[1] + 1]
        except:
            start_occurance = [m.start() for m in re.finditer('{', string)][0]
            end_occurance = [m.start() for m in re.finditer('}', string)][-1]
            string = string[start_occurance:end_occurance + 1]

        string = string.strip()
        clean_string = string.strip('`').strip()

        # Remove the 'json' label from the beginning
        clean_string = clean_string.replace('json', '')

        # print(clean_string)
        clean_string = clean_string.strip()

        # Load the string as JSON
        data = json.loads(clean_string)

        # # Print the extracted dictionary
        # print(data)

        return data
    except:
        return "Parsing Error"

    
def output_parser(string):
    # Remove the leading and trailing triple backticks and any additional whitespace
    try:
        start_occurance = [m.start() for m in re.finditer('{', string)][0]
        end_occurance = [m.start() for m in re.finditer('}', string)][-1]
        string = string[start_occurance:end_occurance + 1]

        string = string.replace("null", "None")

        string = string.strip()
        data = eval(string)
        return data
    except:
        print("**** ", string)
        return "Parsing Error"
