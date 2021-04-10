.PHONY: build clean

build: clean
	python setup.py sdist bdist_wheel

push:
	twine upload dist/*

install:
	python setup.py install

clean:
	rm -rf dist build