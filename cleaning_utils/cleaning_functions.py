import os
import pandas as pd
import csv
from cleaning_utils.senato_cleaning import senatoDocType, senatoRemoveIntest
from cleaning_utils.camera_cleaning import cameraDocType, cameraRemoveIntest
from collections import Counter


def preprocessDocument(dir, out, strdate, leg, cam, test_folder):
    """
    processes a single document, removing intestation and padding, merging the page, processing truncated words and outputs the result in a txt file
    :param dir: path to the document
    :param out: path to the output file
    :param strdate: date of the document
    :param leg: legislature of the document
    :param cam: 0 if camera, 1 if senato
    :param test_folder: path to output the test files
    """

    # year and date are needed to clean camera documents
    if cam == 0:
        year = int(strdate[:4])
        date = int(strdate)

    out = out + ".txt"

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

    # once document type is known, remove intestation, padding, parse columns for each page

    # last_char = ""
    prev_last_char = ""
    is_gold = False

    for filename in page_list:
        clean_doc_name = filename.split(os.sep)[-2].split(".")[0]

        if cam == 1 and (leg[:2] == "cg" or leg[:1] == "l" or leg[:5] == "regno"):
            gold_format = "-".join(
                [
                    "senato",
                    leg,
                    clean_doc_name,
                    str(i),
                    "c.txt",
                ]
            )
        else:
            gold_format = "-".join(
                [
                    "camera" if cam == 0 else "senato",
                    leg,
                    strdate,
                    clean_doc_name,
                    str(i),
                    "c.txt",
                ]
            )

        if gold_format in os.listdir("../evaluation/gold_standard"):
            is_gold = True
            print("gold standard found for " + gold_format)

        dataframe = pd.read_csv(filename, sep="\t", quoting=csv.QUOTE_NONE, encoding="utf-8")

        if dataframe.shape[0] < 2:
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
                new_cols_df["par_num"],
                new_cols_df["page_num"],
                new_cols_df["text"],
                new_cols_df["conf"],
                new_cols_df["top"],
                new_cols_df["height"],
            )
        )

        with open(out, "a", encoding="utf-8") as output_file:
            # print(text_values)
            fillOutputDocument(output_file, text_values, i, prev_last_char)

        if is_gold:
            with open(test_folder + "/" + gold_format, "w", encoding="utf-8") as gold:
                fillOutputDocument(gold, text_values, i, prev_last_char)

        is_gold = False

        prev_last_char = str(new_cols_df["text"].iloc[-1])[-1]

        # prev_top = top

        # prev_last_char = last_char

        #         if not is_truncated:
        #     last_char = str(new_cols_df["text"].iloc[-1])[-1]
        # else:
        #     last_char = "-"

        i += 1

    #### delete index
    # if has_index:
    #     remove_content(out)


def fillOutputDocument(output_file, text_values, page_num, prev_last_char):
    """
    fills the output file with the text from each page
    :param output_file: file to write to
    :param text_values: list of tuples containing the text and the confidence of each word
    :param page_num: number of the page
    :param prev_last_char: last character of the previous page (for handling the case of a truncated word)
    """

    if page_num > 1:
        if prev_last_char == ".":
            output_file.write("\n")
        elif prev_last_char != "-":
            output_file.write(" ")

    # prev_top = None
    closing_count = 0
    is_truncated = False
    # word_count = 0

    for word_count, tup in enumerate(text_values):
        conf = int(tup[3])

        if conf == -1:
            closing_count += 1
            continue

        curr_word = str(tup[2])
        sep = ""

        is_next_line = False
        top = int(tup[4]) - int(tup[5])

        if closing_count == 2:
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


def frequency_count(numbers):
    counter = Counter(numbers)
    return counter.most_common(1)[0][0]


def removePadding(df):
    i = 0
    indexes_to_del = []

    while (df["text"].iloc[i] == "" or df["text"].iloc[i] == " " or pd.isna(df["text"].iloc[i])) and (i < df.shape[0]):
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

    # print(seq[i: i + window_size])

    # pattern = np.array([-1, -1, -1, 0, -1, -1, -1])

    # def match(x):
    #     return (
    #         len(x) == len(pattern)
    #         # and (x[:3][0] == pattern[:3]).all()
    #         # and (x[4:][0] == pattern[4:]).all()
    #         and (x == "" or x[3][1] == " " or pd.isna(x[3][1]))
    #     )

    # df["keep"] = np.where(df["text"].rolling(7).apply(match) == 1, False, True)

    # ranges_to_del = [range(i - 6, i + 1) for i in df[df["keep"] == False].index]

    # indexes_to_del = [num for r in ranges_to_del for num in list(r)]

    # # print(indexes_to_del)

    clean_df = df[~df.index.isin(indexes_to_del)]

    # clean_df = clean_df.drop("keep", axis=1)

    return clean_df.reset_index(drop=True)
