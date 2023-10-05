import os
from cleaning_utils.formatting_func import preprocessDocument
import argparse
from datetime import datetime
import json
from datetime import datetime
import locale
import pandas as pd
from bs4 import BeautifulSoup
from tagging_modules.tagging import createPeopleDatasets
import re
from utils import leg_mapping_full


def cleanCameraPDF(metadata_path, data_path, output_path, gold_folder, test_folder):

    metadata_dict = json.load(open(metadata_path, "r"))

    for leg in os.listdir(os.path.join(data_path, "camera")):
        if os.path.isdir(os.path.join(data_path, "camera", leg)):
            print("1")
            for day in os.listdir(os.path.join(data_path, "camera", leg)):
                if os.path.isdir(os.path.join(data_path, "camera", leg, day)):
                    print("2")
                    for doc in os.listdir(os.path.join(data_path, "camera", leg, day)):
                        if doc.endswith(".pdf"):
                            print("3")
                            # path_for_metadata = os.path.join("out", leg, day, doc)
                            path_for_metadata = "out/" + leg + "/" + day + "/" + doc
                            print(path_for_metadata)
                            if path_for_metadata in metadata_dict[leg]:
                                print("4")
                                if metadata_dict[leg][path_for_metadata]["type"] == "Seduta":
                                    input_path = os.path.join(data_path, "camera", leg, day, doc + ".out")
                                    output_file = os.path.join(output_path, "camera", leg, day + ".xml")

                                    if os.path.exists(input_path):
                                        preprocessDocument(
                                            input_path, output_file, day, leg, 0, gold_folder, test_folder
                                        )
    # ################################## break for testing
    # break
    # #############################################
    # if doc.endswith(".out"):
    #     ################################## break for testing
    #     if leg != "repubblica_13":
    #         break
    #     #############################################
    #     input_path = os.path.join(data_path, leg, day, doc)
    #     clean_leg = leg_mapping_full[leg] if leg in leg_mapping_full else leg
    #     output_file = os.path.join(output_path, "camera", clean_leg, day + ".xml")
    #     preprocessDocument(
    #         input_path,
    #         output_file,
    #         day,
    #         leg,
    #         0,
    #     )
    ################################## break for testing
    # break
    #############################################

    # for leg, leg_dict in metadata_dict.items():
    #     for doc, doc_info in leg_dict.items():
    #         if doc_info["type"] == "Seduta":
    #             input_path = doc_info["filename"].split("/", 1)[1]
    #             clean_path = os.path.join(data_path, "camera", input_path + ".out")
    #             clean_leg = leg_mapping_full[leg] if leg in leg_mapping_full else leg
    #             output_file = os.path.join(output_path, "camera", clean_leg, doc_info["date"] + ".xml")
    #             preprocessDocument(
    #                 clean_path,
    #                 output_file,
    #                 doc_info["date"],
    #                 leg,
    #                 0,
    #             )
    #     ################################## break for testing
    #     break
    #     #############################################à


def cleanSenatoPDFMon(metadata_path, data_path, output_path, gold_folder, test_folder):
    # this time metadata is a csv
    metadata_csv = pd.read_csv(metadata_path, sep=";", encoding="utf-8")

    metadata_csv.rename(columns={"Unnamed: 1": "Filename"}, inplace=True)

    docs_data = list(zip(metadata_csv["Filename"], metadata_csv["Legislatura"], metadata_csv["Data"]))

    for doc_data in docs_data:
        date_raw = doc_data[2]
        date = date_raw[:6] + "19" + date_raw[6:] if len(date_raw.split("/")[2]) == 2 else date_raw
        date_parsed = datetime.strptime(date, "%d/%m/%Y").strftime("%Y%m%d")

        leg_raw = str(doc_data[1])

        # ################################## break for testing
        # if leg_raw != "1":
        #     break
        # #############################################à
        leg_parsed = "regno_0" + leg_raw if len(leg_raw) == 1 else "regno_" + leg_raw

        filename = doc_data[0].split("/")[-1] + ".out"

        input_path = os.path.join(data_path, "senato", "regno_" + leg_raw, filename)

        if os.path.exists(input_path):
            clean_path = input_path
            output_file = os.path.join(output_path, "senato", leg_parsed, date_parsed + ".xml")
            preprocessDocument(clean_path, output_file, date_parsed, leg_parsed, 1, gold_folder, test_folder)


def cleanSenatoPDFRep(metadata_path, data_path, output_path, gold_folder, test_folder):
    metadata_dict = json.load(open(metadata_path, "r"))

    for leg, leg_dict in metadata_dict.items():
        for doc, doc_info in leg_dict.items():
            input_path = doc_info["filename"].split("-", 1)[1]
            clean_path = os.path.join(data_path, input_path + ".out")
            if not os.path.exists(clean_path):
                continue
            clean_filename = convert_date_format(doc_info["date"].split(" ", 1)[1])
            clean_leg = leg_mapping_full[leg] if leg in leg_mapping_full else leg
            print(clean_leg)
            output_file = os.path.join(output_path, "senato", clean_leg, clean_filename + ".xml")
            preprocessDocument(clean_path, output_file, clean_filename, clean_leg, 1, gold_folder, test_folder)
        # ################################## break for testing
        # break
        # #############################################


def cleanCameraHTML(data_path, output_path):
    for leg in os.listdir(os.path.join(data_path, "camera")):
        if os.path.isdir(os.path.join(data_path, "camera", leg)):
            for day in os.listdir(os.path.join(data_path, "camera", leg)):
                if os.path.isdir(os.path.join(data_path, "camera", leg, day)):
                    if leg == "repubblica_13" or leg == "repubblica_14":
                        docs = sorted(
                            [doc for doc in os.listdir(os.path.join(data_path, "camera", leg, day)) if "_s" in doc]
                        )
                        output_file = os.path.join(output_path, "camera", leg, day + ".xml")
                        os.makedirs(os.path.dirname(output_file), exist_ok=True)
                        for doc in docs:
                            # ################################## break for testing
                            # if leg != "repubblica_13":
                            #     break
                            # #############################################
                            # with beautifulsoup, extract texts from htms
                            print("checking html camera " + doc)
                            with open(os.path.join(data_path, "camera", leg, day, doc), "r", encoding="latin-1") as f:
                                soup = BeautifulSoup(f, "html.parser")
                                text = soup.get_text(strip=True, separator="\n")
                                # remove text "Pag. " + number from text
                                text = re.sub(r"Pag. \d+", "", text)
                                clean_text = re.sub(r"\s{2,}", "\n", text)
                                # write texts in output folder
                                with open(output_file, "a", encoding="utf-8") as f:
                                    f.write(clean_text)
                    else:
                        for doc in os.listdir(os.path.join(data_path, "camera", leg, day)):
                            # ################################## break for testing
                            # if leg != "repubblica_15":
                            #     break
                            # #############################################
                            if doc.endswith(".xml"):
                                output_file = os.path.join(output_path, "camera", leg, day + ".xml")
                                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                                # with beautifulsoup, extract texts from htms
                                print("checking html camera " + doc)

                                with open(os.path.join(data_path, "camera", leg, day, doc), "r", encoding="utf-8") as f:
                                    soup = BeautifulSoup(f, "lxml-xml")
                                    text = soup.get_text()
                                    # remove text "Pag. " + number from text
                                    text = re.sub(r"Pag. \d+", "", text)
                                    clean_text = re.sub(r"\s{2,}", "\n", text)

                                    # write texts in output folder
                                    with open(output_file, "a", encoding="utf-8") as f:
                                        f.write(clean_text)


def cleanSenatoHTML(data_path, output_path):
    for leg in os.listdir(os.path.join(data_path, "senato")):
        if os.path.isdir(os.path.join(data_path, "senato", leg)) and leg in ["13", "14", "15", "16", "17", "18"]:
            for year in os.listdir(os.path.join(data_path, "senato", leg)):
                if os.path.isdir(os.path.join(data_path, "senato", leg, year)):
                    for doc in os.listdir(os.path.join(data_path, "senato", leg, year)):
                        if doc.endswith(".htm"):
                            # output_file = os.path.join(output_path, "senato", leg, day + ".xml")
                            # with beautifulsoup, extract texts from htms
                            print("checking html senato " + doc)
                            with open(os.path.join(data_path, "senato", leg, year, doc), "r", encoding="utf-8") as f:
                                soup = BeautifulSoup(f, "html.parser")
                                text = soup.get_text()
                                clean_text = re.sub(r"\s{2,}", "\n", text)
                                pattern = r"(\d{1,2}(?:°)?) (GENNAIO|FEBBRAIO|MARZO|APRILE|MAGGIO|GIUGNO|LUGLIO|AGOSTO|SETTEMBRE|OTTOBRE|NOVEMBRE|DICEMBRE) \d{4}"
                                try:
                                    date_raw = re.search(pattern, clean_text).group()
                                    date_raw = date_raw.replace("°", "")
                                    clean_date = convert_date_format(date_raw)
                                except:
                                    clean_date = "date_not_found_" + year + "_" + doc

                                clean_leg = leg_mapping_full[leg] if leg in leg_mapping_full else leg

                                output_file = os.path.join(output_path, "senato", clean_leg, clean_date + ".xml")
                                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                                # remove text "Pag. " + number from text
                                # text = re.sub(r"Pag. \d+", "", text)
                                # write texts in output folder
                                with open(output_file, "a", encoding="utf-8") as f:
                                    f.write(clean_text)
            # ################################## break for testing
            # break
            # #############################################


def convert_date_format(input_date):
    # Define the input and output date formats
    input_format = "%d %B %Y"
    output_format = "%Y%m%d"
    locale.setlocale(locale.LC_TIME, "it_IT.utf8")

    try:
        # Parse the input date string to a datetime object
        date_obj = datetime.strptime(input_date, input_format)
        # Convert the datetime object back to a formatted string
        output_date = date_obj.strftime(output_format)
        return str(output_date)
    except ValueError:
        # If there's an error parsing the date, return None or handle the error as needed.
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--pdf_data_path", type=str, default="data/", help="Path to the data to process.")
    parser.add_argument("--html_data_path", type=str, default="data/", help="Path to the data to process.")
    parser.add_argument(
        "--output_path",
        type=str,
        default="output/",
        help="Where to output clean documents.",
    )
    parser.add_argument(
        "--camera_metadata_path",
        type=str,
        help="Path to the metadata file for camera documents.",
    )
    parser.add_argument(
        "--senato_rep_metadata_path",
        type=str,
        help="Path to the metadata file for republican senato documents.",
    )
    parser.add_argument(
        "--senato_mon_metadata_path",
        type=str,
        help="Path to the metadata file for monarchical senato documents.",
    )
    parser.add_argument(
        "--gold_folder",
        type=str,
        default="../evaluation/gold_standard",
        help="Path to the gold folder.",
    )
    parser.add_argument(
        "--test_set_folder",
        type=str,
        default="../evaluation/test_set",
        help="Folder where to output the test set.",
    )

    args = parser.parse_args()

    os.makedirs(args.output_path, exist_ok=True)

    start_time = datetime.now()

    createPeopleDatasets("people", "tagging_modules/rdf")

    # cleanCameraHTML(args.html_data_path, args.output_path)
    # cleanSenatoHTML(args.html_data_path, args.output_path)
    cleanSenatoPDFRep(
        args.senato_rep_metadata_path, args.pdf_data_path, args.output_path, args.gold_folder, args.test_set_folder
    )

    cleanSenatoPDFMon(
        args.senato_mon_metadata_path, args.pdf_data_path, args.output_path, args.gold_folder, args.test_set_folder
    )

    cleanCameraPDF(
        args.camera_metadata_path, args.pdf_data_path, args.output_path, args.gold_folder, args.test_set_folder
    )

    end_time = datetime.now()
    print("Duration: {}".format(end_time - start_time))
