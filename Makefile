all: namespaces

namespaces: genes/human/namespaces/names genes/mouse/namespaces/names

genes/human/namespaces/names: scripts/compute_namespaces.py genes/human/namespaces/sources/*
	scripts/compute_namespaces.py genes/human

genes/mouse/namespaces/names: scripts/compute_namespaces.py genes/mouse/namespaces/sources/*
	scripts/compute_namespaces.py genes/mouse
