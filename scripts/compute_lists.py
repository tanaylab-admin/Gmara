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
        names_path = f"{namespaces_dir}/{name}.tsv"
        print(f"Load {name} names ...", flush = True)
        assert os.path.isfile(names_path), f"not a file: {names_path}"
        frame = pd.read_csv(names_path, dtype = str, keep_default_na = False, header = "infer", sep = "\t")
        self.gene_names = set(frame.loc[:, "name"])

class NamespaceMap:
    def __init__(self, namespaces_dir, from_name, to_name):
        names_path = f"{namespaces_dir}/{from_name}.{to_name}.tsv"
        print(f"Load mapping from {from_name} to {to_name} ...", flush = True)
        assert os.path.isfile(names_path), f"not a file: {names_path}"
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

        for namespace_path in os.listdir(namespaces_dir):
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
        assert os.path.isfile(data_path), f"not a file: {data_path}"
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
            file = None
            namespace = self.namespaces[namespace_name]
            for gene_name in sorted(gene_names):
                if gene_name not in namespace.gene_names:
                    print(f"The gene: '{gene_name}' is missing from the namespace: {namespace_name}")
                    if file is None:
                        file = open(f"{self.namespaces_dir}/../sources/{namespace_name}_Missing_from_Lists.txt", "a")
                    print(f"{gene_name}", file = file)
            gene_names &= namespace.gene_names
            if file is not None:
                file.close()

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
    assert len(sys.argv) == 2, "Usage: compute_namespaces.py genes/<organism>/lists/<list>"

    root_dir = sys.argv[1]
    assert os.path.isdir(root_dir), f"not a directory: {root_dir}"

    namespaces_dir = f"{root_dir}/../../namespaces/names"
    assert os.path.isdir(namespaces_dir), f"not a directory: {namespaces_dir}"

    sources_dir = f"{root_dir}/sources"
    assert os.path.isdir(sources_dir), f"not a directory: {sources_dir}"

    sources_yaml = f"{root_dir}/sources/sources.yaml"
    assert os.path.isfile(sources_yaml), f"not a file: {sources_yaml}"
    with open(sources_yaml) as file:
        sources_spec = yaml.safe_load(file)

    names = Names(sources_dir, namespaces_dir)
    for source_spec in sources_spec:
        names.collect_source(source_spec)
    names.verify_names()
    names.complete_names()

    names_dir = f"{root_dir}/names"
    names.write(names_dir)

if __name__ == "__main__":
    main()
