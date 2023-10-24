import os
import argparse
from datetime import datetime
from datetime import datetime
import pandas as pd
from string import punctuation
from lxml import etree as ET
import os
import re
import pandas as pd
import jenkspy
import csv
from modules.camera_cleaning import cameraDocType, cameraRemoveIntest
from modules.senato_cleaning import senatoDocType, senatoRemoveIntest
from string import punctuation

leg_mapping = {
    "regno_1": "regno_01",
    "regno_2": "regno_02",
    "regno_3": "regno_03",
    "regno_4": "regno_04",
    "regno_5": "regno_05",
    "regno_6": "regno_06",
    "regno_7": "regno_07",
    "regno_8": "regno_08",
    "regno_9": "regno_09",
    "l_1": "repubblica_01",
    "cg_1": "repubblica_01",
    "1": "repubblica_01",
    "l_2": "repubblica_02",
    "cg_2": "repubblica_02",
    "2": "repubblica_02",
    "l_3": "repubblica_03",
    "cg_3": "repubblica_03",
    "3": "repubblica_03",
    "l_4": "repubblica_04",
    "cg_4": "repubblica_04",
    "4": "repubblica_04",
    "l_5": "repubblica_05",
    "cg_5": "repubblica_05",
    "5": "repubblica_05",
    "l_6": "repubblica_06",
    "cg_6": "repubblica_06",
    "6": "repubblica_06",
    "l_7": "repubblica_07",
    "cg_7": "repubblica_07",
    "7": "repubblica_07",
    "l_8": "repubblica_08",
    "cg_8": "repubblica_08",
    "8": "repubblica_08",
    "l_9": "repubblica_09",
    "cg_9": "repubblica_09",
    "9": "repubblica_09",
    "l_10": "repubblica_10",
    "cg_10": "repubblica_10",
    "10": "repubblica_10",
    "l_11": "repubblica_11",
    "cg_11": "repubblica_11",
    "11": "repubblica_11",
    "l_12": "repubblica_12",
    "cg_12": "repubblica_12",
    "12": "repubblica_12",
    "l_13": "repubblica_13",
    "cg_13": "repubblica_13",
    "13": "repubblica_13",
    "l_14": "repubblica_14",
    "cg_14": "repubblica_14",
    "14": "repubblica_14",
    "l_15": "repubblica_15",
    "cg_15": "repubblica_15",
    "15": "repubblica_15",
    "l_16": "repubblica_16",
    "cg_16": "repubblica_16",
    "16": "repubblica_16",
    "l_17": "repubblica_17",
    "cg_17": "repubblica_17",
    "17": "repubblica_17",
    "l_18": "repubblica_18",
    "cg_18": "repubblica_18",
    "18": "repubblica_18",
}

reverse_leg_mapping = {v: k for k, v in leg_mapping.items()}


punctuation = punctuation + "“”"


def preprocessDocument(dir, out, strdate, leg, cam):
    """
    processes a single document, removing intestation and padding, merging the page, processing truncated words and outputs the result in a txt file
    :param dir: path to the document
    :param out: path to the output file
    :param strdate: date of the document
    :param leg: legislature of the document
    :param cam: 0 if camera, 1 if senato
    :param gold_folder: path to output the gold standard files
    :param pred_folder: path to output the test files
    """

    # year and date are needed to clean camera documents
    if cam == 0:
        year = int(strdate[:4])
        date = int(strdate)

    i = int(dir.split("-")[-1].split(".")[0])

    print("checking doc " + dir)

    # sort by page number

    filename = dir

    # filter only tsv files (excludes images)

    # get document type (for intestation removal)
    if cam == 0:
        document_type = cameraDocType(date, i, [filename])
    if cam == 1:
        document_type = senatoDocType(leg, i, [filename])

    # last_char = ""
    prev_last_char = ""

    dataframe = pd.read_csv(filename, sep="\t", quoting=csv.QUOTE_NONE, encoding="utf-8")

    # remove intestation and return clean df based on aforementioned document type
    if cam == 0:
        dataframe = cameraRemoveIntest(
            dataframe,
            date,
            year,
            leg,
            document_type,
            i,
        )

    if cam == 1:
        dataframe = senatoRemoveIntest(
            dataframe,
            leg,
            document_type,
            i,
        )

    # there may be an empty page with intestation only

    # remove empty rows from beginning and end of document

    no_padd_df = removePadding(dataframe)

    # remove rows separating columns
    new_cols_df = checkNewCols(no_padd_df, i)

    new_cols_df["page_num"] = i

    os.makedirs(os.path.dirname(out), exist_ok=True)

    text_values = list(
        zip(
            new_cols_df["block_num"],
            new_cols_df["text"],
            new_cols_df["conf"],
            new_cols_df["line_num"],
            new_cols_df["top"],
        )
    )

    with open(out, "w", encoding="utf-8") as output_file:
        # print(text_values)
        # calculate middle separating coordinate

        fillOutputDocument(output_file, text_values, i, prev_last_char)

    prev_last_char = str(new_cols_df["text"].iloc[-1])[-1]

    # prev_top = top

    # prev_last_char = last_char

    #         if not is_truncated:
    #     last_char = str(new_cols_df["text"].iloc[-1])[-1]
    # else:
    #     last_char = "-"

    i += 1

    # read whole document line by line, and taking into account the first four words of a line, check if they are in the people dataset.
    # mind that a name is usually uppercase and followed by a comma or a dot.

    # people can be recognized by the fact that they are written in uppercase and are followed by a comma or a dot.
    # if they are, tag them with their URI. If they are not, check if the first three words are in the dataset. If they are, tag them with their URI.


def fillOutputDocument(output_file, text_values, page_num, prev_last_char):
    """
    fills the output file with the text from each page
    :param output_file: file to write to
    :param text_values: list of tuples containing the text and the confidence of each word
    :param page_num: number of the page
    :param tot_page_num: total number of pages in the document
    :param prev_last_char: last character of the previous page (for handling the case of a truncated word)
    :param people_dataset: dataset containing the people in the legislature
    :param is_gold: whether the output file is a gold standard file
    :param current_president: name of the current president (for handling the case of a new president)
    """

    # if page_num > 1:
    #     if prev_last_char == ".":
    #         output_file.write("\n")
    #     elif prev_last_char != "-":
    #         output_file.write(" ")

    # if page_num == 1:
    #     output_file.write("<?xml version='1.0' encoding='UTF-8'?>\n<document>")
    # prev_top = None
    closing_count = 0
    is_truncated = False
    # word_count = 0
    block = 0
    top = 0

    for word_count, tup in enumerate(text_values):
        conf = int(tup[2])

        if conf == -1:
            closing_count += 1
            continue

        curr_word = str(tup[1])

        # if curr_word.isupper():
        #     keep_track_of_proper_noun += curr_word + " "

        sep = ""

        if closing_count == 2 or block != tup[0] or tup[4] - top > 20:
            # keep_track_of_proper_noun = ""
            sep = "\n"

        else:
            sep = " "

        # if curr_word.islower() and keep_track_of_proper_noun != "":
        #     sep = "\n"
        #     curr_word = keep_track_of_proper_noun + curr_word
        #     keep_track_of_proper_noun = ""

        if is_truncated:
            sep = ""
            is_truncated = False

        if curr_word.endswith("-"):
            curr_word = curr_word[:-1]
            is_truncated = True

        output_file.write(sep + curr_word)

        closing_count = 0
        block = tup[0]
        top = tup[4]

    # if tot_page_num == page_num:
    #     output_file.write("</document>")


def removePadding(df):
    i = 0
    indexes_to_del = []
    # pay attention to not go out of bounds!!!
    while (df["text"].iloc[i] == "" or df["text"].iloc[i] == " " or pd.isna(df["text"].iloc[i])) and (
        i < df.shape[0] - 1
    ):
        indexes_to_del.append(i)
        i += 1
    return df.drop(index=indexes_to_del).reset_index(drop=True)


def checkNewCols(df, page_num):
    window_size = 7

    indexes_to_del = []

    for i in range(len(df["text"]) - window_size + 1):
        # if df["top"] is less than max/2 do not add to indexes_to_del and page_num is 1
        if any(s != "" or s != " " or not pd.isna(s) for s in df["text"].iloc[i : i + window_size]):
            indexes_to_del = list(range(i, i + window_size))

    if len(indexes_to_del) == 0:
        return df

    clean_df = df[~df.index.isin(indexes_to_del)]

    # fix "line continues on other column" case

    return clean_df.reset_index(drop=True)


def cleanGoldTsv(folder, out):
    for i, file in enumerate(os.listdir(folder)):
        if "camera" in file:
            cam = 0
            strdate = file.split("-")[2]
            leg = file.split("-")[1]
        else:
            cam = 1
            poss_leg = file.split("-")[1]
            leg = poss_leg if poss_leg not in reverse_leg_mapping else reverse_leg_mapping[poss_leg]
            strdate = leg
        # if i == 0:
        preprocessDocument(
            os.path.join(folder, file), os.path.join(out, file.replace(".tsv", ".txt")), strdate, leg, cam
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--input_folder",
        type=str,
        default="data/gold_standard_ocr",
        help="path to the folder containing the html files",
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        default="data/pred_set_text",
        help="path to the folder containing the text files",
    )
    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    start_time = datetime.now()
    # createPeopleDatasets(args.people_folder, "tagging_modules/rdf")
    cleanGoldTsv(args.input_folder, args.output_folder)
    # # cleanSenatoHTML(args.html_data_path, args.output_path, args.people_folder)

    # cleanCameraHTML(args.html_data_path, args.output_path, args.people_folder)

    end_time = datetime.now()
    print("Duration: {}".format(end_time - start_time))
