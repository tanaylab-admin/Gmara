#!/usr/bin/env python3

import os.path
import pandas as pd
import re
import shutil
import sys
import yaml

from glob import glob

class Namespace:
    def __init__(self, namespaces_dir, name):
        self.name = name
        names_path = f"{namespaces_dir}/names/{name}.tsv"
        print(f"Load {name} names ...", flush = True)
        frame = pd.read_csv(names_path, dtype = str, keep_default_na = False, header = "infer", sep = "\t")
        self.gene_names = set(frame.loc[:, "name"])

class NamespaceMap:
    def __init__(self, namespaces_dir, from_name, to_name):
        names_path = f"{namespaces_dir}/names/{from_name}.{to_name}.tsv"
        print(f"Load mapping from {from_name} to {to_name} ...", flush = True)
        frame = pd.read_csv(names_path, dtype = str, keep_default_na = False, header = "infer", sep = "\t")
        from_gene_names = frame.loc[:, "from"]
        to_gene_names = frame.loc[:, "to"]
        self.map = {}
        for from_gene_name, to_gene_name in zip(from_gene_names, to_gene_names):
            if from_gene_name not in self.map:
                self.map[from_gene_name] = set()
            self.map[from_gene_name].add(to_gene_name)

class Names:
    def __init__(self, sources_dir, namespaces_dir):
        self.namespaces_dir = namespaces_dir
        self.sources_dir = sources_dir
        self.namespaces = {}
        self.gene_names = {}

        for namespace_path in os.listdir(f"{namespaces_dir}/names"):
            base_path = os.path.basename(namespace_path)
            parts = base_path.split(".")
            if len(parts) == 2:
                namespace_name = parts[0]
                self.namespaces[namespace_name] = Namespace(namespaces_dir, namespace_name)
                self.gene_names[namespace_name] = set()

        self.namespaces_maps = {}
        for from_namespace_name in self.namespaces:
            self.namespaces_maps[from_namespace_name] = {}
            for to_namespace_name in self.namespaces:
                self.namespaces_maps[from_namespace_name][to_namespace_name] = \
                    NamespaceMap(namespaces_dir, from_namespace_name, to_namespace_name)

    def collect_source(self, sources_spec):
        data_path = f"{self.sources_dir}/{sources_spec["data_file"]}"
        has_header = sources_spec.get("has_header", True)
        frame = pd.read_csv(
            data_path,
            dtype = str,
            keep_default_na = False,
            header="infer" if has_header else None,
            sep = "," if data_path.endswith(".csv") else "\t",
            comment = "#",
        )

        for column, namespace_name in sources_spec["columns"].items():
            print(f"Collect sources/{sources_spec["data_file"]} / {column} -> {namespace_name} ...", flush = True)
            if isinstance(column, int):
                gene_names = frame.iloc[:, column].values
            else:
                gene_names = frame.loc[:, column].values
            self.add_names(namespace_name, gene_names)

    def add_names(self, namespace_name, gene_names):
        self.gene_names[namespace_name].update(gene_names)
        if "" in self.gene_names[namespace_name]:
            self.gene_names[namespace_name].remove("")

    def verify_names(self):
        for namespace_name, gene_names in self.gene_names.items():
            print(f"Verify names {namespace_name} ...")

            ignored_path = f"{self.namespaces_dir}/sources/{namespace_name}.Ignored.txt"
            if os.path.isfile(ignored_path):
                ignored_names = set([gene_name[:-1] for gene_name in open(ignored_path).readlines()])
                gene_names -= ignored_names
            else:
                ignored_names = set()


            missing_path = f"{self.namespaces_dir}/sources/{namespace_name}.Missing.txt"
            if os.path.isfile(missing_path):
                os.remove(missing_path)

            missing_names = set()
            namespace = self.namespaces[namespace_name]
            for gene_name in sorted(gene_names):
                if gene_name not in namespace.gene_names \
                        and gene_name not in ignored_names \
                        and gene_name not in missing_names:
                    missing_names.add(gene_name)

            if len(missing_names) > 0:
                gene_names -= missing_names
                with open(missing_path, "a") as file:
                    for gene_name in sorted(missing_names):
                        print(f"The gene: '{gene_name}' is missing from the namespace: {namespace_name}")
                        print(f"{gene_name}", file = file)

    def complete_names(self):
        print("Complete names ...")
        queue = []
        for namespace_name, gene_names in self.gene_names.items():
            for gene_name in gene_names:
                self.complete_name(namespace_name, gene_name, queue, to_add = False)
        while len(queue) != 0:
            namespace_name, gene_name = queue.pop()
            self.complete_name(namespace_name, gene_name, queue, to_add = True)

    def complete_name(self, namespace_name, gene_name, queue, *, to_add):
        if to_add:
            gene_names = self.gene_names[namespace_name]
            if gene_name in gene_names:
                return
            gene_names.add(gene_name)

        for other_namespace_name, map_to_other_namespace in self.namespaces_maps[namespace_name].items():
            other_namespace_gene_names = self.gene_names[other_namespace_name]
            if gene_name in map_to_other_namespace.map:
                for other_gene_name in map_to_other_namespace.map[gene_name]:
                    if other_gene_name not in self.gene_names[other_namespace_name]:
                        queue.append((other_namespace_name, other_gene_name))

    def write(self, names_dir):
        if os.path.exists(names_dir):
            shutil.rmtree(names_dir)
        os.mkdir(names_dir)

        for namespace_name, namespace_gene_names in self.gene_names.items():
            print(f"Write names/{namespace_name}.tsv ...", flush = True)
            with open(f"{names_dir}/{namespace_name}.tsv", "w") as file:
                print("name", file=file)
                for gene_name in sorted(namespace_gene_names):
                    print(gene_name, file=file)

def main():
    assert len(sys.argv) == 3, "Usage: compute_list.py species list"
    species = sys.argv[1]
    list_name = sys.argv[2]

    sources_yaml = f"genes/{species}/lists/{list_name}/sources/sources.yaml"
    with open(sources_yaml) as file:
        sources_spec = yaml.safe_load(file)

    sources_dir = f"genes/{species}/lists/{list_name}/sources"
    namespaces_dir = f"genes/{species}/namespaces"
    names = Names(sources_dir, namespaces_dir)
    for source_spec in sources_spec:
        names.collect_source(source_spec)
    names.verify_names()
    names.complete_names()

    names_dir = f"genes/{species}/namespaces/names"
    names.write(names_dir)

if __name__ == "__main__":
    main()
