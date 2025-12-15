from pydantic import BaseModel, Field, create_model, ConfigDict
from typing import Literal  # or use typing_extensions.Literal in Python <3.8

import json


# = = = = = = = = = = = = = = = = = = = =
class SourcePublicationReferenceModel(BaseModel):
# = = = = = = = = = = = = = = = = = = = =
    publication_database: Literal["PubMed", "DOI"]  = Field(description="Publication database name")
    publication_identifier: str = Field(description="DOI or PUbMed publication identifier")

SourcePublicationReferenceModel.model_config = ConfigDict(extra="forbid")    


# = = = = = = = = = = = = = = = = = = = =
class LocusShortTandemRepeatModel(BaseModel):
# = = = = = = = = = = = = = = = = = = = =
    short_tandem_repeat_locus: Literal["Amelogenin", "CSF1PO", "D2S1338", "D3S1358", "D5S818", "D7S820", "D8S1179", "D13S317", 
            "D16S539", "D18S51", "D19S433", "D21S11", "FGA", "Penta D", "Penta E", "TH01", "TPOX", "vWA", "D1S1656", "D2S441", 
            "D6S1043", "D10S1248", "D12S391", "D22S1045", "DXS101", "DYS391", "F13A01", "F13B", "FESFPS", "LPL", "Penta C", 
            "SE33", "Mouse STR 1-1", "Mouse STR 1-2", "Mouse STR 2-1", "Mouse STR 3-2", "Mouse STR 4-2", "Mouse STR 5-5", 
            "Mouse STR 6-4", "Mouse STR 6-7", "Mouse STR 7-1", "Mouse STR 8-1", "Mouse STR 11-2", "Mouse STR 12-1", "Mouse STR 13-1", 
            "Mouse STR 15-3", "Mouse STR 17-2", "Mouse STR 18-3", "Mouse STR 19-2", "Mouse STR X-1", "Dog FHC2010", "Dog FHC2054", 
            "Dog FHC2079", "Dog PEZ1", "Dog PEZ3", "Dog PEZ5", "Dog PEZ6", "Dog PEZ8", "Dog PEZ12", "Dog PEZ20"]  = Field(
        description="Human, mouse or dog locus used to build a short tandem profile ot the cell line")
    number_of_repeat_in_locus: str = Field(
        description="Number(s) of repeat observed in the allele of the locus.", 
        examples=["11", "7,8", "X", "X,Y"])


LocusShortTandemRepeatModel.model_config = ConfigDict(extra="forbid")    


# = = = = = = = = = = = = = = = = = = = =
class JsonSchemaFactory:
# = = = = = = = = = = = = = = = = = = = =


    # - - - - - - - - - - - - - - - - - - - - 
    def __init__(self):
    # - - - - - - - - - - - - - - - - - - - - 
        self.CellLineModel = self.build_cell_line_model()
        self.CellLineModel.model_config = ConfigDict(extra='forbid')

    # - - - - - - - - - - - - - - - - - - - - 
    def get_clean_line(self, str):
    # - - - - - - - - - - - - - - - - - - - - 
        tmp = str.replace("\n", " ")
        lng = len(tmp)
        while True:
            tmp = tmp.replace("  ", " ")
            if len(tmp) == lng: return tmp
            lng = len(tmp)


    # - - - - - - - - - - - - - - - - - - - - 
    def build_cell_line_model(self):
    # - - - - - - - - - - - - - - - - - - - - 

        cell_line_fields = dict()

        ID_FIELD = (str, Field(
            description=self.get_clean_line("The cell line recommended name. The name of the cell line as provided in the source publication."),
            examples=["HeLa", "017-PC-A", "F.thy 62891"]
            )
        )
        SY_FIELD = (list[str], Field(
            min_items=0, max_items=5,
            description=self.get_clean_line("""List of cell name synonyms. We try to list all the different synonyms for the cell line, 
                including alternative use of lower and upper cases characters. Misspellings are not included in synonyms.""")
            )
        )
        CA_FIELD = (Literal["Cancer cell line", "Conditionally immortalized cell line", "Embryonic stem cell", "Factor-dependent cell line", 
                           "Finite cell line", "Hybrid cell line", "Hybridoma", "Induced pluripotent stem cell", "Somatic stem cell", 
                           "Spontaneously immortalized cell line", "Stromal cell line", "Telomerase immortalized cell line", "Transformed cell line", 
                           "Undefined cell line type"], Field(
            description=self.get_clean_line("""Category to which a cell line belongs. Use 'Undefined cell line type' only when no category is 
                suitable for the cell line""")
            )
        )
        SX_FIELD = (Literal["Female", "Male", "Mixed sex", "Sex ambiguous", "Sex unspecified"], Field(
            description=self.get_clean_line("""Sex of the individual from which the cell line originates. Mixed sex value is for cell 
                lines originating from multiple individuals having different sexes.""")
            )
        )
        RX_FIELD = (list[SourcePublicationReferenceModel], Field(
            min_items=1, max_items=1,
            description=self.get_clean_line("The publication reference appearing at the top of the source publication in the user input (1-1 required)."),
            examples=[{"publication_database": "PubMed",  "publication_identifiers": "821777" }, 
                    {"publication_database": "DOI",     "publication_identifier": "10.1016/B978-012229460-0/50004-X" }]
            )
        )
        ST_FIELD = (list[LocusShortTandemRepeatModel], Field(
            min_items=0,
            description=self.get_clean_line("""A short tandem profile (STR) of the cell line as a list of short tandem repeat loci with 
                the number of repeats observed for each of them.""")
            )
        )
        DI_FIELD = (list[str], Field(
            min_items=0, max_items=3,
            description=self.get_clean_line("Name of the disease(s) suffered by the individual from which the cell line originated (0-2 required)."),
            examples=["NUT midline carcinoma", "Autism spectrum disorder", "Cutaneous melanoma"]
            )
        )
        OX_FIELD = (list[str], Field(
            min_items=1, max_items=2,
            description=self.get_clean_line("Name of the species of the individual from which the cell line originates  (1-2 required)."),
            examples=["Human", "Mus musculus", "Zebrafish"]
            )
        )
        cell_line_fields['cell_line_name'] = ID_FIELD
        cell_line_fields['cell_line_name_synonyms'] = SY_FIELD
        cell_line_fields['source_publication_reference'] = RX_FIELD
        cell_line_fields['cell_line_str_profile'] = ST_FIELD
        cell_line_fields['cell_line_diseases'] = DI_FIELD
        cell_line_fields['cell_line_category'] = CA_FIELD
        cell_line_fields['cell_line_species'] = OX_FIELD
        cell_line_fields['cell_line_sex'] = SX_FIELD

        return create_model("CellLineModel", **cell_line_fields)



    # - - - - - - - - - - - - - - - - - - - - 
    def get_json_schema_string(self, model):
    # - - - - - - - - - - - - - - - - - - - - 
        json_schema = model.model_json_schema()
        pretty_schema = json.dumps(json_schema, indent=2)
        return pretty_schema
    

    # - - - - - - - - - - - - - - - - - - - - 
    def get_json_schema(self, model):
    # - - - - - - - - - - - - - - - - - - - - 
        return model.model_json_schema()
    


# =================================================
if __name__ == '__main__':
# =================================================

    factory = JsonSchemaFactory()
    print(factory.get_json_schema_string(SourcePublicationReferenceModel))    
    print(factory.get_json_schema_string(LocusShortTandemRepeatModel))
    print("---------------")
    print(factory.get_json_schema_string(factory.CellLineModel))
    