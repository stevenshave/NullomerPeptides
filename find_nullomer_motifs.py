
"""
Identify motifs which account for nullomer peptides

Reading in files containing counts of unique peptides at certain lengths,
generate motifs (20 AAs + any AA) and count how many times the motif
accounts for a nullomer peptide.  This allows identification of sequences that
life does not like to make.  Motifs are not queried in reverse, so M..C would
match MWWC, and not CWWM.
"""

__author__ = "Steven Shave"
__version__ = "1.0.0"
__license__ = "MIT"

import argparse, gzip
from itertools import product
import numpy as np


import numpy as np
def count_motif_in_peptide(motif, peptide):
    truemask=[p=="." for p in motif]
    num_matches=0
    for i in range(0,len(peptide)-len(motif)+1):
        num_matches+=np.sum(all([truemask[p]|[motif[j]==peptide[i+j] for j in range(len(motif))][p] for p in range(len(motif))]))
    return num_matches

from nullomer_codon_counter import CodonCounter

def find_nullomer_motifs(input_filename:str, output_filename, pattern_length):
    """ 
    Function to explore all possible motifs of lenght pattern_length and count
    how well they define nullomers present in input_filename.  Writes csv to
    output_filename.
    """
    
    # Valid amino acids plus . to represent any AA.  Dot is regex for any char.
    aas="ARNDCEQGHILKMFPSTWYV."
   
    # Enumerate all combinations of chars in aas. 
    patterns=set(product(*[aas]*pattern_length))
    print(f"Finding {pattern_length}-mer motifs in {input_filename}")
    
    # Occurences dictionary holds number of pattern matches
    occurences={}
    print("Number of regex motif queries=", len(patterns))
    nullomer_counter=0
    
    input_file=None
    if input_filename[-3:]==".gz":
        input_file=gzip.open(input_filename, 'rt')
    else:
        input_file=open(input_filename)

    for line_it, line in enumerate(input_file.readlines()):
        if line_it==0: continue # Skip file header
        if line_it%10000==0: # Progress counter
            print(line_it)
        if line.find(",")==-1:continue # If line does not contain a comma, skip
        if int(line.split(",")[-1])>0:continue # If not a nullomer, skip
        nullomer_counter+=1
        for pattern in patterns:
            regex_result=count_motif_in_peptide(pattern, line.split(",")[0])
            if regex_result>0: # If regex matches, add to dict or increment
                if pattern in occurences.keys():
                    occurences[pattern]+=regex_result
                else:
                    occurences[pattern]=regex_result
    input_file.close()
    output_file=None
    codon_counter=CodonCounter()
    file_header=f"{'Motif,':>10}{'Count,':>10}{'%Match,':>10}{'ExpectedRateByCodons,':>25}{'ExpectedRateByAARates,':>25}{'(TotalNullomers='+str(nullomer_counter)+')':>20}\n"
    output_file=None
    writing_compressed=False
    if output_filename[-3:]==".gz": # Writing compressed gz file
        writing_compressed=True
        output_file=gzip.open(output_filename,"wb")
        output_file.write(file_header.encode())
    else:
        output_file=open(output_filename, "w")
        output_file.write(file_header)

        
    for l in sorted(occurences.items(), key=lambda x: x[1], reverse=True):
        expected_rate_by_codons=codon_counter.get_codon_occurrence_rate_for_peptide(l[0])
        expected_rate_by_aa_occurrences=codon_counter.get_uniprot_observed_occurrence_rate_for_peptide(l[0])
        line_to_write=f"{''.join(l[0])+',':>10}{str(l[1])+',':>10}{(100*l[1]/nullomer_counter):>8.3f}%,{expected_rate_by_codons:>24.5E},{expected_rate_by_aa_occurrences:>24.5E},\n"
        if writing_compressed:
            output_file.write(line_to_write.encode())
        else:
            output_file.write(line_to_write)
    output_file.close()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument("input_filename", help="File containing peptides and counts comma separated")
    parser.add_argument("output_filename",
                        help="File to output motif hit counts to")
    parser.add_argument("motif_length",
                        help="File containing sequences", type=int)

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    find_nullomer_motifs(args.input_filename, args.output_filename,
                       args.motif_length)