
mkdocs:
	PYTHONPATH=. mkdocs serve  -f ./docs/mkdocs.yml 

build:
	poetry build 
