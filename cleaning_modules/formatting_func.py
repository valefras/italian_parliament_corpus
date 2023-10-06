import os
import pandas as pd
import csv
from .senato_cleaning import senatoDocType, senatoRemoveIntest
from .camera_cleaning import cameraDocType, cameraRemoveIntest
from Levenshtein import distance as lev
import numpy as np
from collections import Counter
from fuzzywuzzy import fuzz, process, utils


def preprocessDocument(dir, out, strdate, leg, cam, gold_folder, test_folder):
    """
    processes a single document, removing intestation and padding, merging the page, processing truncated words and outputs the result in a txt file
    :param dir: path to the document
    :param out: path to the output file
    :param strdate: date of the document
    :param leg: legislature of the document
    :param cam: 0 if camera, 1 if senato
    :param gold_folder: path to output the gold standard files
    :param test_folder: path to output the test files
    """

    # year and date are needed to clean camera documents
    if cam == 0:
        year = int(strdate[:4])
        date = int(strdate)

    i = 1

    print("checking doc " + dir)

    # sort by page number

    page_list = sorted(os.listdir(dir))

    # filter only tsv files (excludes images)
    page_list = [os.path.join(dir, x) for x in page_list if x.endswith("tsv")]

    # get document type (for intestation removal)
    if cam == 0:
        document_type = cameraDocType(date, i, page_list)
    if cam == 1:
        document_type = senatoDocType(leg, i, page_list)

    people_dataset = pd.read_csv("people/" + leg + ".csv", encoding="utf-8")

    # once document type is known, remove intestation, padding, parse columns for each page

    # last_char = ""
    prev_last_char = ""
    is_gold = False
    tot_page_num = len(page_list)

    for filename in page_list:
        clean_doc_name = (
            filename.split(os.sep)[-2].split(".")[0]
            if cam == 0 or cam == 1 and leg[:5] == "regno"
            else filename.split("/")[-1].split(".")[0]
        )

        if cam == 1 and leg[:5] == "regno":
            gold_format = (
                "-".join(
                    [
                        "senato",
                        leg,
                        clean_doc_name,
                        str(i),
                    ]
                )
                + ".xml"
            )
        elif cam == 0:
            gold_format = (
                "-".join(
                    [
                        "camera" if cam == 0 else "senato",
                        leg,
                        strdate,
                        clean_doc_name,
                        str(i),
                    ]
                )
                + ".xml"
            )
        elif cam == 1:
            gold_format = (
                "-".join(
                    [
                        "senato",
                        leg,
                        strdate[:4],
                        clean_doc_name,
                        str(i),
                    ]
                )
                + ".xml"
            )
        print(gold_format, filename)

        if gold_format in os.listdir(gold_folder):
            is_gold = True
            print("gold standard found for " + gold_format)

        # if dataframe filename is empty, skip
        if os.stat(filename).st_size == 0:
            i += 1
            continue

        dataframe = pd.read_csv(filename, sep="\t", quoting=csv.QUOTE_NONE, encoding="utf-8")

        if dataframe.shape[0] < 2:
            i += 1
            continue

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

        if dataframe.shape[0] < 2:
            i += 1
            continue

        # remove empty rows from beginning and end of document
        no_padd_df = removePadding(dataframe)

        # remove rows separating columns
        new_cols_df = checkNewCols(no_padd_df)

        new_cols_df["page_num"] = i

        if i == 1:
            os.makedirs(os.path.dirname(out), exist_ok=True)

        text_values = list(
            zip(
                new_cols_df["block_num"],
                new_cols_df["par_num"],
                new_cols_df["page_num"],
                new_cols_df["text"],
                new_cols_df["conf"],
                new_cols_df["top"],
                new_cols_df["height"],
                new_cols_df["word_num"],
            )
        )

        if len(text_values) == 0:
            i += 1
            continue

        with open(out, "a", encoding="utf-8") as output_file:
            # print(text_values)
            fillOutputDocument(output_file, text_values, i, tot_page_num, prev_last_char, people_dataset, is_gold)

        if is_gold:
            if not os.path.exists(test_folder):
                os.makedirs(test_folder)
            with open(test_folder + "/" + gold_format, "w", encoding="utf-8") as gold:
                fillOutputDocument(gold, text_values, i, tot_page_num, prev_last_char, people_dataset, is_gold)
            performTagging(test_folder + "/" + gold_format, leg, cam, people_dataset)

        is_gold = False

        prev_last_char = str(new_cols_df["text"].iloc[-1])[-1]

        # prev_top = top

        # prev_last_char = last_char

        #         if not is_truncated:
        #     last_char = str(new_cols_df["text"].iloc[-1])[-1]
        # else:
        #     last_char = "-"

        i += 1

    performTagging(out, leg, cam, people_dataset)
    # read whole document line by line, and taking into account the first four words of a line, check if they are in the people dataset.
    # mind that a name is usually uppercase and followed by a comma or a dot.


def performTagging(out, leg, cam, people_dataset):
    with open(out, "r", encoding="utf-8") as input_file:
        lines = input_file.readlines()

    is_presidency_open = False
    is_speech_open = False

    new_lines = ["<?xml version='1.0' encoding='UTF-8'?>\n", "<document>\n"]

    for line in lines:
        line = line.replace("<", "").replace(">", "").replace("&", "e")

        new_line = ""
        name = []

        if line.split(" ")[0] == "PRESIDENZA" or line.split(" ")[0] == "Presidenza":
            if utils.full_process(line):
                # wont execute and not produce a warning
                president_best_match = process.extractOne(
                    line.lower(),
                    list(people_dataset["surname"].str.lower()),
                    scorer=fuzz.partial_ratio,
                    score_cutoff=70,
                )
                if president_best_match:
                    president_uri = people_dataset.loc[people_dataset["surname"] == president_best_match[0].upper()][
                        "URI"
                    ].iloc[0]
                    if is_presidency_open:
                        new_line += '</presidency><presidency president="' + president_uri + '">' + line
                    elif is_speech_open:
                        new_line += '</speech><presidency president="' + president_uri + '">' + line
                    else:
                        new_line += '<presidency president="' + president_uri + '">' + line
                    is_presidency_open = True
                new_lines.append(new_line)
                continue
        ### if first letter of line is uppercase, proceed with tagging, else just apppend the line
        elif line[0].isupper():
            ### case 1: names to tag are all lowercase
            if (
                cam == 0 and leg in ["regno_15", "regno_16", "regno_17", "regno_18", "regno_19", "regno_20", "regno_21"]
            ) or (cam == 1 and leg in ["regno_08", "regno_09", "regno_10"]):
                # all names to locate are lowercase, only in these legislatures
                # only way to identify names is the dot or comma at the end of the name

                words = line.split()
                for i, word in enumerate(words):
                    if i >= 4:
                        break
                    if word.endswith(".") or word.endswith(","):
                        name.append(word)
                        break
                    else:
                        name.append(word)

                name = " ".join(name)

                if "Presidente" in name and name.endswith(".") and is_presidency_open:
                    if is_speech_open:
                        new_line += '</speech><speech speaker="' + president_uri + '">' + line
                    else:
                        new_line += '<speech speaker="' + president_uri + '">' + line
                    is_speech_open = True
                    new_lines.append(new_line)
                    continue

                else:
                    if utils.full_process(name):
                        # if name is more than one word, use surname + name and partial ratio
                        if len(name.split()) > 1:
                            surnames_names = list(
                                people_dataset["surname"].str.lower() + " " + people_dataset["name"].str.lower()
                            )
                            best_match = process.extractOne(
                                name.lower(),
                                surnames_names,
                                scorer=fuzz.partial_ratio,
                                score_cutoff=90,
                            )
                            if best_match:
                                best_match_uri = people_dataset.loc[
                                    people_dataset["surname"].str.lower() + " " + people_dataset["name"].str.lower()
                                    == best_match[0]
                                ]["URI"].iloc[0]
                        # if name is exaclty one word (not PRESIDENTE), use only surname and ratio
                        else:
                            best_match = process.extractOne(
                                name.lower(),
                                list(people_dataset["surname"].str.lower()),
                                scorer=fuzz.ratio,
                                score_cutoff=85,
                            )
                            if best_match:
                                best_match_uri = people_dataset.loc[
                                    people_dataset["surname"].str.lower() == best_match[0]
                                ]["URI"].iloc[0]
                        # if among any of the two cases there is a match, tag the line with the URI
                        if best_match:
                            if is_speech_open:
                                new_line += '</speech><speech speaker="' + best_match_uri + '">' + line
                            else:
                                new_line += '<speech speaker="' + best_match_uri + '">' + line
                            is_speech_open = True
                        new_lines.append(new_line)
                        continue

            ### case 2: names to tag are a mix of lowercase and uppercase
            elif cam == 1 and leg in [
                "regno_11",
                "regno_12",
                "regno_13",
                "regno_14",
                "regno_15",
                "regno_16",
                "regno_17",
                "regno_18",
                "regno_19",
            ]:
                # locate the only uppercase series of words (or single word) in the line

                words = line.split()
                for i, word in enumerate(words):
                    if i >= 4:
                        break
                    if has_majority_uppercase(word):
                        if len(word) == 1:
                            break
                        name.append(word)
                        if word.endswith(".") or word.endswith(","):
                            break

                name = " ".join(name)

                if "PRESIDENTE" in name and is_presidency_open:
                    if is_speech_open:
                        new_line += '</speech><speech speaker="' + president_uri + '">' + line
                    else:
                        new_line += '<speech speaker="' + president_uri + '">' + line
                    is_speech_open = True
                    new_lines.append(new_line)
                    continue
                else:
                    if utils.full_process(name):
                        # if name is more than one word, use surname + name and partial ratio
                        if len(name.split()) > 1:
                            surnames_names = list(people_dataset["surname"] + " " + people_dataset["name"])
                            best_match = process.extractOne(
                                name,
                                surnames_names,
                                scorer=fuzz.partial_ratio,
                                score_cutoff=90,
                            )
                            if best_match:
                                best_match_uri = people_dataset.loc[
                                    people_dataset["surname"] + " " + people_dataset["name"] == best_match[0]
                                ]["URI"].iloc[0]
                        # if name is exaclty one word (not PRESIDENTE), use only surname and ratio
                        else:
                            best_match = process.extractOne(
                                name,
                                list(people_dataset["surname"]),
                                scorer=fuzz.ratio,
                                score_cutoff=85,
                            )
                            if best_match:
                                best_match_uri = people_dataset.loc[people_dataset["surname"] == best_match[0]][
                                    "URI"
                                ].iloc[0]
                        # if among any of the two cases there is a match, tag the line with the URI
                        if best_match:
                            if is_speech_open:
                                new_line += '</speech><speech speaker="' + best_match_uri + '">' + line
                            else:
                                new_line += '<speech speaker="' + best_match_uri + '">' + line
                            is_speech_open = True
                        new_lines.append(new_line)
                        continue

            # case 3: names are all uppercase
            else:
                if has_majority_uppercase(line.split(".")[0]) or has_majority_uppercase(line.split(",")[0]):
                    name = []
                    words = line.split()
                    # find name among words, keep all uppercase words UNLESS they are one letter long and more than four words long
                    for word in words:
                        if has_majority_uppercase(word):
                            if len(word) == 1:
                                break
                            name.append(word)
                            if word.endswith(".") or word.endswith(","):
                                break
                            if len(name) >= 4:
                                break
                    name = " ".join(name)

                    # if name is PRESIDENTE search for president in charge and tag the speech with it
                    if "PRESIDENTE" in name and is_presidency_open:
                        if is_speech_open:
                            new_line += '</speech><speech speaker="' + president_uri + '">' + line
                        else:
                            new_line += '<speech speaker="' + president_uri + '">' + line
                        is_speech_open = True
                        new_lines.append(new_line)
                        continue
                    else:
                        if utils.full_process(name):
                            # if name is more than one word, use surname + name and partial ratio
                            if len(name.split()) > 1:
                                surnames_names = list(people_dataset["surname"] + " " + people_dataset["name"])
                                best_match = process.extractOne(
                                    name,
                                    surnames_names,
                                    scorer=fuzz.partial_ratio,
                                    score_cutoff=90,
                                )
                                if best_match:
                                    best_match_uri = people_dataset.loc[
                                        people_dataset["surname"] + " " + people_dataset["name"] == best_match[0]
                                    ]["URI"].iloc[0]
                            # if name is exaclty one word (not PRESIDENTE), use only surname and ratio
                            else:
                                best_match = process.extractOne(
                                    name,
                                    list(people_dataset["surname"]),
                                    scorer=fuzz.ratio,
                                    score_cutoff=85,
                                )
                                if best_match:
                                    best_match_uri = people_dataset.loc[people_dataset["surname"] == best_match[0]][
                                        "URI"
                                    ].iloc[0]
                            # if among any of the two cases there is a match, tag the line with the URI
                            if best_match:
                                if is_speech_open:
                                    new_line += '</speech><speech speaker="' + best_match_uri + '">' + line
                                else:
                                    new_line += '<speech speaker="' + best_match_uri + '">' + line
                                is_speech_open = True
                            new_lines.append(new_line)
                            continue
                else:
                    new_line = line
        else:
            new_line = line

        #     words = line.split()
        #     for word in words:
        #         if not has_majority_uppercase(word):
        #             if (
        #                     cam == 0 and leg not in ["regno_15", "regno_16", "regno_17", "regno_18", "regno_19", "regno_20", "regno_21"]
        #                 ) or (cam == 1 and leg not in ["regno_08", "regno_09", "regno_10"]):
        #                 name.append(word)
        #                 if word.endswith(".") or word.endswith(","):
        #                     break
        #     # if line starts with one or more uppercase words followed by a comma or a dot, check if they are in the dataset

        #             break
        #         else:
        #             if len(word) == 1:
        #                 break
        #             name.append(word)
        #             if word.endswith(".") or word.endswith(","):
        #                 break
        #         if len(name) >= 4:
        #             break

        #     name = " ".join(name)
        #     if "PRESIDENTE" in name and is_presidency_open:
        #         if is_speech_open:
        #             new_line += '</speech><speech speaker="' + president_uri + '">' + line
        #         else:
        #             new_line += '<speech speaker="' + president_uri + '">' + line
        #         is_speech_open = True
        #         new_lines.append(new_line)
        #         continue

        #     else:
        #         surnames_names = list(people_dataset["surname"] + " " + people_dataset["name"])
        #         if utils.full_process(name):
        #             if len(name.split()) > 1:
        #                 best_match = process.extractOne(
        #                     name,
        #                     surnames_names,
        #                     scorer=fuzz.partial_ratio,
        #                     score_cutoff=90,
        #                 )
        #                 if best_match:
        #                     best_match_uri = people_dataset.loc[
        #                         people_dataset["surname"] + " " + people_dataset["name"] == best_match[0]
        #                     ]["URI"].iloc[0]

        #             else:
        #                 best_match = process.extractOne(
        #                     name,
        #                     list(people_dataset["surname"]),
        #                     scorer=fuzz.ratio,
        #                     score_cutoff=85,
        #                 )
        #                 if best_match:
        #                     best_match_uri = people_dataset.loc[people_dataset["surname"] == best_match[0]][
        #                         "URI"
        #                     ].iloc[0]

        #             if best_match:
        #                 if is_speech_open:
        #                     new_line += '</speech><speech speaker="' + best_match_uri + '">' + line
        #                 else:
        #                     new_line += '<speech speaker="' + best_match_uri + '">' + line
        #                 is_speech_open = True
        #             new_lines.append(new_line)
        #             continue
        # else:
        #     new_line = line

        new_lines.append(new_line)

    if is_speech_open:
        new_lines.append("</speech>")

    if is_presidency_open:
        new_lines.append("</presidency>")

    new_lines.append("</document>")

    with open(out, "w", encoding="utf-8") as output_file:
        output_file.writelines(new_lines)

    # people can be recognized by the fact that they are written in uppercase and are followed by a comma or a dot.
    # if they are, tag them with their URI. If they are not, check if the first three words are in the dataset. If they are, tag them with their URI.


def fillOutputDocument(
    output_file, text_values, page_num, tot_page_num, prev_last_char, people_dataset, is_gold, current_president="bruh"
):
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

    #     text_values = list(
    #     zip(
    #         new_cols_df["block_num"],
    #         new_cols_df["par_num"],
    #         new_cols_df["page_num"],
    #         new_cols_df["text"],
    #         new_cols_df["conf"],
    #         new_cols_df["top"],
    #         new_cols_df["height"],
    #         new_cols_df["word_num"],
    #     )
    # )

    if is_gold:
        page_num = 1
        tot_page_num = 1

    if page_num > 1:
        if prev_last_char == ".":
            output_file.write("\n")
        elif prev_last_char != "-":
            output_file.write(" ")

    # if page_num == 1:
    #     output_file.write("<?xml version='1.0' encoding='UTF-8'?>\n<document>")

    # prev_top = None
    closing_count = 0
    is_truncated = False
    # word_count = 0
    block = 0
    is_beginning_of_block = False
    start_of_block = ""

    for word_count, tup in enumerate(text_values):
        conf = int(tup[4])
        word_num = int(tup[7])

        if conf == -1:
            closing_count += 1
            continue

        curr_word = str(tup[3])
        sep = ""

        is_next_line = False
        top = int(tup[5]) - int(tup[6])

        # if block != tup[0] or is_beginning_of_block:
        #     if (
        #         (curr_word.endswith(".") or curr_word.endswith(","))
        #         and conf >= 85
        #         and curr_word.isupper()
        #         and word_num == 1
        #     ):
        #         fuzzy_name = curr_word.lower()

        #         if lev(fuzzy_name, "PRESIDENTE") <= 2:
        #             output_file.write("</speech><speech speaker=" + current_president + ">")

        #         best_match = process.extractOne(
        #             fuzzy_name,
        #             list(people_dataset["surname"].str.lower()),
        #             scorer=fuzz.token_sort_ratio,
        #             score_cutoff=80,
        #         )

        #         if best_match:
        #             person_uri = people_dataset.loc[people_dataset["surname"].str.lower() == best_match[0]]["URI"].iloc[
        #                 0
        #             ]
        #             output_file.write("</speech><speech speaker=" + person_uri + ">")

        #     else:
        #         if len(start_of_block.split()) >= 3:
        #             fuzzy_name = start_of_block.lower()
        #             best_match = process.extractOne(
        #                 fuzzy_name,
        #                 list(people_dataset["surname"].str.lower()),
        #                 scorer=fuzz.token_sort_ratio,
        #                 score_cutoff=70,
        #             )
        #             if best_match:
        #                 print("best match: " + str(best_match))
        #                 person_uri = people_dataset.loc[people_dataset["surname"].str.lower() == best_match[0]][
        #                     "URI"
        #                 ].iloc[0]
        #                 output_file.write("</speech><speech speaker=" + person_uri + ">")
        #             else:
        #                 output_file.write(start_of_block)
        #             start_of_block = ""
        #             is_beginning_of_block = False
        #         else:
        #             is_beginning_of_block = True
        #             start_of_block += curr_word + " "
        #             continue

        if closing_count == 2 or block != tup[0]:
            sep = "\n"

        else:
            sep = " "

        if is_truncated:
            sep = ""
            is_truncated = False

        if curr_word.endswith("-"):
            curr_word = curr_word[:-1]
            is_truncated = True

        output_file.write(sep + curr_word)

        closing_count = 0
        block = tup[0]

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


def checkNewCols(df):
    window_size = 7

    indexes_to_del = []

    for i in range(len(df["text"]) - window_size + 1):
        if any(s != "" or s != " " or not pd.isna(s) for s in df["text"].iloc[i : i + window_size]):
            indexes_to_del = list(range(i, i + window_size))

    if len(indexes_to_del) == 0:
        return df

    clean_df = df[~df.index.isin(indexes_to_del)]

    # fix "line continues on other column" case

    return clean_df.reset_index(drop=True)


def has_majority_uppercase(input_string):
    # Initialize counters for uppercase and lowercase characters
    uppercase_count = 0
    lowercase_count = 0

    # Iterate through each character in the string
    for char in input_string:
        if char.isupper():
            uppercase_count += 1
        elif char.islower():
            lowercase_count += 1

    # Compare the counts to determine if the majority is uppercase
    return uppercase_count > lowercase_count
