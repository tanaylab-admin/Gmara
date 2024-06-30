#!/usr/bin/env python3

import json
import os
import requests
import sys
import time

def main():
    assert len(sys.argv) == 2, "Usage: complete_namespaces.py genes/species"

    root_dir = f"{sys.argv[1]}/namespaces"
    assert os.path.isdir(root_dir), f"not a directory: {root_dir}"

    sources_dir = f"{root_dir}/sources"
    assert os.path.isdir(sources_dir), f"not a directory: {sources_dir}"

    for name in os.listdir(sources_dir):
        if name.endswith("_Missing_from_Lists.txt"):
            namespace_name = name[:-23]
            complete_namespace(namespace_name, sources_dir)

def complete_namespace(namespace_name, sources_dir):
    print(f"Complete identifiers for {namespace_name} ...")
    complete_function = globals().get(f"complete_{namespace_name}")
    missing_names = set()
    for gene_name in sorted(set(open(f"{sources_dir}/{namespace_name}_Missing_from_Lists.txt").readlines())):
        gene_name = gene_name[:-1]
        if gene_name in missing_names:
            continue
        missing_names.add(gene_name)
        if complete_function is None:
            print(f"Don't know how to lookup the missing gene: '{gene_name}' in the namespace: {namespace_name}")
        else:
            complete_function(sources_dir, gene_name)

def complete_Ensembl(sources_dir, ensembl_id):
    url = f"http://tark.ensembl.org/api/transcript/search/?identifier_field={ensembl_id}&expand=genes"
    time.sleep(0.01)  # Throttle requests to avoid appearing to be a DDOS attack.
    page = requests.get(url)
    data = json.loads(page.content)
    active_ids = set()
    for datum in data:
        stable_id = datum.get("stable_id", ensembl_id)
        if stable_id != ensembl_id:
            active_ids.add(stable_id)
        for gene in datum.get("genes", []):
            stable_id = gene.get("stable_id", ensembl_id)
            if stable_id != ensembl_id:
                active_ids.add(stable_id)
    if len(active_ids) == 0:
        print(f"The gene: '{ensembl_id}' is truly missing from the namespace: Ensembl")
    else:
        print(f"Found {len(active_ids)} mappings for the missing Ensembl {ensembl_id} ...")
        store_extra(sources_dir, "Ensembl.Extra.tsv", ensembl_id, active_ids)

def store_extra(sources_dir, extra_path, gene_name, other_gene_names):
    with open(f"{sources_dir}/{extra_path}", "a+") as file:
        for other_gene_name in sorted(other_gene_names):
            print(f"{gene_name}\t{other_gene_name}", file = file)

if __name__ == "__main__":
    main()
