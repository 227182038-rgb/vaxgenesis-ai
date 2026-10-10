"""Module 1 - Genome Analysis Engine: ORF prediction, GC content, codon usage."""
from __future__ import annotations
from typing import Any
from vaxgenesis.modules.base import BaseModule, ModuleResult

class GenomeAnalysisModule(BaseModule):
    module_id = "genome_analysis"
    module_name = "Genome Analysis Engine"
    description = "Module 1 - Genome Analysis Engine: ORF prediction, GC content, codon usage."
    category = "perception"
    inputs = ['reference_genome']
    outputs = ['orfs', 'cds', 'protein_list', 'gc_content', 'codon_usage']
    default_model_version = "1.0.0"

GENETIC_CODE={"TTT":"F","TTC":"F","TTA":"L","TTG":"L","CTT":"L","CTC":"L","CTA":"L","CTG":"L","ATT":"I","ATC":"I","ATA":"I","ATG":"M","GTT":"V","GTC":"V","GTA":"V","GTG":"V","TCT":"S","TCC":"S","TCA":"S","TCG":"S","CCT":"P","CCC":"P","CCA":"P","CCG":"P","ACT":"T","ACC":"T","ACA":"T","ACG":"T","GCT":"A","GCC":"A","GCA":"A","GCG":"A","TAT":"Y","TAC":"Y","TAA":"*","TAG":"*","CAT":"H","CAC":"H","CAA":"Q","CAG":"Q","AAT":"N","AAC":"N","AAA":"K","AAG":"K","GAT":"D","GAC":"D","GAA":"E","GAG":"E","TGT":"C","TGC":"C","TGA":"*","TGG":"W","CGT":"R","CGC":"R","CGA":"R","CGG":"R","AGT":"S","AGC":"S","AGA":"R","AGG":"R","GGT":"G","GGC":"G","GGA":"G","GGG":"G"}
START={"ATG"}; STOP={"TAA","TAG","TGA"}; COMP=str.maketrans("ATCGN","TAGCN")
def _find_orfs(seq,min_len=90):
    orfs=[]
    for strand,s in [("+",seq),("-",s.translate(COMP)[::-1])]:
        for frame in range(3):
            i=frame
            while i<len(s)-2:
                if s[i:i+3] in START:
                    j=i+3
                    while j<len(s)-2:
                        if s[j:j+3] in STOP:
                            if (j+3-i)>=min_len: orfs.append({"start":i,"end":j+3,"strand":strand,"sequence":s[i:j+3]})
                            i=j+3; break
                        j+=3
                    else: break
                else: i+=3
    return orfs
def _translate(dna):
    p=[]
    for i in range(0,len(dna)-2,3):
        aa=GENETIC_CODE.get(dna[i:i+3],"X")
        if aa=="*": break
        p.append(aa)
    return "".join(p)
def _gc(seq):
    gc=sum(1 for c in seq if c in "GC"); at=sum(1 for c in seq if c in "AT")
    return round(gc/max(1,gc+at),4)
async def run(self,inputs):
    genome=inputs.get("reference_genome","").upper().replace("U","T")
    orfs=_find_orfs(genome)
    proteins=[{"sequence":_translate(o["sequence"]),"start":o["start"],"end":o["end"],"strand":o["strand"],"length":len(_translate(o["sequence"]))} for o in orfs if _translate(o["sequence"]) and not _translate(o["sequence"]).endswith("X")]
    return ModuleResult(outputs={"orfs":orfs,"cds":[p["sequence"] for p in proteins],"protein_list":proteins,"gc_content":_gc(genome),"genome_length":len(genome),"orf_count":len(orfs),"protein_count":len(proteins)},model_version=self.default_model_version)
def score_uncertainty(self,result,inputs):
    n=result.outputs.get("protein_count",0); return 0.6 if(n<5 or n>200) else 0.2
