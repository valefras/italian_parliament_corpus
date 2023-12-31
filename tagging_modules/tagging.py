import rdflib
from rdflib import Graph, ConjunctiveGraph, URIRef
from rdflib.namespace import FOAF, XSD, RDF, DC
import os
from rdflib.plugins.sparql import prepareQuery
from Levenshtein import distance as lev
import time
import pandas as pd

# from utils import ordered_leg_names

ordered_leg_names = [
    "regno_01",
    "regno_02",
    "regno_03",
    "regno_04",
    "regno_05",
    "regno_06",
    "regno_07",
    "regno_08",
    "regno_09",
    "regno_10",
    "regno_11",
    "regno_12",
    "regno_13",
    "regno_14",
    "regno_15",
    "regno_16",
    "regno_17",
    "regno_18",
    "regno_19",
    "regno_20",
    "regno_21",
    "regno_22",
    "regno_23",
    "regno_24",
    "regno_25",
    "regno_26",
    "regno_27",
    "regno_28",
    "regno_29",
    "regno_30",
    "consulta_nazionale",
    "costituente",
    "repubblica_01",
    "repubblica_02",
    "repubblica_03",
    "repubblica_04",
    "repubblica_05",
    "repubblica_06",
    "repubblica_07",
    "repubblica_08",
    "repubblica_09",
    "repubblica_10",
    "repubblica_11",
    "repubblica_12",
    "repubblica_13",
    "repubblica_14",
    "repubblica_15",
    "repubblica_16",
    "repubblica_17",
    "repubblica_18",
]


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
            SELECT DISTINCT ?person ?name ?surname ?job
            # job is 0 if the person is a member of the government, 1 if the person is a deputy, 2 if the person is a senator
            WHERE {{
            ?person a foaf:Person .
            ?person foaf:surname ?surname .
            ?person foaf:firstName ?name .
            {{
                ?person <http://dati.camera.it/ocd/rif_membroGoverno> ?mandateGov .
                ?mandateGov ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/{leg}>

                BIND(0 AS ?job)
            }}
            UNION
            {{
                ?person <http://dati.camera.it/ocd/rif_mandatoCamera> ?mandateCam .
                ?mandateCam ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/{leg}>

                BIND(1 AS ?job)
            }}
            UNION
            {{
                {{
                    ?person <http://dati.camera.it/ocd/rif_mandatoSenato> ?mandateSen .
                    ?mandateSen ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/{leg}>

                    BIND(2 AS ?job)
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
                    FILTER(?end_date >= ?start_leg_date && ?start_date < ?end_leg_date)

                    BIND(2 AS ?job)
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
    parliament_composition = pd.DataFrame(columns=["name", "surname", "job", "URI"])
    for row in qres:
        parliament_composition = pd.concat(
            [
                parliament_composition,
                pd.DataFrame({"name": [row.name], "surname": [row.surname], "job": [row.job], "URI": [row.person]}),
            ]
        )

    # Record the end time
    end_time = time.time()

    # Calculate the execution time in seconds
    execution_time = end_time - start_time

    print("Execution time for legislature " + leg + ": " + str(execution_time) + " seconds")

    return parliament_composition


def createPeopleDatasets(output_path="../people", rdf_path="tagging_modules/rdf"):
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


createPeopleDatasets()
