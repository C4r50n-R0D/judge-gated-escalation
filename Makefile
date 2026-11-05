.PHONY: test unit e2e
test: unit e2e
unit:
	python3 tests/test_units.py
e2e:
	bash tests/test_pipeline.sh
