import jiwer
from symspellpy.symspellpy import SymSpell
import string
from utils import leg_mapping
import pandas as pd
import argparse
import os
import seaborn as sns
import matplotlib.pyplot as plt
import math
import statistics
from collections import Counter
from lxml import etree


string.punctuation += "«»–"


def computeSymspellBase(test_set_path, output_path, dict_folder, max_edit_distance):
    """
    starting from the clean texts computed from the preprocessing, corrects the using the default italian dictionary
    :param test_set_path: path to the clean texts
    :param output_path: where to output corrected texts
    :param max_edit_distance: max edit distance for correction
    """

    sym_spell = SymSpell(max_dictionary_edit_distance=max_edit_distance)

    dictionary_path = os.path.abspath(os.path.join(dict_folder, "it-100k.txt"))

    sym_spell.load_dictionary(
        dictionary_path,
        term_index=0,
        count_index=1,
        separator=" ",
        encoding="utf-8",
    )

    for file in os.listdir(test_set_path):
        with open(test_set_path + "/" + file, "r", encoding="utf-8") as f1:
            lines = f1.readlines()

        os.makedirs(os.path.dirname(output_path + "/" + file), exist_ok=True)

        with open(output_path + "/" + file, "w", encoding="utf-8") as f2:
            for line in lines:
                # clean_line = line.translate(str.maketrans("", "", string.punctuation))

                suggestions = sym_spell.lookup_compound(
                    line,
                    max_edit_distance=max_edit_distance,
                    transfer_casing=True,
                )
                corrected_line = ""
                for suggestion in suggestions:
                    corrected_line += suggestion.term + " "
                f2.write(corrected_line + "\n")


def computeSymspellWindowedDictionaries(test_set_path, output_path, dict_folder, max_edit_distance):
    """
    computes the corrected texts using windowed dictionaries
    :param test_set_path: path to the clean texts
    :param output_path: where to output corrected texts
    :param dict_path: path to the windowed dictionaries
    :param max_edit_distance: max edit distance for correction
    """

    global leg_mapping

    for file in os.listdir(test_set_path):
        with open(test_set_path + "/" + file, "r", encoding="utf-8") as f1:
            lines = f1.readlines()

        os.makedirs(os.path.dirname(output_path + "/" + file), exist_ok=True)

        # get right dictionary for file by using the leg_mapping
        leg_raw = file.split("-")[1]
        leg = leg_mapping[leg_raw] if leg_raw in leg_mapping else leg_raw

        dictionary_path = os.path.abspath(dict_folder + "/" + leg + ".txt")

        sym_spell = SymSpell(max_dictionary_edit_distance=max_edit_distance)

        sym_spell.load_dictionary(
            dictionary_path,
            term_index=0,
            count_index=1,
            separator=" ",
            encoding="utf-8",
        )

        with open(output_path + "/" + file, "w", encoding="utf-8") as f2:
            for line in lines:
                # clean_line = line.translate(str.maketrans("", "", string.punctuation))

                suggestions = sym_spell.lookup_compound(
                    line,
                    max_edit_distance=max_edit_distance,
                    transfer_casing=True,
                )
                corrected_line = ""
                for suggestion in suggestions:
                    corrected_line += suggestion.term + " "
                f2.write(corrected_line + "\n")


def evaluateTags(gold_standard_folder, test_set_folder):
    print("eval tags")
    # open gold standard
    # open test set

    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for gold_file in os.listdir(gold_standard_folder):
        print(gold_file)
        with open(gold_standard_folder + "/" + gold_file, "r", encoding="utf-8") as f1:
            gold = f1.read()

        with open(test_set_folder + "/" + gold_file, "r", encoding="utf-8") as f2:
            pred = f2.read()

        root = etree.fromstring(bytes(gold, encoding="utf-8"))

        # Iterate through all elements in the XML
        for elem in root.iter():
            # Check if the word_to_delete is in the text content of the element
            if "PRESIDENTE" in elem.text or "Presidente" in elem.text:
                # If the word is found, remove the element
                if elem.getparent() is not None:
                    parent = elem.getparent()
                    parent.remove(elem)

        gold = etree.tostring(root, pretty_print=True).decode()

        # same for pred
        root_pred = etree.fromstring(bytes(pred, encoding="utf-8"))
        # Iterate through all elements in the XML
        for elem in root_pred.iter():
            # Check if the word_to_delete is in the text content of the element
            if "PRESIDENTE" in elem.text or "Presidente" in elem.text:
                # If the word is found, remove the element
                if elem.getparent() is not None:
                    parent = elem.getparent()
                    parent.remove(elem)

        pred = etree.tostring(root_pred, pretty_print=True).decode()

        # check if speech tag exists in either file
        # if not, skip file
        if "</speech>" not in gold or "</speech>" not in pred:
            continue

        gold_xml = pd.read_xml(gold, xpath=".//speech")
        pred_xml = pd.read_xml(pred, xpath=".//speech")

        # Parse the XML

        gold_xml = gold_xml[["speaker"]]
        pred_xml = pred_xml[["speaker"]]

        gold_list = [str(x).split("/")[-1] for x in gold_xml["speaker"]]
        pred_list = [str(x).split("/")[-1] for x in pred_xml["speaker"]]

        gold_speakers = Counter(gold_list)
        pred_speakers = Counter(pred_list)

        # Calculate True Positives, False Positives, and False Negatives
        true_positives += sum((gold_speakers & pred_speakers).values())  # Count of common elements
        false_positives += sum(
            (pred_speakers - gold_speakers).values()
        )  # Elements in predicted but not in gold standard
        false_negatives += sum(
            (gold_speakers - pred_speakers).values()
        )  # Elements in gold standard but not in predicted

        print(gold_speakers, pred_speakers)

        temp_true_positives = sum((gold_speakers & pred_speakers).values())
        temp_false_positives = sum((pred_speakers - gold_speakers).values())
        temp_false_negatives = sum((gold_speakers - pred_speakers).values())

        print(
            temp_true_positives / (temp_true_positives + temp_false_positives),
            temp_true_positives / (temp_true_positives + temp_false_negatives),
        )

    # Calculate Precision and Recall
    precision = true_positives / (true_positives + false_positives)
    recall = true_positives / (true_positives + false_negatives)

    # print(gold_speakers, pred_speakers)
    # print(true_positives, false_positives, false_negatives)

    print("Precision:", precision)
    print("Recall:", recall)

    # jaccard = round(counter_cosine_similarity(gold_speakers, pred_speakers), 3)

    # cosine_similarities.append(jaccard)
    # print(jaccard)

    # compute cosine similarity between the two counters

    # print(cosine_similarities)
    # print(statistics.mean(cosine_similarities))


def evaluateText(
    gold_standard_folder,
    clean_text_folder,
    corrected_base_folder,
    corrected_windowed_folder,
):
    """
    calculates the WER and CER for the corrected texts, with regards to the golden_standard
    :param golden_standard_path: path to the golden standard
    :param corrected_texts_path: path to the corrected texts
    :return: a dataframe containing results
    """

    computeSymspellBase(args.uncorrected_set_folder, args.symspell_base_set_folder, args.dict_folder, 2)

    computeSymspellWindowedDictionaries(
        args.uncorrected_set_folder,
        args.symspell_window_set_folder,
        args.dict_folder,
        2,
    )

    res = []

    for gold_file in os.listdir(gold_standard_folder):
        for file in os.listdir(clean_text_folder):
            if file == gold_file:
                with open(gold_standard_folder + "/" + gold_file, "r", encoding="utf-8") as f1:
                    gold = f1.read()
                    clean_gold = gold.translate(str.maketrans("", "", string.punctuation)).lower()

                with open(clean_text_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = pred.translate(str.maketrans("", "", string.punctuation)).lower()

                print([jiwer.wer(clean_gold, clean_pred), "WER", "Uncorrected"])

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Uncorrected"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Uncorrected"])

        for file in os.listdir(corrected_base_folder):
            if file == gold_file:
                with open(gold_standard_folder + "/" + gold_file, "r", encoding="utf-8") as f1:
                    gold = f1.read()
                    clean_gold = gold.translate(str.maketrans("", "", string.punctuation)).lower()

                with open(corrected_base_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = pred.translate(str.maketrans("", "", string.punctuation)).lower()

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Base"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Base"])

        for file in os.listdir(corrected_windowed_folder):
            if file == gold_file:
                with open(gold_standard_folder + "/" + gold_file, "r", encoding="utf-8") as f1:
                    gold = f1.read()
                    clean_gold = gold.translate(str.maketrans("", "", string.punctuation)).lower()
                with open(corrected_windowed_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = pred.translate(str.maketrans("", "", string.punctuation)).lower()

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Windowed"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Windowed"])

    print(res)
    res_data = pd.DataFrame(res, columns=["val", "cat", "set"])

    print(res_data.groupby(["cat", "set"], as_index=False).mean())

    # save results to csv
    res_data.to_csv("symspell_eval.csv", index=False)
    return res_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--dict_folder",
        type=str,
        help="Folder containing dictionaries to use for the tests.",
    )
    parser.add_argument(
        "--gold_standard_folder",
        type=str,
        default="gold_standard",
        help="Folder containing the golden standard.",
        required=False,
    )
    parser.add_argument(
        "--uncorrected_set_folder",
        type=str,
        default="uncorrected_set",
        help="Folder where the pre processed texts are stored.",
        required=False,
    )
    parser.add_argument(
        "--symspell_base_set_folder",
        type=str,
        default="base_set",
        help="Folder where to save the base Symspell-corrected set.",
        required=False,
    )
    parser.add_argument(
        "--symspell_window_set_folder",
        type=str,
        default="window_set",
        help="Folder where to save the windowed Symspell-corrected set.",
        required=False,
    )

    parser.add_argument(
        "--eval_tags_only",
        action="store_true",
    )
    parser.add_argument(
        "--eval_text_only",
        action="store_true",
    )
    parser.add_argument(
        "--test_set_folder",
        type=str,
        default="test_set",
        help="Folder containing the test set.",
        required=False,
    )
    args = parser.parse_args()
    if args.eval_tags_only:
        evaluateTags(args.gold_standard_folder, args.test_set_folder)
    elif args.eval_text_only:
        evaluateText(
            args.gold_standard_folder,
            args.uncorrected_set_folder,
            args.symspell_base_set_folder,
            args.symspell_window_set_folder,
        )
    else:
        evaluateTags(args.gold_standard_folder, args.test_set_folder)
        evaluateText(
            args.gold_standard_folder,
            args.uncorrected_set_folder,
            args.symspell_base_set_folder,
            args.symspell_window_set_folder,
        )
