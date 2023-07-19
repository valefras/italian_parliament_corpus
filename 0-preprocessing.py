import os
from cleaning_utils.cleaning_functions import preprocessDocument
import argparse


def cleanDocs(data_path, output_path, test_set_folder):
    """
    iterates over all documents in the data folder, cleans them and outputs them in the output folder
    :param data_path: path to the data folder
    :param output_path: path to the output folder
    """
    os.makedirs(test_set_folder, exist_ok=True)

    for cam in os.listdir(data_path):
        for leg in sorted(os.listdir(os.path.join(data_path, cam))):
            if cam == "senato" and (leg[:2] == "cg" or leg[:1] == "l" or leg[:5] == "regno"):
                for doc in os.listdir(os.path.join(data_path, cam, leg)):
                    if doc.endswith("out"):
                        output_path_file = output_path + "/" + cam + "/" + leg + "/" + doc
                        preprocessDocument(
                            os.path.join(data_path, cam, leg, doc),
                            output_path_file,
                            leg,
                            leg,
                            1,
                            test_set_folder,
                        )
            else:
                for day in sorted(os.listdir(os.path.join(data_path, cam, leg))):
                    for doc in os.listdir(os.path.join(data_path, cam, leg, day)):
                        if doc.endswith("out"):
                            output_path_file = output_path + "/" + cam + "/" + leg + "/" + day + "/" + doc
                            cam_num = 0 if cam == "camera" else 1
                            preprocessDocument(
                                os.path.join(data_path, cam, leg, day, doc),
                                output_path_file,
                                day,
                                leg,
                                cam_num,
                                test_set_folder,
                            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--data_path", type=str, default="data/", help="Path to the data to process.")
    parser.add_argument(
        "--output_path",
        type=str,
        default="output/",
        help="Where to output clean documents.",
    )
    parser.add_argument(
        "--test_set_folder",
        type=str,
        default="test_set/",
        help="Folder where to output the test set.",
    )

    args = parser.parse_args()

    cleanDocs(args.data_path, args.output_path, args.test_set_folder)


################### IGNORE #######################


# import re
# import requests

# # open the text file
# with open('example.txt', 'r') as file:
#     text = file.read()

# # find all consecutive words with all caps letters
# matches = re.findall(r'\b(?![MDCLXVI]+\b)[A-Z]{3,}(?:\s+[A-Z]{3,})*\b', text)

# # create a Wikidata query to find the QIDs for each match
# for match in matches:
#     name = ''
#     surname = ''
#     query = """
#     SELECT * WHERE {
#         ?politician wdt:P31 wd:Q5 ;
#                     wdt:P27 wd:Q38 ;
#                     rdfs:label ?politicianLabel .
#         FILTER(LANG(?politicianLabel) = "it") .
#         FILTER(CONTAINS(LCASE(?politicianLabel), \"""" + name + """\") && CONTAINS(LCASE(?politicianLabel), \"""" + surname + """\"))
# }
#     """
#     response = requests.get('https://query.wikidata.org/sparql', params={'query': query})
#     if response.ok:
#         data = response.json()
#         for result in data['results']['bindings']:
#             qid = result['item']['value'].split('/')[-1]
#             label = result['itemLabel']['value']
#             print(f"{match}: {qid} ({label})")
