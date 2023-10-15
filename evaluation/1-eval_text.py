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
        # tree = etree.parse(test_set_path + "/" + file)
        # lines = etree.tostring(tree.getroot(), encoding="utf-8", method="text").decode("utf-8").split("\n")
        with open(test_set_path + "/" + file, "r", encoding="utf-8") as f1:
            lines = f1.readlines()

        os.makedirs(os.path.dirname(output_path + "/" + file), exist_ok=True)

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
        # tree = etree.parse(test_set_path + "/" + file)
        # lines = etree.tostring(tree.getroot(), encoding="utf-8", method="text").decode("utf-8").split("\n")
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
        with open(test_set_path + "/" + file, "r", encoding="utf-8") as f:
            lines = f.readlines()

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
                with open(gold_standard_folder + "/" + file, "r", encoding="utf-8") as f2:
                    gold = f2.read()
                # exclude first and last word
                clean_gold = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", gold).replace("\n", " ").lower().split()[1:-1])

                with open(pred_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                clean_pred = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", pred).replace("\n", " ").lower().split()[1:-1])

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Uncorrected"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Uncorrected"])

        for file in corrected_base_files:
            if file == gold_file:
                with open(gold_standard_folder + "/" + file, "r", encoding="utf-8") as f2:
                    gold = f2.read()
                clean_gold = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", gold).replace("\n", " ").lower().split()[1:-1])

                with open(corrected_base_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", pred).replace("\n", " ").lower().split()[1:-1])

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Base"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Base"])

        for file in corrected_windowed_files:
            if file == gold_file:
                with open(gold_standard_folder + "/" + file, "r", encoding="utf-8") as f2:
                    gold = f2.read()
                clean_gold = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", gold).replace("\n", " ").lower().split()[1:-1])

                with open(corrected_windowed_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", pred).replace("\n", " ").lower().split()[1:-1])

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Windowed"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Windowed"])

        for file in symspell_window_lower_files:
            if file == gold_file:
                with open(gold_standard_folder + "/" + file, "r", encoding="utf-8") as f2:
                    gold = f2.read()
                clean_gold = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", gold).replace("\n", " ").lower().split()[1:-1])

                with open(symspell_window_lower_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", pred).replace("\n", " ").lower().split()[1:-1])
                if jiwer.wer(clean_gold, clean_pred) > 0.2:
                    print(gold_file)
                    print(jiwer.wer(clean_gold, clean_pred))

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Windowed Lower Case"])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Windowed Lower Case"])

    res_data = pd.DataFrame(res, columns=["val", "cat", "set"])

    print(res_data.groupby(["cat", "set"], as_index=False).mean())

    # save results to csv
    if era == "all":
        res_data.to_csv(os.path.join(args.metrics_folder, "symspell_eval.csv"), index=False)

        res_data.groupby(["cat", "set"], as_index=False).mean().to_csv(
            os.path.join(args.metrics_folder, "symspell_eval_mean.csv"), index=False
        )
    if era == "pre":
        res_data.to_csv(os.path.join(args.metrics_folder, "symspell_eval_pre.csv"), index=False)

        res_data.groupby(["cat", "set"], as_index=False).mean().to_csv(
            os.path.join(args.metrics_folder, "symspell_pre_eval_mean.csv"), index=False
        )
    if era == "post":
        res_data.to_csv(os.path.join(args.metrics_folder, "symspell_eval_post.csv"), index=False)

        res_data.groupby(["cat", "set"], as_index=False).mean().to_csv(
            os.path.join(args.metrics_folder, "symspell_post_eval_mean.csv"), index=False
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
    plot1.figure.savefig(os.path.join(args.metrics_folder, file_name), dpi=200)

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
        "--split_eval",
        action="store_true",
    )
    parser.add_argument(
        "--create_corrected_sets",
        action="store_true",
    )
    parser.add_argument(
        "--metrics_folder",
        type=str,
        default="metrics",
    )
    args = parser.parse_args()

    os.makedirs(args.metrics_folder, exist_ok=True)

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


    if not args.split_eval:
        evaluateText(
            args.gold_standard_folder,
            args.uncorrected_set_folder,
            args.symspell_base_set_folder,
            args.symspell_window_set_folder,
            args.symspell_window_lower_folder,
            "all",
        )

    else:
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
