import os
import sys
from cl_sim_calc import ClSimCalc
from publi_cl_pairs_factory import PubliClPairsFactory
from cl_text_generator import ClTextGenerator
from utils import log_it



# =================================================================================
if __name__ == '__main__':
# =================================================================================

    cl_generator = ClTextGenerator()

    cl_comparator = ClSimCalc()

    pairs_factory = PubliClPairsFactory()
    pairs_factory.load_pairs()
    pair = pairs_factory.pairs[0]
    log_it(pair)
    data = pairs_factory.get_example_data(pair)
    expected_cl = data["cello_text"]
    publi_text = data["publi_text"]
    generated_cl = cl_generator.generate_cl(publi_text)
    result = cl_comparator.compare_cl_entries(generated_cl, expected_cl)
    sim_result_lines = "\n".join(cl_comparator.get_result_lines(result))
    #log_it(f"\n-------- response details ----------------\n\n{response}")
    log_it(f"\n-------- assistant response --------------\n\n{generated_cl}")
    log_it(f"\n-------- expected  response --------------\n\n{expected_cl}")
    log_it(f"\n-------- function calls ------------------\n\n")
    for fc in cl_generator.funcalls: print(fc)
    log_it(f"\n-------- similarity ----------------------\n\n{sim_result_lines}")
    log_it(f"\n-------- end --------")
