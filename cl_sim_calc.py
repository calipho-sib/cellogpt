import sys
import os
import datetime
from sentence_transformers import SentenceTransformer, util
from itertools import permutations
from utils import log_it
from colorama import Fore, Style, init

# ---------------------- Cell line similarity calculator ----------------------
class ClSimCalc:
# -----------------------------------------------------------------------------


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def __init__(self):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
 

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def compare_cl_entries(self, act_entry, exp_entry):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        entry_dict = { "act": act_entry, "exp": exp_entry}
        fld_dict = dict()
        for tag in entry_dict:
            entry = entry_dict[tag]
            for line in entry.split("\n"):
                if line.startswith("AC   "): continue
                if line.startswith("DT   "): continue
                if line.startswith("//"): continue
                if line.strip() == "": continue
                if line.startswith("CC   "):
                    index = line.find(":") 
                    name = line[0:index] if index > -1 else "CC   invalid"
                    value = line[index + 1:].strip() if index > -1 else line[5:].strip()
                elif line.startswith("ST   "):
                    index = line.find(":") 
                    name = line[0:index] if index > -1 else "ST   invalid"
                    value = line[index + 1:].strip() if index > -1 else line[5:].strip()
                elif line.startswith("DR   "):
                    index = line.find(";") 
                    name = line[0:index] if index > -1 else "DR   invalid"
                    value = line[index + 1:].strip() if index > -1 else line[5:].strip()
                elif line.startswith("RX   "):
                    index = line.find("=") 
                    name = line[0:index] if index > -1 else "RX   invalid"
                    value = line[index + 1:].strip() if index > -1 else line[5:].strip()
                else:
                    name = line[0:5]
                    value = line[5:].strip()
                if name not in fld_dict: fld_dict[name] = { "act": [], "exp": [] }
                fld_dict[name][tag].append(value)

        fields = sorted(fld_dict.keys())
        entry_weight = 0
        entry_score = 0
        for f in fields:
            #log_it("--------------")
            f_pad = f.ljust(25)
            sentence_dict = { "act": [], "exp": [] }
            for tag in [ "act", "exp" ]:
                for sentence in fld_dict[f][tag]:
                    sentence_dict[tag].append(sentence)                
                    #log_it(f"{f_pad} - {tag} : {sentence}")
            #log_it(f"DEBUG Computing score for field {f}")
            score = self.get_best_score(sentence_dict["act"], sentence_dict["exp"])
            weight = max( len(sentence_dict["act"]), len(sentence_dict["exp"]))
            weighted_score = round(score / weight, 5)
            fld_dict[f]["score"] = score
            fld_dict[f]["weight"] = weight
            fld_dict[f]["weighted_score"] = weighted_score
            #log_it(f"{f_pad} - weight: {weight}, score:{score}, weighted score: {weighted_score}")
            entry_weight += weight
            entry_score += score
        entry_score = round(entry_score,5)
        weighted_score = round(entry_score / entry_weight, 5)    
        fld_dict["entry"] = { "weight" : entry_weight, "score": entry_score, "weighted_score": weighted_score }
        f_pad = "entry".ljust(25)
        #log_it("--------------")
        #log_it(f"{f_pad} - weight: {entry_weight}, score:{entry_score}, weighted score: {weighted_score}")
        return fld_dict
        

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_best_score(self, actual_sentences, expected_sentences):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        while len(actual_sentences) < len(expected_sentences): actual_sentences.append("")
        while len(expected_sentences) < len(actual_sentences): expected_sentences.append("")

        # Compute cosine similarity between sentence pairs
        act_embeddings = self.model.encode(actual_sentences, convert_to_tensor=True)
        exp_embeddings = self.model.encode(expected_sentences, convert_to_tensor=True)
        cosine_scores = util.cos_sim(exp_embeddings, act_embeddings)

        n = len(actual_sentences)
        act_indexes = list(range(n))
        permut_list = list(permutations(list(range(n))))
        best_permut_score = 0
        #best_permut = None
        for permut in permut_list:
            permut_score = 0.0
            exp_indexes = list(permut)
            for i in range(n):
                act_idx = act_indexes[i]
                exp_idx = exp_indexes[i]
                if actual_sentences[act_idx] == "" or expected_sentences[exp_idx] == "":
                    score = 0.0
                else:
                    score = cosine_scores[act_idx][exp_idx].item()
                permut_score += score
                # act_pad = actual_sentences[act_idx].ljust(10)
                # exp_pad = expected_sentences[exp_idx].ljust(10)
                # log_it(act_idx, "-", exp_idx, ":", act_pad, "-", exp_pad, "=>", score)
            if permut_score > best_permut_score:
                best_permut_score = permut_score
                best_permut = permut
            #log_it("permut_score:", permut_score)
            #log_it("------")
        #log_it(best_permut, "has best score", best_permut_score)
        return round(best_permut_score,5)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def field_should_be_displayed(self, field_key, only_prefixes):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        if only_prefixes is None: return True
        if type(only_prefixes) == str: return field_key.startswith(only_prefixes)
        if type(only_prefixes) == list:
            for prefix in only_prefixes:
                if field_key.startswith(prefix): return True
            return False
        return False


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_result_lines(self, result_dic, only_prefixes=None):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        lines = list()
        for k in sorted(list(result_dic.keys())):
            if self.field_should_be_displayed(k, only_prefixes):            
                v = result_dic[k]
                fld = k.ljust(25)
                score =  f"{v['score']:10.5f}"
                weight = f"{v['weight']:5d}"
                wscore =  f"{v['weighted_score']:10.5f}"
                if v['weighted_score'] == 1: wscore = Fore.LIGHTGREEN_EX + wscore + Style.RESET_ALL
                line = f"{fld} {weight} {score} {wscore}"
                lines.append(line)
                #log_it(line)
        return lines


# =======================================
if __name__ == '__main__':
# =======================================

    act = ["notion", "food", "hi"]
    exp = ["hello", "eat", "concept"]

    act_entry = """ID   MPT-S1
SY   MPT S1; MPT-S1 cell line; MPT-S1 PDX
DR   ENA: PRJEB48011
DR   ENA: PRJEB48016
RX   PubMed: 35365682
RX   DOI: 10.1038/s41523-022-00413-1
RX   PMCID: PMC8975864
WW   https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8975864/
CC   From: Established at the Laboratory of Cancer Epigenome, National Cancer Centre Singapore (NCCS) with contributions from Cancer Discovery Hub (NCCS), Duke‑NUS Medical School and Genome Institute of Singapore; corresponding author: Jason Yongsheng Chan.
CC   Donor information: 51‑year‑old Chinese female with malignant phyllodes tumor of the left breast; developed local recurrence (chest wall) and lung metastases; received multiple lines of therapy including liposomal doxorubicin, gemcitabine+docetaxel, palliative radiotherapy and pazopanib; initial clinical response to pazopanib followed by progression.
CC   Derived from site: Trucut biopsy of recurrent chest wall mass (metastatic lesion from left breast phyllodes tumor). A patient‑derived xenograft (PDX) was established in NSG mice and the cell line was derived from enzymatic dissociation of the xenograft after serial transplantation.
CC   Cell type: Spindle‑shaped stromal (fibroepithelial) tumor cells. Histology: osteoclast‑like multinucleated giant cells, epithelioid areas and heterologous cartilaginous/osteoid elements. IHC: p63 positive; high Ki‑67; cytokeratin (AE1/3, MNF116), EMA and GATA3 negative.
CC   Characteristics: Continuous culture beyond 6 months; morphology elongated spindle cells. Culture: DMEM + 10% FBS + 1% penicillin‑streptomycin; 37 °C, 5% CO2. Xenograft‑passaged in female NSG mice (subcutaneous). Mouse cell depletion (Miltenyi Mouse Cell Depletion Kit) performed prior to culture; mouse and human CD45 staining used to exclude xenograft‑associated lymphoma. STR authentication performed (Supplementary Table 1).
CC   Doubling time: Approximately 2–3 days (48–72 h).
CC   Drug response / phenotype: In vitro sensitivity to several chemotherapeutics with IC50s ranging ~0.32 nM to 77.9 nM. Tyrosine kinase inhibitors decreased viability with IC50s: pazopanib 6257 nM, sunitinib 4698 nM, axitinib 2636 nM, sorafenib 1393 nM. Pazopanib (1–10 µM) induced dose‑dependent apoptosis (increased sub‑G1 fraction; PARP and caspase‑3 cleavage), reduced clonogenicity and migration, induced micronuclei formation, decreased ENPP1 expression, increased cytosolic DNA, phospho‑TBK1 and PD‑L1, and inhibited in vivo PDX growth (100 mg/kg daily) with reduced microvessel density. ENPP1 inhibitor (ENPP1‑IN‑1) decreased viability and ENPP1/C‑Myc levels; other TKIs tested did not reduce ENPP1.
CC   Sequence variation: Somatic mutations validated and concordant across patient tumor, PDX and cell line: MED12 c.131G>A; TP53 c.754_756delCTC and c.750_754delinsA; RB1 c.1530_1531delAG and c.1588_1589delAA; KMT2D c.6079_6082delAATT. Whole‑exome sequencing reported 41 missense, 1 nonsense, 13 silent and 14 indel somatic variants (Supplementary Table 2).
CC   Omics: Whole‑exome sequencing (tumor vs matched blood) and whole‑transcriptome sequencing (tumor and cell lines including pazopanib treatment) performed. ENA accessions: PRJEB48011 (WES), PRJEB48016 (RNA‑seq). Transcriptomic analyses and GSEA identified deregulated oncogenic and apoptosis pathways and pazopanib‑mediated downregulation of MMP13, ST6GAL2 and ENPP1.
CC   Authentication: STR genotyping (Axil Scientific, Singapore) performed; STR profile reported in Supplementary Table 1.
CC   Xenograft notes: PDX created by subcutaneous implantation of 2–3 mm tumor cores into 6‑week‑old female NSG mice; serial transplantation was performed and cell line derived after the third serial transplant.
CC   Registration: Not listed in public cell line repositories at time of publication; phyllodes xenograft and cell lines available from corresponding author upon reasonable request.
CC   Population: Chinese (donor ethnicity).
DI   Malignant phyllodes tumor of the breast
OX   Human; NCBI_TaxID=9606
SX   Female
AG   51 years
CA   Cancer cell line
//
"""

    exp_entry = """ID   MPT-S1
DR   cancercelllines; CVCL_B7GV
DR   Wikidata; Q112930125
RX   PubMed=35365682;
CC   Population: Chinese.
CC   Characteristics: Established from a nude mouse xenograft.
CC   Doubling time: 2-3 days (PubMed=35365682).
CC   Sequence variation: Mutation; HGNC; HGNC:7133; KMT2D; Simple; c.6079_6082delAATT; Zygosity=Heterozygous (PubMed=35365682).
CC   Sequence variation: Mutation; HGNC; HGNC:11957; MED12; Simple; p.Gly44Asp (c.131G>A); ClinVar=VCV000092220; Zygosity=Heterozygous (PubMed=35365682).
CC   Sequence variation: Mutation; HGNC; HGNC:9884; RB1; Simple; c.1530_1531delAG; Zygosity=Heterozygous (PubMed=35365682).
CC   Sequence variation: Mutation; HGNC; HGNC:9884; RB1; Simple; c.1588_1589delAA; Zygosity=Heterozygous (PubMed=35365682).
CC   Sequence variation: Mutation; HGNC; HGNC:11998; TP53; Simple; c.750_754delinsA; Zygosity=Heterozygous (PubMed=35365682).
CC   Sequence variation: Mutation; HGNC; HGNC:11998; TP53; Simple; p.Leu252del (c.754_756delCTC); ClinVar=VCV000998484; Zygosity=Heterozygous (PubMed=35365682).
CC   Omics: Genomics; Whole exome sequencing.
CC   Derived from site: In situ; Breast; UBERON=UBERON_0000310.
ST   Source(s): PubMed=35365682
ST   Amelogenin: X
ST   CSF1PO: 12
ST   D10S1248: 13,14
ST   D12S391: 21
ST   D13S317: 9,12
ST   D16S539: 10,11
ST   D18S51: 18
ST   D19S433: 13.2
ST   D1S1656: 11,16
ST   D21S11: 29,30
ST   D22S1045: 14
ST   D2S1338: 23
ST   D2S441: 12
ST   D3S1358: 15,16
ST   D5S818: 11
ST   D7S820: 12
ST   D8S1179: 11,13
ST   DYS391: 9
ST   FGA: 19
ST   Penta D: 9,14
ST   Penta E: 11,19
ST   TH01: 9
ST   TPOX: 8,9
ST   vWA: 14,16
DI   NCIt; C4504; Malignant breast phyllodes tumor
DI   ORDO; Orphanet_180261; Phyllodes tumor of the breast
OX   NCBI_TaxID=9606; ! Homo sapiens (Human)
SX   Female
AG   51Y
CA   Cancer cell line
//
"""


    clsim = ClSimCalc()
    result_dic = clsim.compare_cl_entries(act_entry, exp_entry)
    lines = clsim.get_result_lines(result_dic, ["entry", "CC"])
    for l in lines: print(l)
    
    sys.exit()



    # Sample sentence pairs to compare
    sentence_pairs = [
        ("The cat sits on the mat.", "A cat is sitting on a mat."),
        ("The sky is blue.", "The sky was clear and sunny."),
        ("I love programming.", "I enjoy coding."),
        ("Apples are tasty.", "I like oranges."),
        ("ID   MPT-S1",                                                         "ID   MPT-S1"),
        ("CA   Cancer cell line",                                               "CA   Cancer cell line"),
        ("AG   51Y",                                                            "AG   51 years"),
        ("SX   Female",                                                         "SX   Female"),
        ("OX   NCBI_TaxID=9606; ! Homo sapiens (Human)",                        "OX   Human; NCBI_TaxID=9606"),
        ("DI   ORDO; Orphanet_180261; Phyllodes tumor of the breast",           "DI   Malignant phyllodes tumor of the breast"),
        ("CC   Derived from site: In situ; Breast; UBERON=UBERON_0000310.",     "CC   Derived from site: Trucut biopsy of recurrent chest wall mass (metastatic lesion from left breast phyllodes tumor). A patient‑derived xenograft (PDX) was established in NSG mice and the cell line was derived from enzymatic dissociation of the xenograft after serial transplantation."),
        ("CC   Omics: Genomics; Whole exome sequencing.",                       "CC   Omics: Whole‑exome sequencing (tumor vs matched blood) and whole‑transcriptome sequencing (tumor and cell lines including pazopanib treatment) performed. ENA accessions: PRJEB48011 (WES), PRJEB48016 (RNA‑seq). Transcriptomic analyses and GSEA identified deregulated oncogenic and apoptosis pathways and pazopanib‑mediated downregulation of MMP13, ST6GAL2 and ENPP1."),
        ("CC   Doubling time: 2-3 days (PubMed=35365682).",                     "CC   Doubling time: Approximately 2-3 days (48-72 h)."),
        ("CC   Doubling time: 2-3 days (PubMed=35365682).",                     "CC   Doubling time: Approximately 2–3 days (48–72 h)."),
        ("RX   PubMed=35365682;",                                               "RX   PubMed: 35365682"),
        ("CC   Population: Chinese.",                                           "CC   Population: Chinese (donor ethnicity)."),
        ("CC   Population: Chinese.",                                           ""),
    ]

    # Compute embeddings for all sentences in pairs
    sentences1 = [pair[0] for pair in sentence_pairs]
    sentences2 = [pair[1] for pair in sentence_pairs]

    embeddings1 = model.encode(sentences1, convert_to_tensor=True)
    embeddings2 = model.encode(sentences2, convert_to_tensor=True)

    # Compute cosine similarity between sentence pairs
    cosine_scores = util.cos_sim(embeddings1, embeddings2)

    for i, (sent1, sent2) in enumerate(sentence_pairs):
        log_it("--------------")
        log_it(f"Sentence 1: {sent1}")
        log_it(f"Sentence 2: {sent2}")
        log_it(f"Similarity score: {cosine_scores[i][i].item():.4f}\n")
