# SPARQL Shape Fragments
Note: this repository serves as an up-to-date version of the project found in the [Shape Fragments repository](https://github.com/Shape-Fragments/SHACL2SPARQL). This package uses an updated version of the [SHACL Logical Syntax Parser](https://github.com/MaximeJakubowski/sls_project).

The main goal of this project is to translate SHACL shapes to corresponding SPARQL queries according to the shape fragments specification.

## Current status
At the moment, this project is broken. It does not run, and is being worked on. An older, working version can be found [here](https://github.com/Shape-Fragments/SHACL2SPARQL).

## Requirements
- python 3.9.7
- python packages listed in `requirements.txt`

You need to add the `slsparser` folder from [sls_project](https://github.com/MaximeJakubowski/sls_project) as a subpackage of `ssf`.

## Installation
Set up a Python virtual environment and install packages from `requirements.txt`.

Let's say the virtual environment is located in `.env`:
1. `$ source .env/bin/activate`
2. `$ python -m pip install -r requirements.txt`

## Usage
The interface to the software is located in `ssf.py`. 
To run the program (while having the virtual environment activated): 

`$ python ssf.py`

This will display the help string. To generate a SPARQL query from a shapes graph:

`$ python ssf.py --frag shapesgraph.ttl`

where `shapesgraph.ttl` is the relevant shapes graph in turtle format.

To generate SPARQL queries which ignore tests (as generated for the experiments in the paper):

`$ python ssf.py --frag -i shapesgraph.ttl`
