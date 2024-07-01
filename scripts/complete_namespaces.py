#!/usr/bin/env python3

import json
import os
import requests
import sys
import time

def main():
    assert len(sys.argv) == 2, "Usage: complete_namespaces.py species"
    species = sys.argv[1]

    sources_dir = f"genes/{species}/namespaces/sources"
    for name in os.listdir(sources_dir):
        if name.endswith(".Missing.txt"):
            namespace_name = name[:-12]
            complete_namespace(namespace_name, sources_dir)

def complete_namespace(namespace_name, sources_dir):
    print(f"Complete identifiers for {namespace_name} ...")
    complete_function = globals().get(f"complete_{namespace_name}")

    missing_path = f"{sources_dir}/{namespace_name}.Missing.txt"
    if os.path.isfile(missing_path):
        missing_names = set(open(missing_path))
    else:
        missing_names = set()

    ignored_path = f"{sources_dir}/{namespace_name}.Ignored.txt"
    if os.path.isfile(ignored_path):
        ignored_names = set(open(ignored_path))
    else:
        ignored_names = set()

    for gene_name in sorted(missing_names):
        gene_name = normalize_name(namespace_name, gene_name[:-1])
        if gene_name not in ignored_names \
                and (complete_function is None or not complete_function(sources_dir, gene_name)):
            ignored_names.add(gene_name)
            print(f"The missing gene: '{gene_name}' will be ignored from the namespace: {namespace_name}")
            with open(ignored_path, "a") as file:
                print(gene_name, file = file)

    if os.path.isfile(missing_path):
        os.remove(missing_path)

def complete_Ensembl(sources_dir, ensembl_id):
    url = f"http://tark.ensembl.org/api/transcript/search/?identifier_field={ensembl_id}&expand=genes"
    time.sleep(0.01)  # Throttle requests to avoid appearing to be a DDOS attack.
    page = requests.get(url)
    data = json.loads(page.content)

    active_ids = set()
    for datum in data:
        stable_id = normalize_name("Ensembl", datum.get("stable_id", ensembl_id))
        if stable_id != ensembl_id:
            active_ids.add(stable_id)
        for gene in datum.get("genes", []):
            stable_id = normalize_name("Ensembl", gene.get("stable_id", ensembl_id))
            if stable_id != ensembl_id:
                active_ids.add(stable_id)

    if len(active_ids) == 0:
        return False

    store_extra(sources_dir, "Ensembl.Extra.tsv", ensembl_id, active_ids)
    print(f"Found {len(active_ids)} mappings for the missing Ensembl {ensembl_id}")
    return True

def complete_Symbol(sources_dir, symbol):
    url = f"http://api.genome.ucsc.edu/search?search={symbol}&genome=hg38"
    time.sleep(0.01)
    page = requests.get(url)
    data = json.loads(page.content)

    symbols = set()
    ensembl_ids = set()

    for positionMatch in data["positionMatches"]:
        for match in positionMatch["matches"]:
            position = match["position"]
            chromosome, locations = position.split(":")
            start, end = locations.split("-")
            chromosome = chromosome[3:]
            time.sleep(0.01)
            match_url = f"https://rest.ensembl.org/overlap/region/human/{chromosome}:{start}:{end}?feature=gene;content-type=application/json"
            match_page = requests.get(match_url)
            match_data = json.loads(match_page.content)
            for match_datum in match_data:
                if "external_name" in match_datum:
                    symbols.add(normalize_name("Symbol", match_datum["external_name"]))
                if "gene_id" in match_datum:
                    ensembl_ids.add(normalize_name("Ensembl", match_datum["gene_id"]))
                if "canonical_transcript" in match_datum:
                    ensembl_ids.add(normalize_name("Ensembl", match_datum["canonical_transcript"]))

    if len(symbols) > 0:
        print(f"Found {len(symbols)} Symbol mappings for the missing Symbol {symbol}")
        store_extra(sources_dir, "Symbol.Extra.tsv", symbol, symbols)

    if len(ensembl_ids) > 0:
        print(f"Found {len(ensembl_ids)} Ensembl mappings for the missing Symbol {symbol}")
        store_extra(sources_dir, "Symbol.Ensembl.Extra.tsv", symbol, ensembl_ids)

    return len(symbols) + len(ensembl_ids) > 0

def normalize_name(namespace_name, name):
    if namespace_name == "UCSC":
        return name
    parts = name.split(".")
    if len(parts) == 2:
        return parts[0]
    else:
        return name

def store_extra(sources_dir, extra_path, gene_name, other_gene_names):
    with open(f"{sources_dir}/{extra_path}", "a+") as file:
        for other_gene_name in sorted(other_gene_names):
            print(f"{gene_name}\t{other_gene_name}", file = file)

if __name__ == "__main__":
    main()
