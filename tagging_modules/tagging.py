import rdflib
from rdflib import Graph, ConjunctiveGraph, URIRef
from rdflib.namespace import FOAF, XSD, RDF, DC
import os
from rdflib.plugins.sparql import prepareQuery
from Levenshtein import distance as lev
import time
import pandas as pd
from utils import ordered_leg_names


def initialize(rdf_path):
    """
    Parses together all the useful parliament RDF files in the given path
    :param rdf_path: the path where the RDF files are stored
    :return: None
    """

    global dataset

    dataset = ConjunctiveGraph()

    dataset.parse(os.path.join(rdf_path, "persona.rdf"), format="nt")
    dataset.parse(os.path.join(rdf_path, "mandatoCamera.rdf"), format="nt")
    dataset.parse(os.path.join(rdf_path, "mandatoSenato.rdf"), format="nt")
    dataset.parse(os.path.join(rdf_path, "membroGoverno.rdf"), format="nt")
    dataset.parse(os.path.join(rdf_path, "legislatura.rdf"), format="nt")


def queryRDF(leg):
    """
    Queries the RDF files for the names of the people in the given legislature
    :param leg: the legislature to query
    :return: a dataframe containing the names of the people in the given legislature
    """

    query = prepareQuery(
        f"""
            SELECT DISTINCT ?person ?name ?surname
            WHERE {{
            ?person a foaf:Person .
            ?person foaf:surname ?surname .
            ?person foaf:firstName ?name .
            {{
                ?person <http://dati.camera.it/ocd/rif_membroGoverno> ?mandateGov .
                ?mandateGov ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/{leg}>
            }}
            UNION
            {{
                ?person <http://dati.camera.it/ocd/rif_mandatoCamera> ?mandateCam .
                ?mandateCam ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/{leg}>
            }}
            UNION
            {{
                {{
                    ?person <http://dati.camera.it/ocd/rif_mandatoSenato> ?mandateSen .
                    ?mandateSen ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/{leg}>
                }}
                UNION
                {{
                    ?person <http://dati.camera.it/ocd/rif_mandatoSenato> ?mandateSen .
                    OPTIONAL{{?mandateSen ocd:rif_leg ?leg}}
                    FILTER(!BOUND(?leg))
                    
                    ?mandateSen dc:date ?date .
                    <http://dati.camera.it/ocd/legislatura.rdf/{leg}> dc:date ?leg_date .
                    
                    BIND(xsd:integer(strbefore(?leg_date, "-")) AS ?start_leg_date) .
                    BIND(xsd:integer(strbefore(?date, "-")) AS ?start_date) .
                    BIND(xsd:integer(strafter(?date, "-")) AS ?end_date) .
                    BIND(xsd:integer(strafter(?leg_date, "-")) AS ?end_leg_date) .

                    # filter for ?start_date being inside the legislature OR ?end_date being inside the legislature
                    FILTER(?end_date >= ?start_leg_date && ?start_date <= ?end_leg_date)

                }}
            }}
            }}
        """,
        initNs={"foaf": FOAF, "ocd": URIRef("http://dati.camera.it/ocd/"), "xsd": XSD, "dc": DC},
    )

    # calculate time of query execution
    start_time = time.time()

    qres = dataset.query(query)
    print(len(qres))
    parliament_composition = pd.DataFrame(columns=["name", "surname", "URI"])
    for row in qres:
        parliament_composition = pd.concat(
            [parliament_composition, pd.DataFrame({"name": [row.name], "surname": [row.surname], "URI": [row.person]})]
        )

    # Record the end time
    end_time = time.time()

    # Calculate the execution time in seconds
    execution_time = end_time - start_time

    print("Execution time for legislature " + leg + ": " + str(execution_time) + " seconds")

    return parliament_composition


def createPeopleDatasets(output_path="people", rdf_path="tagging_modules/rdf"):
    """
    Create a dataset for each legislature containing the names of the people in that legislature
    :param output_path: the path where the datasets will be saved
    :param rdf_path: the path where the RDF files are stored
    :return: None
    """
    initialize(rdf_path)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    global ordered_leg_names

    for leg in ordered_leg_names:
        parliament_composition = queryRDF(leg)
        parliament_composition.to_csv(os.path.join(output_path, leg + ".csv"), index=False)
