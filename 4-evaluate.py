import jiwer
from symspellpy.symspellpy import SymSpell
import string
from utils import leg_mapping, pre_war, post_war
import pandas as pd
import argparse
import os
import seaborn as sns
import matplotlib.pyplot as plt
import math
import statistics
from collections import Counter
import re
from lxml import etree
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


string.punctuation += "«»–’"


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
        tree = etree.parse(test_set_path + "/" + file)
        lines = etree.tostring(tree.getroot(), encoding="utf-8", method="text").decode("utf-8").split("\n")
        # with open(test_set_path + "/" + file, "r", encoding="utf-8") as f1:
        #     lines = f1.readlines()

        os.makedirs(os.path.dirname(output_path + "/" + file), exist_ok=True)

        file = file.replace(".txt", ".xml")

        with open(output_path + "/" + file, "w", encoding="utf-8") as f2:
            for line in lines:
                line = re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", line)

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
        print(file)
        tree = etree.parse(test_set_path + "/" + file)
        lines = etree.tostring(tree.getroot(), encoding="utf-8", method="text").decode("utf-8").split("\n")
        # with open(test_set_path + "/" + file, "r", encoding="utf-8") as f1:
        #     lines = f1.readlines()
        file = file.replace(".txt", ".xml")

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
                line = re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", line)
                suggestions = sym_spell.lookup_compound(
                    line,
                    max_edit_distance=max_edit_distance,
                    transfer_casing=True,
                )
                corrected_line = ""
                for suggestion in suggestions:
                    corrected_line += suggestion.term + " "
                f2.write(corrected_line + "\n")


def computeSymspellWindowedDictionariesLower(test_set_path, output_path, dict_folder, max_edit_distance):
    global leg_mapping

    for file in os.listdir(test_set_path):
        tree = etree.parse(test_set_path + "/" + file)
        lines = etree.tostring(tree.getroot(), encoding="utf-8", method="text").decode("utf-8").split("\n")

        file = file.replace(".txt", ".xml")

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
        corrected_lines = []
        split_lines = [re.split(r" (?=[A-Z])", line) for line in lines]

        for line in split_lines:
            corrected_line = ""
            for segment in line:
                if len(segment) > 0:
                    if segment[0].islower():
                        corrected_line += correctSegment(segment, sym_spell, max_edit_distance) + " "
                    else:
                        segment = re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", segment)
                        corrected_line += segment + " "
            corrected_lines.append(corrected_line)

        with open(output_path + "/" + file, "w", encoding="utf-8") as f2:
            for line in corrected_lines:
                # rid of unnecessary spaces

                line = " ".join(line.split())
                f2.write(line + "\n")


def correctSegment(segment, sym_spell, max_edit_distance):
    toRtn = ""
    if segment != "":
        segment = re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", segment)
        suggestions = sym_spell.lookup_compound(
            segment,
            max_edit_distance=max_edit_distance,
            transfer_casing=True,
        )
        for suggestion in suggestions:
            toRtn += suggestion.term + " "
    toRtn = " ".join(toRtn.split())
    return toRtn


def evaluateTags(gold_standard_folder, test_set_folder, era="all"):
    print("eval tags")
    # open gold standard
    # open test set

    true_positives = 0
    false_positives = 0
    false_negatives = 0

    gold_files = os.listdir(gold_standard_folder)

    if era == "pre":
        gold_files = [file for file in os.listdir(gold_standard_folder) if file.split("-")[1] in pre_war]
    if era == "post":
        gold_files = [file for file in os.listdir(gold_standard_folder) if file.split("-")[1] in post_war]

    for gold_file in gold_files:
        print(gold_file)
        with open(gold_standard_folder + "/" + gold_file, "r", encoding="utf-8") as f1:
            gold = f1.read()

        with open(test_set_folder + "/" + gold_file, "r", encoding="utf-8") as f2:
            pred = f2.read()

        gold_list = []

        root = etree.fromstring(bytes(gold, encoding="utf-8"))

        # Iterate through all elements in the XML
        # if root.find(".//presidency") is None:
        for element in root.findall(".//speech[@is_president='true']"):
            gold_list.append("president")
            parent = element.getparent()
            parent.remove(element)

        gold = etree.tostring(root, pretty_print=True).decode()

        pred_list = []

        # same for pred
        root_pred = etree.fromstring(bytes(pred, encoding="utf-8"))
        # Iterate through all elements in the XML
        # for elem in root_pred.iter():
        # if root.find(".//presidency") is None:
        for element in root_pred.findall(".//speech[@is_president='true']"):
            pred_list.append("president")
            parent = element.getparent()
            parent.remove(element)

            # # Check if the word_to_delete is in the text content of the element
            # if "PRESIDENTE." in elem.text or "Presidente." in elem.text or "PRESIDENTE" in elem.text:
            #     # If the word is found, remove the element
            #     if elem.getparent() is not None:
            #         parent = elem.getparent()
            #         parent.remove(elem)

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

        gold_list.extend([str(x).split("/")[-1] for x in gold_xml["speaker"]])
        pred_list.extend([str(x).split("/")[-1] for x in pred_xml["speaker"]])

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
    f1 = 2 * (precision * recall) / (precision + recall)

    # print(gold_speakers, pred_speakers)
    # print(true_positives, false_positives, false_negatives)

    if era == "all":
        # save results in a csv
        res_data = pd.DataFrame(
            [[precision, recall, f1]],
            columns=["precision", "recall", "f1"],
        )

        res_data.to_csv(os.path.join(args.metrics_path, "tags_eval.csv"), index=False)

        print(res_data)
        print("total number of tags " + str(true_positives + false_positives + false_negatives))

    if era == "pre":
        # save results in a csv
        res_data = pd.DataFrame(
            [[precision, recall, f1]],
            columns=["precision", "recall", "f1"],
        )

        res_data.to_csv(os.path.join(args.metrics_path, "tags_eval_pre.csv"), index=False)

        print(res_data)
        print("total number of tags PRE " + str(true_positives + false_positives + false_negatives))

    if era == "post":
        # save results in a csv
        res_data = pd.DataFrame(
            [[precision, recall, f1]],
            columns=["precision", "recall", "f1"],
        )

        res_data.to_csv(os.path.join(args.metrics_path, "tags_eval_post.csv"), index=False)

        print(res_data)
        print("total number of tags POST" + str(true_positives + false_positives + false_negatives))

    if era == "all":
        file_name = "tags_eval.png"
    if era == "pre":
        file_name = "tags_eval_pre.png"
    if era == "post":
        file_name = "tags_eval_post.png"

    precision = res_data["precision"].iloc[0]
    recall = res_data["recall"].iloc[0]
    f1 = res_data["f1"].iloc[0]

    labels = ["Precision", "Recall", "F1 Score"]
    values = [precision, recall, f1]

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))

    sns.set_theme(style="ticks", palette="pastel")
    # draw and save barplot for precision, recall and f1
    plot = sns.barplot(x=labels, y=values, color="darkgrey")
    # Adding data labels
    for i, v in enumerate(values):
        plot.text(i, v + 0.02, str(round(v, 3)), ha="center", va="center", fontsize=12)

    # Title and labels
    plot.set_ylabel("Value")

    # Save the plot
    fig.tight_layout()
    plot.figure.savefig(os.path.join(args.metrics_path, file_name), dpi=200)

    # jaccard = round(counter_cosine_similarity(gold_speakers, pred_speakers), 3)

    # cosine_similarities.append(jaccard)
    # print(jaccard)

    # compute cosine similarity between the two counters

    # print(cosine_similarities)
    # print(statistics.mean(cosine_similarities))


def evaluateText(
    gold_standard_folder,
    pred_folder,
    corrected_base_folder,
    corrected_windowed_folder,
    symspell_window_lower_folder,
    era="all",
):
    """
    calculates the WER and CER for the corrected texts, with regards to the golden_standard
    :param golden_standard_path: path to the golden standard
    :param corrected_texts_path: path to the corrected texts
    :return: a dataframe containing results
    """

    if args.create_corrected_sets:
        computeSymspellWindowedDictionariesLower(
            args.uncorrected_set_folder,
            args.symspell_window_lower_folder,
            args.dict_folder,
            2,
        )

        computeSymspellBase(args.uncorrected_set_folder, args.symspell_base_set_folder, args.dict_folder, 2)

        computeSymspellWindowedDictionaries(
            args.uncorrected_set_folder,
            args.symspell_window_set_folder,
            args.dict_folder,
            2,
        )

    gold_files = os.listdir(gold_standard_folder)
    pred_files = os.listdir(pred_folder)
    corrected_base_files = os.listdir(corrected_base_folder)
    corrected_windowed_files = os.listdir(corrected_windowed_folder)
    symspell_window_lower_files = os.listdir(symspell_window_lower_folder)

    if era == "pre":
        gold_files = [file for file in os.listdir(gold_standard_folder) if file.split("-")[1] in pre_war]
        pred_files = [file for file in os.listdir(pred_folder) if file.split("-")[1] in pre_war]
        corrected_base_files = [file for file in os.listdir(corrected_base_folder) if file.split("-")[1] in pre_war]
        corrected_windowed_files = [
            file for file in os.listdir(corrected_windowed_folder) if file.split("-")[1] in pre_war
        ]
        symspell_window_lower_files = [
            file for file in os.listdir(symspell_window_lower_folder) if file.split("-")[1] in pre_war
        ]

    if era == "post":
        gold_files = [file for file in os.listdir(gold_standard_folder) if file.split("-")[1] in post_war]
        pred_files = [file for file in os.listdir(pred_folder) if file.split("-")[1] in post_war]
        corrected_base_files = [file for file in os.listdir(corrected_base_folder) if file.split("-")[1] in post_war]
        corrected_windowed_files = [
            file for file in os.listdir(corrected_windowed_folder) if file.split("-")[1] in post_war
        ]
        symspell_window_lower_files = [
            file for file in os.listdir(symspell_window_lower_folder) if file.split("-")[1] in post_war
        ]

    res = []

    for gold_file in gold_files:
        for file in pred_files:
            if file == gold_file:
                gold_tree = etree.parse(gold_standard_folder + "/" + gold_file)
                gold = etree.tostring(gold_tree.getroot(), encoding="utf-8", method="text").decode("utf-8")
                clean_gold = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", gold).replace("\n", " ").lower().split())

                pred_tree = etree.parse(pred_folder + "/" + file)
                pred = etree.tostring(pred_tree.getroot(), encoding="utf-8", method="text").decode("utf-8")
                clean_pred = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", pred).replace("\n", " ").lower().split())

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Uncorrected"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Uncorrected"])

        for file in corrected_base_files:
            if file == gold_file:
                gold_tree = etree.parse(gold_standard_folder + "/" + gold_file)
                gold = etree.tostring(gold_tree.getroot(), encoding="utf-8", method="text").decode("utf-8")
                clean_gold = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", gold).replace("\n", " ").lower().split())

                with open(corrected_base_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", pred).replace("\n", " ").lower().split())

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Base"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Base"])

        for file in corrected_windowed_files:
            if file == gold_file:
                gold_tree = etree.parse(gold_standard_folder + "/" + gold_file)
                gold = etree.tostring(gold_tree.getroot(), encoding="utf-8", method="text").decode("utf-8")
                clean_gold = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", gold).replace("\n", " ").lower().split())

                with open(corrected_windowed_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", pred).replace("\n", " ").lower().split())

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Windowed"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Windowed"])

        for file in symspell_window_lower_files:
            if file == gold_file:
                gold_tree = etree.parse(gold_standard_folder + "/" + gold_file)
                gold = etree.tostring(gold_tree.getroot(), encoding="utf-8", method="text").decode("utf-8")
                clean_gold = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", gold).replace("\n", " ").lower().split())

                with open(symspell_window_lower_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", pred).replace("\n", " ").lower().split())
                # if jiwer.wer(clean_gold, clean_pred) > 0.2:
                #     print(gold_file)
                #     print(jiwer.wer(clean_gold, clean_pred))

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Windowed Lower Case"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Windowed Lower Case"])

    res_data = pd.DataFrame(res, columns=["val", "cat", "set"])

    print(res_data.groupby(["cat", "set"], as_index=False).mean())

    # save results to csv
    if era == "all":
        res_data.to_csv(os.path.join(args.metrics_path, "symspell_eval.csv"), index=False)

        res_data.groupby(["cat", "set"], as_index=False).mean().to_csv(
            os.path.join(args.metrics_path, "symspell_eval_mean.csv"), index=False
        )
    if era == "pre":
        res_data.to_csv(os.path.join(args.metrics_path, "symspell_eval_pre.csv"), index=False)

        res_data.groupby(["cat", "set"], as_index=False).mean().to_csv(
            os.path.join(args.metrics_path, "symspell_pre_eval_mean.csv"), index=False
        )
    if era == "post":
        res_data.to_csv(os.path.join(args.metrics_path, "symspell_eval_post.csv"), index=False)

        res_data.groupby(["cat", "set"], as_index=False).mean().to_csv(
            os.path.join(args.metrics_path, "symspell_post_eval_mean.csv"), index=False
        )

        # change font to helvetica
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = "Helvetica"

    if era == "all":
        title_wer = "WER for the Symspell-corrected texts (against the golden standard)"
        title_cer = "CER for the Symspell-corrected texts (against the golden standard)"
        file_name = "symspell_eval.png"
    if era == "pre":
        title_wer = "WER for the Symspell-corrected texts (against the golden standard) - pre-war"
        title_cer = "CER for the Symspell-corrected texts (against the golden standard) - pre-war"
        file_name = "symspell_eval_pre.png"
    if era == "post":
        title_wer = "WER for the Symspell-corrected texts (against the golden standard) - post-war"
        title_cer = "CER for the Symspell-corrected texts (against the golden standard) - post-war"
        file_name = "symspell_eval_post.png"

    fig, ax = plt.subplots(nrows=2, figsize=(6, 12))

    sns.set_theme(style="ticks", palette="pastel")

    # Draw a nested boxplot to show bills by day and time
    plot = sns.boxplot(x="set", y="val", color="darkgrey", data=res_data[res_data["cat"] == "WER"], ax=ax[0])
    # sns.despine( trim=True)
    plot.set_title(title_wer)
    plot.set_xlabel("Set")
    plot.set_ylabel("WER")
    # plot.figure.savefig("symspell_wer.png")
    plot1 = sns.boxplot(x="set", y="val", color="darkgrey", data=res_data[res_data["cat"] == "CER"], ax=ax[1])
    # sns.despine( trim=True)
    plot1.set_title(title_cer)
    plot1.set_xlabel("Set")
    plot1.set_ylabel("CER")
    fig.tight_layout()
    plot1.figure.savefig(os.path.join(args.metrics_path, file_name), dpi=200)

    # also save mean results to csv


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
        "--symspell_window_lower_folder",
        type=str,
        default="corrected_windowed_lower",
        help="Folder where to save the windowed Symspell-corrected set.",
        required=False,
    )

    parser.add_argument(
        "--metrics_path",
        type=str,
        default="metrics",
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
        "--split_eval",
        action="store_true",
    )
    parser.add_argument(
        "--create_corrected_sets",
        action="store_true",
    )
    # parser.add_argument(
    #     "--test_set_folder",
    #     type=str,
    #     default="test_set",
    #     help="Folder containing the test set.",
    #     required=False,
    # )
    args = parser.parse_args()

    os.makedirs(args.metrics_path, exist_ok=True)

    if args.split_eval:
        evaluateText(
            args.gold_standard_folder,
            args.uncorrected_set_folder,
            args.symspell_base_set_folder,
            args.symspell_window_set_folder,
            args.symspell_window_lower_folder,
            "pre",
        )
        evaluateText(
            args.gold_standard_folder,
            args.uncorrected_set_folder,
            args.symspell_base_set_folder,
            args.symspell_window_set_folder,
            args.symspell_window_lower_folder,
            "post",
        )
        evaluateTags(args.gold_standard_folder, args.uncorrected_set_folder, "pre")
        evaluateTags(args.gold_standard_folder, args.uncorrected_set_folder, "post")
    else:
        if args.eval_tags_only:
            evaluateTags(args.gold_standard_folder, args.uncorrected_set_folder)
        elif args.eval_text_only:
            evaluateText(
                args.gold_standard_folder,
                args.uncorrected_set_folder,
                args.symspell_base_set_folder,
                args.symspell_window_set_folder,
                args.symspell_window_lower_folder,
            )
        else:
            evaluateTags(args.gold_standard_folder, args.uncorrected_set_folder)
            evaluateText(
                args.gold_standard_folder,
                args.uncorrected_set_folder,
                args.symspell_base_set_folder,
                args.symspell_window_set_folder,
                args.symspell_window_lower_folder,
            )
