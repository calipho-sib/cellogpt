import sys
import os
import requests
import json
from openai import OpenAI
from utils import log_it
from dictionary_searcher import DictionarySearcher


# = = = = = = = = = = = = = = = =
class ClTextGenerator:
# = = = = = = = = = = = = = = = =


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.model="gpt-5-mini"
        self.client = OpenAI()
        self.funcalls = list()
        self.dico_searcher = DictionarySearcher()
        log_it("INFO ClTextGenerator instance initialized")


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def strip_lines(self, text):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        lines = list()
        for line in text.split("\n"):
            lines.append(line.strip())
        return "\n".join(lines)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_defined_tools(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        funs = [
            {
                "type": "function",
                "name": "get_disease_line",
                "description": "Builds a DI line for the Cellosaurus entry from the disease_name parameter.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "disease_name": {
                            "type": "string",
                            "description": "The name of a disease, as reported in the source publication.",
                        },
                    },
                    "required": ["disease_name"],
                    "additionalProperties": False
                },
            },
            {
                "type": "function",
                "name": "get_site_line",
                "description": "Builds a CC line with topic 'Derived from site' for the Cellosaurus entry from site_name and site_type parameters.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site_name": {
                            "type": "string",
                            "description": "The name of the anatomical site of the organism from which the cell line originates, as reported in the source publication.",
                        },
                        "site_type": {
                            "type": "string",
                            "enum": ["Metastatic", "In situ"],
                            "description": "Metastatic or in situ origin of the sample from which the cell line is derived.",
                        },
                    },
                    "required": ["site_name", "site_type"],
                    "additionalProperties": False
                },
            },
        ]
        return funs


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_disease_line(self, disease_name):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        term, score = self.dico_searcher.search("disease", disease_name)
        db = term["db"]
        id = term["id"]
        pref_name = term["pref_name"]
        rounded_score = round(score, 5)
        log_it(f"DEBUG DI   {db}; {id}; {pref_name} => score={rounded_score}, disease_found='{disease_name}'")
        return f"DI   {db}; {id}; {pref_name}"


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_site_line(self, site_name, site_type):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        term, score = self.dico_searcher.search("anatomy", site_name)
        db = term["db"]
        id = term["id"]
        pref_name = term["pref_name"]
        rounded_score = round(score, 5)
        log_it(f"DEBUG CC   Derived from site: {site_type}; {pref_name}; {db}={id} => score={rounded_score}, site_found='{site_name}, type_found='{site_type}'")
        return f"CC   Derived from site: {site_type}; {pref_name}; {db}={id}."


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_instructions(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        fields_info = open('fields-info.txt').read()
        more_instructions = open('more-instructions.txt').read()
        return self.strip_lines(f"""
            As an expert of the Cellosaurus content and data structure, you extract relevant information 
            found in a publication in order to generate a cell line entry for the cellosaurus in txt format. 
            To help you generate the Cellosaurus entry, read the entry description and format here:

            {fields_info}

            {more_instructions}

            During generation of the Cellosaurus entry, ignore creation of 'AC   ', 'DT   ' and 'DR   ' fields.
            """)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_input(self, publi):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        return self.strip_lines(f"""
                Use the content of the following publication to generate a cell line entry for Cellosaurus.

                {publi}
                """)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def generate_cl(self, publi):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.funcalls = list()

        # Create a running input list we will add to over time
        input_list = [
            {"role": "user", "content": self.get_input(publi)}
        ]

        # Prompt the model with tools defined
        response = self.client.responses.create(
            model="gpt-5",
            #reasoning={"effort": "high"},
            #tool_choice="auto",
            tools=self.get_defined_tools(),
            instructions=self.get_instructions(),
            input=input_list,
        )

        # Save function call outputs for subsequent requests
        input_list += response.output

        for item in response.output:
            if item.type == "function_call":
                if item.name == "get_disease_line":
                    args_dict =  json.loads(item.arguments)
                    name =args_dict["disease_name"]
                    line = self.get_disease_line(name)            
                    self.funcalls.append({ "function": item.name, "args": args_dict, "output": line})
                    input_list.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": line
                    })
                elif item.name == "get_site_line":
                    args_dict =  json.loads(item.arguments)
                    name =args_dict["site_name"]
                    typ =args_dict["site_type"]
                    line = self.get_site_line(name, typ)            
                    self.funcalls.append({ "function": item.name, "args": args_dict, "output": line})
                    input_list.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": line
                    })

        # print("--------- Final input:")
        # for el in input_list:
        #     print(el)
        #     print("-------------")

        response =self.client.responses.create(
            model="gpt-5",
            input=input_list,
        )

        # The model should be able to give a response!
        # print("------------ Final response model dump json:")
        # print(response.model_dump_json(indent=2))
        # print("------------ Final response output text:")
        # print("\n" + response.output_text)
        # print("--- end")

        return response.output_text



    

# =================================================================================
if __name__ == '__main__':
# =================================================================================

    publi_text = open("data/publi_txt/2342463.txt").read()
    cl_generator = ClTextGenerator()
    generated_cl = cl_generator.generate_cl(publi_text)
    log_it(f"\n-------- generated cl --------------\n\n{generated_cl}")
    log_it(f"\n-------- function calls ------------\n\n")
    for fc in cl_generator.funcalls: print(fc)
    log_it(f"\n-------- end --------")

