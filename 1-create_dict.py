import os
import argparse
import csv
import pandas as pd
from pandas import Index
from tqdm import tqdm
from utils import Dictionary, ordered_legs


def createLegDict(cam, path, confidence_cutoff=94):
    """
    Create a dictionary of words and frequencies for a specific legislatura
    :param cam: 0 for camera, 1 for senato
    :param path: path to the folder containing the legislatura documents
    :param confidence_cutoff: confidence cutoff for tesseract
    :return: dictionary of words and frequencies for the legislatura
    """
    # start_time = time.time()
    final_dict = Dictionary()
    if cam == 0 or (
        cam == 1 and (path.split("/")[-1] in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"])
    ):
        for day in os.listdir(path):
            for doc in os.listdir(os.path.join(path, day)):
                if doc.endswith("out"):
                    input_paths = os.listdir(os.path.join(path, day, doc))
                    page_list = [os.path.join(path, day, doc, x) for x in input_paths if x.endswith("tsv")]
                    single_doc_dict = createDocDict(page_list, confidence_cutoff)
                    final_dict.merge(single_doc_dict)
    else:
        for doc in os.listdir(path):
            if doc.endswith("out"):
                input_paths = os.listdir(os.path.join(path, doc))
                page_list = [os.path.join(path, doc, x) for x in input_paths if x.endswith("tsv")]
                single_doc_dict = createDocDict(page_list, confidence_cutoff)
                final_dict.merge(single_doc_dict)
    # print("--- %s seconds ---" % (time.time() - start_time))
    return final_dict


def createDocDict(pages, confidence_cutoff):
    """
    create a dictionary of words and frequencies for a single document
    :param pages: list of paths to the pages of the document
    :param confidence_cutoff: confidence cutoff for tesseract
    :return: dictionary of words and frequencies for the document
    """
    doc_dict = Dictionary()
    for page in pages:
        if os.path.getsize(page) == 0:
            continue

        dataf = pd.read_csv(page, sep="\t", quoting=csv.QUOTE_NONE, encoding="utf-8")

        if (
            dataf.shape[0] < 2
            or len(dataf["text"]) == 0
            # or not pd.api.types.is_string_dtype(dataf["text"])
        ):
            continue

        dataf_clean = dataf.dropna(subset=["text"])

        dataf_clean_no_w = dataf_clean[dataf_clean["text"].astype(str).str.strip() != ""]

        dataf_clean_no_w.reset_index(drop=True, inplace=True)

        truncated_ix1 = dataf_clean_no_w[dataf_clean_no_w["text"].astype(str).str.endswith("-")].index
        truncated_ix2 = Index([x + 1 for x in truncated_ix1], dtype="int64")
        ix_to_drop = truncated_ix1.append(truncated_ix2)

        dataf_clean_trunc = dataf_clean_no_w.drop(ix_to_drop, errors="ignore", axis=0)

        # dataf_clean_trunc2 = dataf_clean_trunc1.drop(truncated_ix2, errors="ignore", axis=0)
        # print(dataf_clean_trunc2.shape)

        # count words in each page and return a dictionary of words and frequencies using vectorization
        tokens = (
            # first remove all the words with confidence < confidence_cutoff
            dataf_clean_trunc.loc[dataf_clean_trunc["conf"] > confidence_cutoff, "text"].astype(str)
            # then remove all punctuation and truncated words
            # .str.findall(
            #     r"(?!.*-$)[A-Za-zÀ-ú'-]+|[!\"#$%&()*+,./:;<=>?@\[\\\]^_`{\|}~«»—]|\d+"
            # )
            .str.findall(r"(?!.*-$)[A-zÀ-ú'-]+|\d+")
            # at this point we have a list of lists
            # we remove all the entries that are not lists
            # .apply(lambda x: x if isinstance(x, list) else None)
            # .dropna()
        )

        # try:
        tokens_unstacked = [word for sublist in tokens for word in sublist]
        # except:
        #     filtered_data = tokens.apply(
        #         lambda x: x if not isinstance(x, list) else None
        #     ).dropna()
        #     print(filtered_data)

        doc_dict.addMany(tokens_unstacked)
    # print("--- %s seconds ---" % (time.time() - start_time))

    return doc_dict


def createDictionaries(
    data_folder,
    output_folder,
    cutoff_method,
    cutoff_value,  # fuzzy_span
):
    """
    create dictionaries for a span of legilature
    :param data_folder: path to the folder containing the data
    :param output_folder: path to the folder where to save the dictionaries
    :param cutoff_method: method with which to cut the dictionary (0 = keep top n, 1 = keep words with frequency > freq_cutoff)
    :param cutoff_value: value to use for the cutoff
    """
    # :param fuzzy_span: span of legislatures to merge (deprecated)

    ########### deprecated ###########

    # def split(a, n):
    #     k, m = divmod(len(a), n)
    #     return (a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))

    # subdivided_merged = list(split(ordered_legs, math.floor(len(ordered_legs) / fuzzy_span)))
    # for sublist in tqdm(
    #     subdivided_merged,
    #     desc="Creating ordered_legs dictionary",
    #     total=len(subdivided_merged),
    #     leave=False,
    # ):

    ##################################

    os.makedirs(os.path.dirname(output_folder), exist_ok=True)

    span_dict = Dictionary()
    for leg in tqdm(
        ordered_legs,
        desc="Creating a dictionary for each legistatura",
        total=len(ordered_legs),
        leave=False,
    ):
        camera_leg = leg[0]
        senato_leg = leg[1:]
        camera_leg_path = os.path.join(data_folder, "camera", camera_leg)
        if os.path.exists(camera_leg_path):
            camera_leg_dict = createLegDict(0, camera_leg_path, args.confidence_cutoff)
            span_dict.merge(camera_leg_dict)

        if senato_leg[0] is not None:
            for senato in senato_leg:
                senato_leg_path = os.path.join(data_folder, "senato", senato)
                if os.path.exists(senato_leg_path):
                    senato_leg_dict = createLegDict(1, senato_leg_path, args.confidence_cutoff)
                    span_dict.merge(senato_leg_dict)
        if cutoff_method == 0:
            span_dict.keep_top_n(cutoff_value)
        else:
            span_dict.freq_cutoff(cutoff_value)
        # span_dict.edit_punctuation()
        span_dict.sort()
        dict_name = leg[0]
        span_dict.save(os.path.join(output_folder, dict_name + ".txt"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--data_path", type=str, default="data/", help="Path to the data to process.")
    parser.add_argument("--output_path", type=str, default="data/", help="Where to output dictionaries.")
    # parser.add_argument(
    #     "--fuzzy_span",
    #     type=int,
    #     default=1,
    #     help="Span of legislatures to merge (best split possible).",
    #     required=False,
    # )

    parser.add_argument(
        "--confidence_cutoff",
        type=int,
        default=94,
        help="Confidence cutoff for tesseract.",
        required=False,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--freq_cutoff",
        type=int,
        default=10,
        help="Frequency cutoff for words.",
        required=False,
    )
    group.add_argument(
        "--keep_top_n",
        type=int,
        default=100000,
        help="Keep top n words by frequency.",
        required=False,
    )

    args = parser.parse_args()

    # method with which to cut the dictionary (0 = keep top n, 1 = keep words with frequency > freq_cutoff)
    cut_method = 0 if args.keep_top_n else 1

    cut_value = args.keep_top_n if args.keep_top_n else args.freq_cutoff

    createDictionaries(
        args.data_path,
        args.output_path,
        cut_method,
        cut_value,  # args.fuzzy_span
    )
