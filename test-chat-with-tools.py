from openai import OpenAI
import json

client = OpenAI()

# 1. Define a list of callable tools for the model
tools = [
    {
        "type": "function",
        "name": "get_city_details",
        "description": "Get some typical details of the city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city_name": { "type": "string", "description": "A city name", },
            },
            "required": ["city_name"]
        }
    }, {
        "type": "function",
        "name": "get_name_details",
        "description": "Provides infomation about names given tu human beings.",
        "parameters": {
            "type": "object",
            "properties": {
                "someones_name": {"type": "string", "description": "Someone's first name, e.g. Bob", },
            },
            "required": ["someones_name"]
        }
    }
]

instructions="""
Rewrite the story as appears in the input but:
1) call the function get_name_details() when you encounter people names and replace the name with the output of the function. 
2) call the function get_city_details() when you encounter city names and replace the city name with the output of the function. 
"""

input_story = """
Story:
It is a story about normal people.
John went to Boston when he was 12. His parents, 
Melanie and Paul, married in 1977 in London.
They came to US beause they got a free green card.
"""

def get_name_details(someones_name):
    return f"{someones_name} (a pretty name)"

def get_city_details(city_name):
    return f"{city_name} (a beautiful city)"


# Create a running input list we will add to over time
input_list = [
    {"role": "user", "content": input_story}
]

# 2. Prompt the model with tools defined
response = client.responses.create(
    model="gpt-5",
    tools=tools,
    instructions=instructions,
    input=input_list,
)

# Save function call outputs for subsequent requests
input_list += response.output

for item in response.output:
    if item.type == "function_call":
        if item.name == "get_city_details":
            args_dict =  json.loads(item.arguments)
            someones_name =args_dict["city_name"]
            city_details = get_city_details(someones_name)            
            input_list.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": city_details
            })
        elif item.name == "get_name_details":
            args_dict =  json.loads(item.arguments)
            someones_name =args_dict["someones_name"]
            name_details = get_name_details(someones_name)            
            input_list.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": name_details
            })

print("--------- Final input:")
for el in input_list:
    print(el)
    print("-------------")

response = client.responses.create(
    model="gpt-5",
#    tools=tools,
#    instructions="Rewrite the story as in the input but integrate the name details you could get by calling the function get_name_details.",
    input=input_list,
)

# 5. The model should be able to give a response!
print("------------ Final response model dump json:")
print(response.model_dump_json(indent=2))
print("------------ Final response output text:")
print("\n" + response.output_text)
print("--- end")

