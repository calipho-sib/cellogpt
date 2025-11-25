import os
from doc_converter import DocConverter
from utils import log_it


# = = = = = = = = = = = = = =
class PubliClPairsFactory:
# = = = = = = = = = = = = = =

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def __init__(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - -    
        #self.cl_publi_pair_file = "../jats-parser/cl-single-publi-with-pmcid.tsv"   # a) for these (with pmcids) we can get publis as text using my converter fed with sibils fetched json 
        self.pmcid_data_dir = "../jats-parser/data_txt"                              # a) dir where txt version of publi examples having a pmcid are stored
        self.cl_publi_pair_file = "../jats-parser/cl-single-publi-0-xref.tsv"        # b) for those (no constraints on pmcid) we can use Amos' pdf directory and doc_convertor.py
        self.pdf_dir = "pdf"                                                         # b) Amos' input dir
        self.publi_dir = "data/publi_txt"                                            # b) dir where txt version of publication in Amos' dir is built and stored for data examples
        self.cl_data_dir = "data/cl_txt"
        self.files_in_pdf_dir = os.listdir(self.pdf_dir)
        self.pairs = list()


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def load_pairs(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        tmp_pairs = self.step1_load_cl_publi_pair_examples()                          # loads everything but ignores conversion of publi to txt
        log_it("INFO", f"Found {len(tmp_pairs)} example pairs")
        self.step2_convert_cl_publi_pair_examples(tmp_pairs)
        log_it("INFO", f"Stored {len(self.pairs)} example pairs with usable generated publi text content")


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def step1_load_cl_publi_pair_examples(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        # a) cl      cl_class        xref_count      xref_db_count   species_list    publi_id        publi_year      pmcid
        # b) cl      cl_class        xref_count      xref_db_count   species_list    publi_id        publi_year
        pubid_dict = dict()
        with open(self.cl_publi_pair_file) as stream:
            stream.readline() # skip header line
            while True:
                line = stream.readline()
                if line == "": break
                fields = line.strip().split("\t")
                xref_count = fields[2]
                # criterion (2) - reject cell lines with DR lines (is now handled in previous step by the SPARQL query)
                if xref_count != "0": continue
                cl_class = fields[1]
                # criterion (5) - reject pairs with a hybrid* cell line
                if cl_class in ["Hybridoma", "HybridCellLine"]: continue
                cl = fields[0]
                # pubid = fields[7] # case a)
                pubid=fields[5]     # case b)
                # criterion (8) we ignore CelloPub
                if pubid.startswith("CelloPub"): continue
                if pubid not in pubid_dict: pubid_dict[pubid] = set()
                pubid_dict[pubid].add(cl)
        log_it("DEBUG", "Got", len(pubid_dict), "pubid entries")

        # criterion (4) - keep only pairs when pubid is related to no more than one cell line
        tmp_pairs = list()
        for pubid in pubid_dict:
            if len(pubid_dict[pubid]) == 1:
                tmp_pairs.append({"cl": next(iter(pubid_dict[pubid])), "pubid": pubid})
        log_it("DEBUG", "Filtered out pubids with more than one cell line")

        pairs = list()
        for i, pair in enumerate(tmp_pairs):
            if i % 500 == 0: log_it("DEBUG", f"Loading and checking cell lines {i}/{len(tmp_pairs)}")
            example = self.get_example_data(pair, ignore_publi_data=True) # we don't need publication data for criteria below
            cl_entry = example["cello_text"]
            # criterion (7) - cell line should not have a parent
            if self.cell_line_has_parent(cl_entry): continue
            # criterion (6) - Misc line should not mention a source of information
            if self.cell_line_has_misc_with_source(cl_entry): continue
            pairs.append(pair)
        log_it("DEBUG", "Filtered out cell lines with parents and with sources in misc")

        return pairs


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def step2_convert_cl_publi_pair_examples(self, tmp_pairs):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        for pair in tmp_pairs:
            data_pair = self.get_example_data(pair, ignore_publi_data = False)        # performs conversion of publi to txt if needed
            txt = data_pair["publi_text"]
            if len(txt) >= 1000: self.pairs.append(pair)                              # ignore pairs where publi is empty or almost empty


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def cell_line_has_misc_with_source(self, cl_entry):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        for line in cl_entry.split("\n"):
            if line.startswith("CC   Miscellaneous:"):
                #log_it("DEBUG", "cell line with misc field")
                for str in [ "from archive documents", "from author direct submission",  "Direct author submission", 
                                "from personal commuincation", "from MSKCC", "from personal communication" ]:
                    if str in line: 
                        #log_it("DEBUG", "Found cell line with source in misc field")
                        return True
        return False


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def cell_line_has_parent(self, cl_entry):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        for line in cl_entry.split("\n"):
            if line.startswith("HI   "): 
                #log_it("DEBUG", "Found cell line with parent")
                return True
        return False


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_cello_entry_txt(self, clac):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        filename = f"{self.cl_data_dir}/{clac}.txt"
        # get cl file from cache if exists
        if os.path.exists(filename):
            cello_text = open(filename).read()
            #log_it(f"DEBUG got it from cache:", clac)
        # otherwise get it from remote api and cache it
        else:
            url = f"https://www.cellosaurus.org/{clac}.txt"
            cello_text = requests.get(url).text
            with open(filename, "w") as stream: stream.write(cello_text)
            #log_it("DEBUG had to download it:", clac)
        return cello_text


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_expected_cl_entry(self, clac):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        lines = list()
        for line in self.get_cello_entry_txt(clac).split("\n"):
            if line.startswith("AC   "): continue       # we ignore accession number
            elif line.startswith("DT   "): continue     # we ignore version and dates
            elif line.startswith("DR   "): continue     # we ignore cross-refs
            lines.append(line)
            if line.startswith("//"): break             # we ignore RX details so we stop after first encounter of //
        return "\n".join(lines)        


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_example_data(self, pair, ignore_publi_data = False):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        return self.get_example_data_b(pair, ignore_publi_data=ignore_publi_data)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_example_data_a(self, pair):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        #log_it("pair", pair)
        pubid = pair["pubid"]
        file = f"{self.pmcid_data_dir}/{pubid}.txt"
        publi_text = open(file, 'r').read()
        clac = pair["cl"]
        #cello_text = self.get_cello_entry_txt(clac)
        cello_text = self.get_expected_cl_entry(clac)
        return { "publi_text": publi_text, "cello_text": cello_text}


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_example_data_b(self, pair, ignore_publi_data = False):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        clac = pair["cl"]
        #cello_text = self.get_cello_entry_txt(clac)
        cello_text = self.get_expected_cl_entry(clac)
        pubid = pair["pubid"]
        if ignore_publi_data:
            return { "publi_text": None, "cello_text": cello_text}
        else:
            publi_text = self.get_publi_text(pubid)
            return { "publi_text": publi_text, "cello_text": cello_text}


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_publi_text(self, pubid):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        rootname = self.get_rootname(pubid)
        txt_filename = f"{self.publi_dir}/{rootname}.txt"
        
        # Get publi text version form cache directory if exists
        if os.path.exists(txt_filename): 
            with open(txt_filename) as stream:
                publi_text = stream.read()
                return publi_text

        # Otherwise create cache file and return content of text file generated
        pub_header = "Publication " + pubid.replace("=", ": ")
        files = self.get_publi_sorted_matching_files(pubid)
        elems = list()
        for i, file in enumerate(files):
            filepath = f"{self.pdf_dir}/{file}"
            publication_id=pub_header if i==0 else None
            if i == 1: elems.append("# Supplementary data")
            elem = DocConverter().convert_to_text(filepath, publication_id=publication_id)
            if elem: elems.append(elem)
            else: log_it("WARNING None or empty text conversion for", filepath)
        publi_text = "\n\n".join(elems)
        with open(txt_filename, "w") as stream: 
            stream.write(publi_text)
            return publi_text


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_rootname(self, pubid):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        rootname = None
        if pubid.startswith("PubMed="):
            rootname = pubid[7:]
        elif pubid.startswith("DOI="):
            rootname = pubid.replace("=", "_").replace("/", "-").replace(";", "-").replace(":", "-").replace("<", "-").replace(">", "-")
        return rootname


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def get_publi_sorted_matching_files(self, pubid):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        rootname = self.get_rootname(pubid)
        if rootname is None: return list()
        matching_files = list(file for file in self.files_in_pdf_dir if file.startswith(rootname))
        matching_files.sort()
        if len(matching_files) > 0 and not matching_files[0].endswith(".pdf"):
            log_it(f"WARNING first file of {pubid} is not a pdf:", matching_files)
        return matching_files


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
    def check_pairs(self, pairs):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        for pair in pairs:
            pubid = pair["pubid"]
            matching_files = self.get_publi_sorted_matching_files(pubid)
            if len(matching_files) == 0:
                log_it(f"WARNING No matching files for {pubid}")
            

    

# =================================================================================
if __name__ == '__main__':
# =================================================================================

    factory = PubliClPairsFactory()
    factory.load_pairs()
    print("--------------- some example pairs ---------------")
    for i, pair in enumerate(factory.pairs):
        if i > 10: break
        print(pair)

    pair = factory.pairs[20]
    data = factory.get_example_data(pair)
    cello_text = data["cello_text"]
    publi_text = data["publi_text"]
    print("\n--------------- pair at index 20 ---------------\n")
    print(pair)    
    print("\n--------------- cl entry  of pair 20 ---------------\n")
    print(cello_text)
    print("\n--------------- publi txt of pair 20 ---------------\n")
    print(publi_text)
    print("\n--------------- end ---------------\n")

 