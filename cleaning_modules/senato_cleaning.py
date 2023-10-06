from Levenshtein import distance as lev
import csv
from collections import Counter
import pandas as pd
import numpy as np


def frequency_count(numbers):
    counter = Counter(numbers)
    return counter.most_common(1)[0][0]


def assessDocType(df, leg, page_num):
    """
    tries to assess the type of senato document based on the first 120 words of a page
    :param df: dataframe of the page
    :param date: date of the document
    :param page_num: page number
    :return page type
    """

    sorted_df = df.sort_values("top")[:120]
    words_lst = sorted_df["text"]

    ### I legislatura repubblicana, 3 tipi di documenti: giunta, commissione e assemblea
    if leg == "cg_4" or leg == "cg_5":
        for word in words_lst:
            word = str(word)
            if lev(word, "BILANCIO") < 3:
                return 1
        return 0

    if leg == "cg_12":
        for word in words_lst:
            word = str(word)

            if lev(word, "DISEGNI") < 3:
                return 1
            if lev(word, "Senato") < 3:
                return 2
            if lev(word, "COMITATO") < 3:
                return 3
        return 0

    if leg == "cg_11":
        for word in words_lst:
            word = str(word)

            if lev(word, "DISEGNI") < 3:
                return 1
            # if lev(word, "Senato") < 3:
            #     return 2
        return 0

    if leg == "cg_10":
        for word in words_lst:
            word = str(word)
            if lev(word, "DISEGNI") < 3:
                return 1
            if lev(word, "Senato") < 3:
                return 2
        return 0

    if leg == "cg_9":
        for word in words_lst:
            word = str(word)
            if lev(word, "BILANCIO") < 3:
                return 1
            if lev(word, "MASSONICA") < 3:
                return 2
        return 0

    if leg == "cg_8":
        for word in words_lst:
            word = str(word)
            if lev(word, "SINDONA") < 3:
                return 1
        return 0

    if leg == "cg_7":
        for word in words_lst:
            word = str(word)
            if lev(word, "BILANCIO") < 3:
                return 1
        return 0

    # if leg == "l_5":
    #     for word in words_lst:
    #         word = str(word)
    #         if lev(word, "DISEGNI") < 3:
    #             return 1
    #     return 0


def senatoRemoveIntest(df, leg, document_type, page_num):
    """
    removes intestation from a senato document, based on the legislature and document type
    :param df: dataframe of the page
    :param leg: legislature of the document
    :param document_type: document type of the document
    :param page_num: page number
    :return clean dataframe
    """
    sorted_df = df.sort_values("top")[:80]
    words_lst = sorted_df["text"]

    padding = 50

    ins_cost, del_cost, sub_cost = 1, 1, 1

    ### 1 leg assemblee
    target_word = "DISCUSSIONI"

    ### 1 leg commissioni
    if leg == "cg_1":
        if page_num == 1:  ### no intestation in first page
            return df

        target_word = "RIUNIONE"

    if leg == "l_1":
        target_word = "Disegni"

    if leg == "cg_2":
        if page_num == 1:  ### no intestation in first page
            return df

        distances = words_lst.apply(lambda x: min(lev(str(x), "SEDUTA"), lev(str(x), "RIUNIONE")))
        min_dist = distances.idxmin()

        max_h = sorted_df.loc[min_dist]["top"] + 50

        return df[df["top"] > max_h].reset_index(drop=True)

    if leg == "l_2":
        target_word = "DISEGNI"

    if (
        leg == "l_3"
        or leg == "l_4"
        or leg == "l_5"
        or leg == "l_6"
        or leg == "l_7"
        or leg == "l_8"
        or leg == "l_9"
        or leg == "l_10"
        or leg == "l_11"
        or leg == "l_12"
    ):
        if page_num == 1:  ### no intestation in first page
            return df
        target_word = "DISEGNI"

    if (
        leg == "3"
        or leg == "4"
        or leg == "5"
        or leg == "6"
        or leg == "7"
        or leg == "8"
        or leg == "9"
        or leg == "10"
        or leg == "11"
        or leg == "12"
    ):
        if page_num == 1:  ### no intestation in first page
            return df

        target_word = "ASSEMBLEA"

    if leg == "cg_3":
        if page_num == 1:  ### no intestation in first page
            return df
        target_word = "SEDUTA"

    if leg == "cg_4" or leg == "cg_5":
        if document_type == 0:
            if page_num == 1:  ### no intestation in first page
                return df
            target_word = "SEDUTA"
        elif document_type == 1:
            target_word = "BILANCIO"

    if leg == "cg_12":
        if document_type == 0:
            if page_num == 1:
                return df

            distances = words_lst.apply(lambda x: min(lev(str(x), "SEDUTA"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

        if document_type == 1:
            target_word = "DISEGNI"

        if document_type == 2:
            if page_num == 1:
                return df

            distances = words_lst.apply(lambda x: min(lev(str(x), "RESOCONTO"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

    if leg == "cg_11":
        if document_type == 0:
            if page_num == 1:
                return df

            distances = words_lst.apply(lambda x: min(lev(str(x), "SEDUTA"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

        if document_type == 1:
            if page_num == 1:
                return df
            target_word = "DISEGNI"

        if document_type == 2:
            if page_num == 1:
                return df

            distances = words_lst.apply(lambda x: min(lev(str(x), "RESOCONTO"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

        if document_type == 3:
            if page_num == 1:
                return df

            distances = words_lst.apply(lambda x: min(lev(str(x), "COMITATO"), lev(str(x), "SEDUTA")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

    if leg == "cg_10":
        if document_type == 0:
            if page_num == 1:
                return df

            distances = words_lst.apply(lambda x: min(lev(str(x), "RESOCONTO"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

        if document_type == 1:
            if page_num == 1:
                return df
            target_word = "DISEGNI"

    if leg == "cg_9":
        if document_type == 0:
            if page_num == 1:
                return df
            distances = words_lst.apply(lambda x: min(lev(str(x), "RESOCONTO"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

        if document_type == 1:
            target_word = "BILANCIO"

        if document_type == 2:
            if page_num == 1:
                return df
            target_word = "Camera"

    if leg == "cg_8":
        if document_type == 0:
            if page_num == 1:
                return df
            distances = words_lst.apply(lambda x: min(lev(str(x), "RESOCONTO"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

        if document_type == 1:
            if page_num == 1:
                return df
            target_word = "Camera"

    if leg == "cg_7":
        if document_type == 0:
            if page_num == 1:
                return df
            distances = words_lst.apply(lambda x: min(lev(str(x), "RESOCONTO"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

        if document_type == 1:
            target_word = "BILANCIO"

        if leg == "cg_6":
            if page_num == 1:
                return df
            distances = words_lst.apply(lambda x: min(lev(str(x), "RESOCONTO"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

    if leg[:5] == "regno" and int(leg[-2:].replace("_", "")) <= 11:
        distances = words_lst.apply(lambda x: min(lev(str(x), "TORNATA"), lev(str(x), "SESSIONE")))
        min_dist = distances.idxmin()

        max_h = sorted_df.loc[min_dist]["top"] + 50

        return df[df["top"] > max_h].reset_index(drop=True)

    # if leg == "l_4" or leg == "l_5":
    #     if document_type == 0:
    #         return df
    #     elif document_type == 1:
    #         target_word = "DISEGNI"

    distances = words_lst.apply(lambda x: lev(str(x), target_word, weights=(ins_cost, del_cost, sub_cost)))
    min_dist = distances.idxmin()

    max_h = sorted_df.loc[min_dist]["top"] + padding

    return df[df["top"] > max_h].reset_index(drop=True)


def senatoDocType(leg, page_num, page_list):
    """
    assesses the document type of a senato document based on the date and the first 3 pages
    :param leg: legislature of the document
    :param page_num: page number
    :param page_list: list of pages
    :return document type
    """
    document_type = None

    if leg[:5] == "regno":
        return

    if leg[-1] == "1" or leg[-1] == "2" or leg[-1] == "3" or leg == "4" or leg == "5" or leg == "6" or leg == "12":
        return

    # check document type from first 3 pages (necessary only starting from 1943, since all documents were equal before)
    document_type_list = []
    # check first three pages or less if there are less than 3 pages
    num_pages_check = min(len(page_list), 5)
    for page in np.random.choice(page_list, num_pages_check):
        dataframe = pd.read_csv(page, sep="\t", quoting=csv.QUOTE_NONE, encoding="utf-8")
        # if page is empty skip it
        if dataframe.shape[0] < 3:
            continue

        ########### special cases ################

        ### loggia massonica p2

        if leg == "cg_9" and 2 in document_type_list:
            continue

        if leg == "cg_8" and 1 in document_type_list:
            continue

        document_type_list.append(assessDocType(dataframe, leg, page_num))

        # document type is the most frequent one in first three pages
    if len(document_type_list) > 0:
        return frequency_count(document_type_list)
    return None
