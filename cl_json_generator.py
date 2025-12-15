import sys
import os
import requests
import json
from openai import OpenAI
from utils import log_it
from dictionary_searcher import DictionarySearcher
from json_schema_factory import JsonSchemaFactory


# = = = = = = = = = = = = = = = =
class ClJsonGenerator:
# = = = = = = = = = = = = = = = =


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.model="gpt-5-mini"
        #self.model="gpt-4o-2024-08-06"
        self.client = OpenAI()
        self.json_model_factory = JsonSchemaFactory()


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def strip_lines(self, text):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        lines = list()
        for line in text.split("\n"):
            lines.append(line.strip())
        return "\n".join(lines)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_instructions(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        return self.strip_lines(f"""
            You are an expert of the Cellosaurus content and your task is to extract relevant information 
            related to the cell line mentioned in the source publication given in the input.
            """)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_input(self, publi):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        return self.strip_lines(f"""
            Extract cell line properties mentioned in the following source publication:
            {publi}
        """)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def generate_cl_from_model_4o(self, publi):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        """
        Note: documentation about response object structure is poor at the moment (Dec 8, 2025)
        Generate a cell line json object by using the latest manner to chat with gpt
        returns an object with properties status and obj_response with the cell line object as a value (if status is okeverything's ok)
        """
        response = self.client.responses.parse(
            model=self.model,
            instructions = self.get_instructions(),
            input = self.get_input(publi),
            text = {
                "format": {
                    "type": "json_schema",
                    "strict": True,
                    "name": "cell_line_model",
                    "schema": self.json_model_factory.CellLineModel.model_json_schema()
                }})
        
        for output in response.output:
            for content in output.content:
                if content.text and content.type == "output_text":
                    try:
                        obj = json.loads(content.text)
                        return { "status": "ok", "obj_response": obj}
                    except Exception as e:
                        # oups, expected json not parseable
                        msg = "ERROR could not json parse response.output[i].content[j].text in response"
                        log_it(msg, e, response)
                        return { "status": "error", "message": msg, "raw_response": response }

        # oups, expected content not found in response
        msg = "ERROR could not find response.output[i].content[j].text in response"
        log_it(msg, response)
        return { "status": "error", "message": msg, "raw_response": response }


    
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def generate_cl(self, publi):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        """
        generate a cell line json object by using old manner to chat with gpt
        returns the cell line object (if okeverything's ok)
        """
        completion = self.client.chat.completions.parse(
            model=self.model,
            messages=[
                { "role": "system", "content": self.get_instructions() },
                { "role": "user",   "content": self.get_input(publi) }
            ],
            response_format=self.json_model_factory.CellLineModel
        )

        result = completion.choices[0].message

        if result.refusal:
            return result.refusal
        else:
            obj = json.loads(result.content)
            return obj

 


# =================================================================================
if __name__ == '__main__':
# =================================================================================

    publi_text = open("data/publi_txt/2342463.txt").read()
    cl_generator = ClJsonGenerator()
    generated_cl = cl_generator.generate_cl(publi_text)
    log_it(f"\n-------- generated cl --------------\n\n")
    #print(generated_cl)
    print(json.dumps(generated_cl, indent=2))
    #print(json.dumps(generated_cl, indent=2))
    log_it(f"\n-------- end --------")

