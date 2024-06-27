# Gmara <img src="Gmara.jpg" align="right" height="280" alt="" />
Genes Manifests Archive for RNA Analysis

## Motivation

This repository holds lists of genes for use in scRNA-seq analysis.
They are stored in machine-readable format so they can be used by software, directly from this repository, optionally with commit tags to ensure reproducability.

The intent is that these lists be used as *initial* lists for analysis (e.g., provide initial list of lateral genes for metacells analysis).
The analyst is responsible for exercising judgement and common sense when using these lists.

Contribution of new lists or list modifications is welcome!

## Structure

The data is stored in the following tree:

* All data is under the `genes` directory.
    * A sub-directory exists for each organism (e.g., `human`, `mouse`).
        * A `namespaces` sub-directory contains a description of the gene namespaces used.
            * A `sources` sub-directory contains the source files we collected the gene namespaces from.
            * A `names` sub-directory contains the actual gene names.
        * A `lists` sub-directory` contains the actual gene lists.

Additional sub-directories may be added in the future.

## API and Versioning

There's no API provided here. The idea is that you should fetch the data file(s) you need directly through the github
URLs using `wget`, `curl` or any other method for fetching HTTP data. That said, it is possible to provide a thing API
for fetching specific data using these URLs.

Since this is a github repository, you can always refer to a specific commit of this repository in the URLs to get the
same data. This is useful anywhere reproduciblity is important (e.g. vignettes and published results).

## Lists

Each list is a sub-directory under the `lists` sub-directory, holding the following files:

* `README.md` contains a free text in markdown format that describes the semantics of the list.

* For each namespace, _namespace_`.tsv` contains a single column called `name` holding the named genes in
  alphabetical order. This includes both the canonical and the alternative gene names, to make it easier to test whether
  a gene is included in the list.

Lists are curated by hand, typically using ``scripts/map_list.py`` to map names between namespaces.

## Namepaces

"The naming of cats is a difficult matter" - T. S. Eliot

There are [too many ways](https://xkcd.com/927/) to uniquely identify a gene. We support the following:
defines its own gene naming scheme:
[Ensembl](https://www.ensembl.org/info/genome/genebuild/gene_names.html),
[RefSeq](https://www.ncbi.nlm.nih.gov/refseq/),
[HGNC](https://www.genenames.org/),
[MGI](https://www.informatics.jax.org/),
[UCSC](https://genome.ucsc.edu/).

To maintain lists of genes we must deal with these gene namespaces. We do this by scraping data from many places and
maintaining a mapping between the different gene name spaces. Note that in some namespaces, what we refer to as a "name"
here is called the "symbol" or "marker".

We use the following data model for handling gene namespaces:

* We use a separate namespace for each organism. If a standard genes namespace applies to multiple organisms, we
  replicate it.

* In each namespace, there is a set of "canonical" gene names.

* It is assumed that once a name was added to a namespace, it is never removed - only renamed to some new name(s).
  It may be that multiple old names are combined into a new one or that an old name is split into several new ones.

* Each canonical name has an associated set of "alternative" (alias and/or older) names to reflect usage and/or
  changes made to the namespace over time.

For each pair of namespaces, the mapping between them associates a set of names in one namespace with a (possibly empty)
set of names with the other. Ideally this is a one-to-one mapping, but similarly to alternatives within a namespace,
sometimes several gene name(s) in one namespace are mapped to a single name in another, or even a many-to-many mapping.

Therefore, mapping a gene name between namespace (or even merely converting each gene name to its canonical name)
requires some strategy to deal with cases where the name is split into several names, or is merged with other names.

To compute all the above, we begin with an ordered set of "source of truth" files. These are TSV or CSV files under the
`sources` sub-directory which have at least two column containing names, to establish the link between names (within the
same namespace or across namespaces). In addition we have a single `sources.yaml` file which contains a sequence of
mappings with the following keys, as well as a comment describing the source:

* ``data_file`` holds the name of the CSV or TSV source data file.
* ``has_header`` is a boolean specifying whether the data file has a header line (default: `true`).
* `columns` holds a mapping whose key is the column name (or 0-based index), and whose value is a mapping with the
  following keys:
    * `namespace` is the name of the namespace of the name(s) in the column.
    * ``is_alternative`` is a boolean (default: `false`) specifying whether the name(s) in the column are alternatives
      to the canonical name.

Each source file should specify at least two columns to use. If multiple columns are associated with the same namespace,
all but one must contain alternative names. The value in each column may be a single name or a list of names. The
separator can be either `,`, `;`, `|`, ` ` (space) or `\t` (tab). It must be different from the separator of the file (`,` or
`\t` (tab), indicated by the file's suffix).

Links between names are collected from all source files. The computed canonical names are these that were not used as
alternatives anywhere in the source files. This computation is done by ``scripts/compute_namespaces.py``.

To represent the result, in the `names` sub-directory we keep the following files:

* _namespace_`.tsv` contains two columns called `name` and ``is_canonical``, and holds all the unique gene names of the
  namespace in alphabetical order.

* For each pair of namespaces, _namespace1_`.`_namespace2_`.tsv` contains two columns called `from` and `to`, and holds
  the mapping from _namespace1_ names to _namespace2_ names, in alphabetical order. The `to` names given for
  _namespace2_ are always canonical. Note that the same _namespace1_ name may appear multiple times to allow for
  one-to-many mappings.
