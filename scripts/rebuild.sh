
set -x -e

rm -rf genes/*/names/sources/*_Missing_from_Lists.txt

scripts/compute_namespaces.py genes/human
scripts/compute_namespaces.py genes/mouse

scripts/compute_lists.py genes/human/lists/transcription_factors

scripts/complete_namespaces.py genes/human

rm -rf genes/*/names/sources/*_Missing_from_Lists.txt

scripts/compute_namespaces.py genes/human

scripts/compute_lists.py genes/human/lists/transcription_factors
