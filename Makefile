all: haversine-a3.png rule-a3.png
INKSCAPE ?= $(HOME)/bin/inkscape-1.4

%.png: %.svg
	$(INKSCAPE) \
		--export-dpi 600 \
		-o $@ \
		$<

haversine-a3.svg: *.py
	./make-haversine.py
rule-a3.svg: *.py
	./make-rule.py
