all: lists

namespaces: \
            genes/human/namespaces/names \
            genes/mouse/namespaces/names

genes/human/namespaces/names: \
            scripts/compute_namespaces.py \
            genes/human/namespaces/sources/*
	scripts/compute_namespaces.py genes/human

genes/mouse/namespaces/names: \
            scripts/compute_namespaces.py \
            genes/mouse/namespaces/sources/*
	scripts/compute_namespaces.py genes/mouse

lists: \
            genes/human/lists/transcription_factors/names/Ensembl.tsv

genes/human/lists/transcription_factors/names/Ensembl.tsv: \
            scripts/compute_lists.py \
            genes/human/namespaces/names \
            genes/human/lists/transcription_factors/sources/*
	scripts/compute_lists.py genes/human/lists/transcription_factors
