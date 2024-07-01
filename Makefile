SPECIES = human mouse

human_LISTS = transcription_factors
mouse_LISTS =

all: namespaces lists

clean:
	rm -rf `find . -name 'log.txt'`

clean_extra:
	rm -rf genes/*/namespaces/sources/*.Extra.tsv
	for IGNORED in genes/*/namespaces/sources/*.Ignored.tsv ; \
	do \
	    MISSING=`echo $$IGNORED | sed 's/Ignored/Missing/'` ; \
	    if [ -f $$IGNORED ] ; then \
	        cat $$IGNORED >> $$MISSING ; \
	        rm $$IGNORED ; \
	    fi ; \
	done


define SPECIES_RULES

namespaces: $(1)_namespaces

$(1)_namespaces: genes/$(1)/namespaces/log.txt

genes/$(1)/namespaces/log.txt: scripts/compute_namespaces.py $(filter-out README.md,$(wildcard genes/$(1)/namespaces/sources/*))
	set -o pipefail && scripts/compute_namespaces.py $(1) 2>&1 | tee genes/$(1)/namespaces/log.txt

lists: $(1)_lists

$(1)_lists: genes/$(1)/lists/log.txt

genes/$(1)/lists/log.txt: scripts/complete_namespaces.py
	set -o pipefail && scripts/complete_namespaces.py $(1) 2>&1 | tee genes/$(1)/lists/log.txt

$(foreach list,$($(1)_LISTS),$(eval $(call SPECIES_LIST_RULES,$(1),$(list))))
endef


define SPECIES_LIST_RULES

genes/$(1)/lists/log.txt: genes/$(1)/lists/$(2)/log.txt

genes/$(1)/lists/$(2)/log.txt: scripts/compute_list.py genes/$(1)/namespaces/log.txt $(filter-out README.md,$(wildcard genes/$(1)/lists/$(2)/sources/*))
	set -o pipefail && scripts/compute_list.py $(1) $(2) 2>&1 | tee genes/$(1)/lists/$(2)/log.txt
endef


$(foreach species,$(SPECIES),$(eval $(call SPECIES_RULES,$(species))))
