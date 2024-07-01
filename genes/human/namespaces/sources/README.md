This directory holds the sources of the genes namespaces:

* `sources.yaml` lists the source files and how to process them.
* `<name>.csv` and/or `<name>.tsv` are comma-seperated or tab-seperated data source files. The `<name>` typically
  based on the name(s) of the relevant namespaces it contains data for.
* `<name>.Extra.tsv` contains names of genes that did not appear in any of the data sources, but that we managed to find
  data for using web API calls for the specific gene. We only know about such genes because at some point we saw them
  in the sources of some list, or in some data set.
* `<name>.Ignored.tsv` contains the names of genes that we saw somewhere (list sources, data sets) but do not appear
  in the data files and we couldn't find any data for them using web APIs. These names will *not* appear in the computed
  lists.
* `<name>.Missing.tsv` contains the names of genes that we saw somewhere (list sources, data sets) but did not (yet)
  look up using the web APIs. This file is temporary; running `scripts/complete_namespaces.py` will invoke the web APIs,
  add the names to the `Extra` or `Ignored` file, and remove the `Missing` file.
