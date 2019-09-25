default:
	cat Makefile

dist: 
	python3 setup.py sdist
	python3 setup.py bdist
