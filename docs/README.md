# Steps for adding new documents to ReadTheDocs:

## Add a new document
- clone the repo from 
	- https://gitlab.com/ska-telescope/ska-mid-cbf-fhs-vcc

- create new folder in ska-mid-cbf-fhs-vcc/docs
    - eg: ska-mid-cbf-fhs-vcc/docs/api

- at the bottom of the ska-mid-cbf-fhs-vcc/docs/index.rst add a new section for api docs eg:

    ```
	.. toctree::
  	  :maxdepth: 2
          :caption: <api section title>
          :hidden:

  	  api/<api_doc_1.md>
  	  api/<api_doc_2.md>
    ```

- setup new poetry shell for the project ska-mid-cbf-fhs-vcc
    ```
	poetry shell
    ```

- in the poetry shell run the following:
    ```
	poetry lock
	poetry install
    ```

## Building ReadTheDocs Locally
- to generate the documents navigate into the ska-mid-cbf-fhs-vcc/docs and run:
    ```
	make html
    ```

- The generated docs can be found in: 
	- ska-mid-cbf-fhs-vcc/docs/build

- open Index.html in your browser to view the documentation
