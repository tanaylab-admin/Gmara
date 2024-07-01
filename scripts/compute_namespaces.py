#!/usr/bin/env python3

import os.path
import pandas as pd
import re
import shutil
import sys
import yaml

class Gene:
    def __init__(self, name, is_alternative):
        self.name = name
        self.is_alternative = is_alternative
        self.links = set()

class Namespace:
    def __init__(self, name):
        self.name = name
        self.genes = {}

class Namespaces:
    def __init__(self, sources_dir):
        self.sources_dir = sources_dir
        self.namespaces = {}

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

        columns = []
        for column, column_spec in sources_spec["columns"].items():
            namespace_name = column_spec["namespace"]
            is_alternative = column_spec.get("is_alternative", False)
            if isinstance(column, int):
                data = frame.iloc[:, column].values
            else:
                data = frame.loc[:, column].values
            columns.append((namespace_name, is_alternative, data))

        for first_column in range(len(columns)):
            first_namespace_name, first_is_alternative, first_gene_names = columns[first_column]
            print(f"Collect sources/{sources_spec["data_file"]} / {first_column} -> {first_namespace_name} ...", flush = True)
            for row in range(frame.shape[0]):
                self.add_names(first_namespace_name, first_is_alternative, split_names(first_gene_names[row]))
            for second_column in range(first_column):
                second_namespace_name, second_is_alternative, second_gene_names = columns[second_column]
                print(f"Collect sources/{sources_spec["data_file"]} / {first_column} -> {first_namespace_name} / {second_column} -> {second_namespace_name} ...", flush = True)
                for row in range(frame.shape[0]):
                    self.link_names(
                        first_namespace_name,
                        split_names(first_gene_names[row]),
                        second_namespace_name,
                        split_names(second_gene_names[row]),
                    )

    def add_names(self, namespace_name, is_alternative, gene_names):
        if namespace_name not in self.namespaces:
            self.namespaces[namespace_name] = Namespace(namespace_name)
        namespace = self.namespaces[namespace_name]
        for gene_name in gene_names:
            if gene_name != "":
                if gene_name not in namespace.genes:
                    namespace.genes[gene_name] = Gene(gene_name, is_alternative)
                elif is_alternative:
                    namespace.genes[gene_name].is_alternative = True

    def link_names(self, first_namespace_name, first_gene_names, second_namespace_name, second_gene_names):
        first_namespace = self.namespaces[first_namespace_name]
        second_namespace = self.namespaces[second_namespace_name]
        for first_gene_name in first_gene_names:
            if first_gene_name != "":
                for second_gene_name in second_gene_names:
                    if second_gene_name != "":
                        first_namespace.genes[first_gene_name].links.add((second_namespace_name, second_gene_name))
                        second_namespace.genes[second_gene_name].links.add((first_namespace_name, first_gene_name))

    def collect_extra(self):
        for namespace_name in self.namespaces:
            self.collect_extra_namespace(namespace_name)
            for other_namespace_name in self.namespaces:
                if namespace_name < other_namespace_name:
                    self.collect_extra_namespaces(namespace_name, other_namespace_name)

    def collect_extra_namespace(self, namespace_name):
        namespace = self.namespaces[namespace_name]
        extra_path = f"{self.sources_dir}/{namespace_name}.Extra.tsv"
        if os.path.isfile(extra_path):
            print(f"Collect sources/{namespace_name}.Extra.tsv ...")
            frame = pd.read_csv(
                extra_path,
                dtype = str,
                keep_default_na = False,
                header=None,
                sep = "\t",
            )
            first_gene_names = frame.iloc[:, 0].values
            second_gene_names = frame.iloc[:, 1].values
            self.add_names(namespace_name, True, first_gene_names)
            self.add_names(namespace_name, False, second_gene_names)
            self.link_names(namespace_name, first_gene_names, namespace_name, second_gene_names)

    def collect_extra_namespaces(self, first_namespace_name, second_namespace_name):
        first_namespace = self.namespaces[first_namespace_name]
        second_namespace = self.namespaces[second_namespace_name]
        extra_path = f"{self.sources_dir}/{first_namespace_name}.{second_namespace_name}.Extra.tsv"
        if os.path.isfile(extra_path):
            print(f"Collect sources/{first_namespace_name}.{second_namespace_name}.Extra.tsv ...")
            frame = pd.read_csv(
                extra_path,
                dtype = str,
                keep_default_na = False,
                header=None,
                sep = "\t",
            )
            first_gene_names = frame.iloc[:, 0].values
            second_gene_names = frame.iloc[:, 1].values
            self.add_names(first_namespace_name, True, first_gene_names)
            self.add_names(second_namespace_name, False, second_gene_names)
            self.link_names(first_namespace_name, first_gene_names, second_namespace_name, second_gene_names)

    def complete_links(self):
        for namespace_name in self.namespaces:
            print(f"Complete links {namespace_name} ...", flush = True)
            for gene_name in self.namespaces[namespace_name].genes:
                self.complete_name_links(namespace_name, gene_name)

    def complete_name_links(self, from_namespace_name, from_gene_name):
        from_gene = self.namespaces[from_namespace_name].genes[from_gene_name]
        from_links = from_gene.links
        from_is_alternative = from_gene.is_alternative
        queue = list(from_gene.links)
        while len(queue) > 0:
            link = queue.pop()
            if link not in from_links:
                to_namespace_name, to_gene_name = link
                to_gene = self.namespaces[to_namespace_name].genes[to_gene_name]
                if from_is_alternative or link_namespace_name != namespace_name:
                    from_links.add(link)
                    queue.extend(to_gene.links)

    def ensure_canonical(self):
        for namespace_name in self.namespaces:
            print(f"Ensure canonical {namespace_name} ...", flush = True)
            for gene_name in self.namespaces[namespace_name].genes:
                self.ensure_canonical_gene(namespace_name, gene_name)

    def ensure_canonical_gene(self, namespace_name, gene_name):
        gene = self.namespaces[namespace_name].genes[gene_name]
        if not gene.is_alternative:
            return
        first_gene_name = gene_name
        for link in gene.links:
            link_namespace_name, link_gene_name = link
            if link_namespace_name == namespace_name:
                link_gene = self.namespaces[namespace_name].genes[link_gene_name]
                if not link_gene.is_alternative:
                    return
                if link_gene_name < first_gene_name:
                    first_gene_name = link_gene_name
        if first_gene_name == gene_name:
            gene.is_alternative = False

    def write(self, names_dir):
        if os.path.exists(names_dir):
            shutil.rmtree(names_dir)
        os.mkdir(names_dir)

        for namespace_name in self.namespaces:
            self.write_namespace(namespace_name, names_dir)
            for namespace2_name in self.namespaces:
                self.write_namespaces(namespace_name, namespace2_name, names_dir)

    def write_namespace(self, namespace_name, names_dir):
        print(f"Write names/{namespace_name}.tsv ...", flush = True)
        with open(f"{names_dir}/{namespace_name}.tsv", "w") as file:
            print("name\tis_canonical", file=file)
            genes = self.namespaces[namespace_name].genes
            for gene_name, gene in sorted(genes.items()):
                print(f"{gene_name}\t{not gene.is_alternative}", file=file)

    def write_namespaces(self, namespace1_name, namespace2_name, names_dir):
        print(f"Write names/{namespace1_name}.{namespace2_name}.tsv ...", flush = True)
        with open(f"{names_dir}/{namespace1_name}.{namespace2_name}.tsv", "w") as file:
            print("from\tto", file=file)
            genes1 = self.namespaces[namespace1_name].genes
            for gene_name1, gene_data1 in sorted(genes1.items()):
                for link in gene_data1.links:
                    link_namespace_name, link_gene_name = link
                    if link_namespace_name == namespace2_name:
                        link_gene = self.namespaces[link_namespace_name].genes[link_gene_name]
                        if not link_gene.is_alternative:
                            print(f"{gene_name1}\t{link_gene_name}", file=file)

def split_names(names):
    return [normalize_name(name) for name in re.split(r"[| ,;\t]", names)]

def normalize_name(name):
    if not name.startswith("ENS"):
        return name
    parts = name.split(".")
    if len(parts) == 2:
        return parts[0]
    else:
        return name

def main():
    assert len(sys.argv) == 2, "Usage: compute_namespaces.py species"
    species = sys.argv[1]

    sources_dir = f"genes/{species}/namespaces/sources"
    sources_yaml = f"genes/{species}/namespaces/sources/sources.yaml"
    with open(sources_yaml) as file:
        sources_spec = yaml.safe_load(file)

    namespaces = Namespaces(sources_dir)
    for source_spec in sources_spec:
        namespaces.collect_source(source_spec)
    namespaces.collect_extra()
    namespaces.complete_links()
    namespaces.ensure_canonical()

    names_dir = f"genes/{species}/namespaces/names"
    namespaces.write(names_dir)

if __name__ == "__main__":
    main()
