# Gmara
Genes Manifests Archive for RNA Analysis

## Motivation

This repository holds lists of genes for use in scRNA-seq analysis.
They are stored in machine-readable format so they can be used by software, directly from this repository, optionally with commit tags to ensure reproducability.

The intent is that these lists be used as *initial* lists for analysis (e.g., provide initial list of lateral genes for metacells analysis).
The analyst is responsible for exercising judgement and common sense when using these lists.

Contribution of new lists or list modifications is welcome!

## Structure

The gene lists are stored as a pair of files under the `genes` directory.
The next level directories identify the species (e.g., `human`, `mouse`).
Additional nested sub-directories may be used in the future.

Each list is a pair of files with the same name.

One file has a `.md` suffix and contains free text in markdown format that describes the semantics of the list.

The actual list data is a file with `.csv` suffix ontaining some genes in arbitrary order.
The first line of the CSV file is a header line with the column names.
Each column contains the names of the genes in some namespace.
The supported namespaces are:

* `ensembl` - A gene identfier from [ensembl.org](https://www.ensembl.org/index.html)

TODO: Additional namespaces (e.g. 10X)
