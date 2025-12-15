import os
import sys
from sentence_transformers import SentenceTransformer
import numpy as np
from utils import log_it

class DictionarySearcher:
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        model_name: (optional) SentenceTransformer model name
        """
        log_it(f"INFO Loading sentence transformer model {model_name}")
        self.model = SentenceTransformer(model_name)
        self.termi_dir = "terminologies"
        self.dictionaries = dict()
        self.load_disease_terms()   
        self.load_anatomy_terms()


    def add_dictionary(self, dict_name, lines):
        """
        dict_name: the name of the dictionary
        lines: a list of terms in tsv format: db TAB id TAB pref_name TAB name
        """
        self.dictionaries[dict_name] = { "embeddings": list(), "meta": list() }
        dict = self.dictionaries[dict_name]
        terms = list()
        for t in lines:
            db, id, pref_name, name = t.strip().split("\t")
            terms.append(name)
            dict["meta"].append( { "db":db, "id":id, "pref_name":pref_name, "name": name } )

        embed_file = f"{self.termi_dir}/{dict_name}.embeddings.npy"
        if os.path.exists(embed_file):
            dict["embeddings"] =  np.load(embed_file)
        else:
            dict["embeddings"] = self.model.encode(terms, convert_to_numpy=True, normalize_embeddings=True)
            np.save(embed_file,  dict["embeddings"])


    def search(self, dict_name, query_term):
        """
        query_term: input disease name/phrase (string)
        Returns: (matched_term, identifier, similarity_score)
        """
        query_emb = self.model.encode(query_term, convert_to_numpy=True, normalize_embeddings=True)
        # Compute cosine similarities using dot product, since vectors are normalized
        dict = self.dictionaries[dict_name]
        similarities = np.dot(dict["embeddings"], query_emb)
        max_idx = np.argmax(similarities)
        best_term = dict["meta"][max_idx]
        return best_term, float(similarities[max_idx])


    def search_top_k(self, dict_name, query_term, k=3):
        query_emb = self.model.encode(query_term, convert_to_numpy=True, normalize_embeddings=True)
        dict = self.dictionaries[dict_name]
        similarities = np.dot(dict["embeddings"], query_emb)
        top_k_idx = np.argpartition(-similarities, k-1)[:k]  # Get indices of top k similar terms (unsorted)
        top_k_idx = top_k_idx[np.argsort(-similarities[top_k_idx])]  # Sort top k indices by similarity descending
        results = []
        for idx in top_k_idx:
            results.append((dict["meta"][idx], float(similarities[idx])))
        return results


    def load_disease_terms(self):
        log_it("INFO Loading disease terms")
        lines = open(f"{self.termi_dir}/ORDO.tsv").readlines()
        if lines[0].startswith("db\tid"): del lines[0]          # remove header line
        lines2 = open(f"{self.termi_dir}/NCIt_DI.tsv").readlines()
        if lines2[0].startswith("db\tid"): del lines2[0]        # remove header line
        lines.extend(lines2)
        self.add_dictionary("disease", lines)


    def load_anatomy_terms(self):
        log_it("INFO Loading anatomy terms")
        lines = open(f"{self.termi_dir}/UBERON.tsv").readlines()
        if lines[0].startswith("db\tid"): del lines[0]          # remove header line
        self.add_dictionary("anatomy", lines)


if __name__ == '__main__':

    lines = """
    disease; C101029; Atrioventricular septal defect
    disease; C101200; Neonatal alloimmune thrombocytopenia
    disease; C101201; Myelomeningocele
    disease; C101214; Spina bifida
    disease; Orphanet_1047; Sideroblastic anemia
    disease; Orphanet_1048; Isolated anencephaly/exencephaly
    disease; Orphanet_104; Leber hereditary optic neuropathy
    disease; Orphanet_1052; Mosaic variegated aneuploidy syndrome
    disease; Orphanet_1071; Ankyloblepharon-ectodermal defects-cleft lip/palate syndrome
    disease; Orphanet_107; BOR syndrome
    anatomy; UBERON_0000029; Right lymph node
    anatomy; UBERON_0036014; Right posterior thigh adjacent to buttocks, hypodermis
    anatomy; UBERON_0002072; Right posterior thigh adjacent to buttocks, hypodermis
    anatomy; UBERON_0008779; Right subclavius, hypodermis
    """.split("\n")

    searcher = DictionarySearcher()
    log_it("INFO Term searcher initialized")
 
    if len(sys.argv) == 3:
        dico = sys.argv[1]
        term = sys.argv[2]
        print(f"\nTerm searched: {term} \n")
        for best_term, score in searcher.search_top_k(dico, term, 5):
            print(f"{score:.5f}", best_term)
        exit(0)
 
    for line in lines:
        line = line.strip()
        if line == "" : continue
        dico, id, term = line.split("; ")
        print("------------------------")
        print("Searching", dico, id, term)
        print("------------------------")
        for best_term, score in searcher.search_top_k(dico, term, 5):
            score_str = round(score, 5)
            if best_term["id"] == id:
                print(f"MATCH {score:.5f}", best_term)
            else:
                print(f"close {score:.5f}", best_term)
    log_it("End")
