all: haversine-a3.png rule-a3.png
INKSCAPE ?= $(HOME)/bin/inkscape-1.4
DPI ?= 600

%.png: %.svg
	$(INKSCAPE) \
		--export-dpi $(DPI) \
		-o $@ \
		$<

haversine-a3.svg: *.py
	./make-haversine.py
rule-a3.svg: *.py
	./make-rule.py
