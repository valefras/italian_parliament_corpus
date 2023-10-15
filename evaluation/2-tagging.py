
import os
from cleaning_modules.formatting_func import preprocessDocument
import argparse
from datetime import datetime
import json
from datetime import datetime
import locale
import pandas as pd
from bs4 import BeautifulSoup
from tagging_modules.tagging import createPeopleDatasets
import re
from cleaning_modules.formatting_func import performTagging
from utils import leg_mapping, ordered_leg_names
from string import punctuation
from lxml import etree as ET
import os
import pandas as pd
import csv
from ..cleaning_modules.camera_cleaning import cameraDocType, cameraRemoveIntest
from ..cleaning_modules.senato_cleaning import senatoDocType, senatoRemoveIntest
from Levenshtein import distance as lev
import numpy as np
from collections import Counter
from fuzzywuzzy import fuzz, process, utils
import re
from string import punctuation
import xml.etree.ElementTree as ET

def performTagging(out, leg, cam, people_dataset, president_for_gold="no_president"):
    with open(out, "r", encoding="utf-8") as input_file:
        lines = input_file.readlines()

    is_presidency_open = False
    is_speech_open = False
    president = ""
    if president_for_gold != "no_president":
        print("president for gold: " + president_for_gold)
        president_uri = president_for_gold

    new_lines = ["<?xml version='1.0' encoding='UTF-8'?>\n", "<document>\n"]

    for line in lines:
        line = line.replace("<", "").replace(">", "").replace("&", "e")

        new_line = ""
        name = []
        line = remove_whitespace_and_punctuation_from_beginning(line)
        if len(line) == 0:
            continue

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
                    if is_speech_open and is_presidency_open:
                        new_line += '</speech></presidency><presidency president="' + president_uri + '">' + line
                        is_speech_open = False
                    elif is_presidency_open:
                        new_line += '</presidency><presidency president="' + president_uri + '">' + line
                    elif is_speech_open:
                        new_line += '</speech><presidency president="' + president_uri + '">' + line
                        is_speech_open = False
                    else:
                        new_line += '<presidency president="' + president_uri + '">' + line
                    is_presidency_open = True
                    president = president_uri
                else:
                    new_line = line
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

                if (
                    "Presidente" in name
                    and name.endswith(".")
                    and (is_presidency_open or president_for_gold != "no_president")
                ):
                    if is_speech_open:
                        new_line += '</speech><speech speaker="' + president_uri + '" is_president="true">' + line
                    else:
                        new_line += '<speech speaker="' + president_uri + '" is_president="true">' + line
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
                                score_cutoff=80,
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
                                scorer=fuzz.token_set_ratio,
                                score_cutoff=80,
                            )
                            if best_match:
                                best_match_uri = people_dataset.loc[
                                    people_dataset["surname"].str.lower() == best_match[0]
                                ]["URI"].iloc[0]
                        # if among any of the two cases there is a match, tag the line with the URI
                        if best_match:
                            if is_speech_open:
                                new_line += (
                                    '</speech><speech speaker="' + best_match_uri + '" is_president="false">' + line
                                )
                            else:
                                new_line += '<speech speaker="' + best_match_uri + '" is_president="false">' + line
                            is_speech_open = True
                        else:
                            new_line = line
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

                if "PRESIDENTE" in name and (is_presidency_open or president_for_gold != "no_president"):
                    if is_speech_open:
                        new_line += '</speech><speech speaker="' + president_uri + '" is_president="true">' + line
                    else:
                        new_line += '<speech speaker="' + president_uri + '" is_president="true">' + line
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
                                score_cutoff=80,
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
                                scorer=fuzz.token_set_ratio,
                                score_cutoff=80,
                            )
                            if best_match:
                                best_match_uri = people_dataset.loc[people_dataset["surname"] == best_match[0]][
                                    "URI"
                                ].iloc[0]
                        # if among any of the two cases there is a match, tag the line with the URI
                        if best_match:
                            if is_speech_open:
                                new_line += (
                                    '</speech><speech speaker="' + best_match_uri + '" is_president="false">' + line
                                )
                            else:
                                new_line += '<speech speaker="' + best_match_uri + '" is_president="false">' + line
                            is_speech_open = True
                        else:
                            new_line = line
                        new_lines.append(new_line)
                        continue
                new_line = line

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
                    if leg in [
                        "repubblica_13",
                        "repubblica_14",
                        "repubblica_15",
                        "repubblica_16",
                        "repubblica_17",
                        "repubblica_18",
                    ]:
                        name = re.sub("[\(\[].*?[\)\]]", "", name)

                    # if name is PRESIDENTE search for president in charge and tag the speech with it
                    if "PRESIDENTE" in name and (is_presidency_open or president_for_gold != "no_president"):
                        if is_speech_open:
                            new_line += '</speech><speech speaker="' + president_uri + '" is_president="true">' + line
                        else:
                            new_line += '<speech speaker="' + president_uri + '" is_president="true">' + line
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
                                    scorer=fuzz.token_sort_ratio
                                    if cam == 0
                                    and leg
                                    in [
                                        "repubblica_13",
                                        "repubblica_14",
                                        "repubblica_15",
                                        "repubblica_16",
                                        "repubblica_17",
                                        "repubblica_18",
                                    ]
                                    else fuzz.partial_ratio,
                                    score_cutoff=80,
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
                                    scorer=fuzz.token_set_ratio,
                                    score_cutoff=80,
                                )
                                if best_match:
                                    best_match_uri = people_dataset.loc[people_dataset["surname"] == best_match[0]][
                                        "URI"
                                    ].iloc[0]
                            # if among any of the two cases there is a match, tag the line with the URI
                            if best_match:
                                if is_speech_open:
                                    new_line += (
                                        '</speech><speech speaker="' + best_match_uri + '" is_president="false">' + line
                                    )
                                else:
                                    new_line += '<speech speaker="' + best_match_uri + '" is_president="false">' + line
                                is_speech_open = True
                            else:
                                new_line = line
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

    return president


def remove_whitespace_and_punctuation_from_beginning(input_string):
    # Define a regular expression pattern to match whitespace and punctuation at the beginning of the string

    out_string = input_string.lstrip(punctuation).lstrip(" ")

    # Use re.sub to replace the matched pattern with an empty string

    return out_string