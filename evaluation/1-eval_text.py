import jiwer
from symspellpy.symspellpy import SymSpell
import string
from utils import leg_mapping, pre_war, post_war, ordered_leg_names_short
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

leg_mapping_fancy = {
    "regno_01": "Kingdom I",
    "regno_02": "Kingdom II",
    "regno_03": "Kingdom III",
    "regno_04": "Kingdom IV",
    "regno_05": "Kingdom V",
    "regno_06": "Kingdom VI",
    "regno_07": "Kingdom VII",
    "regno_08": "Kingdom VIII",
    "regno_09": "Kingdom IX",
    "regno_10": "Kingdom X",
    "regno_11": "Kingdom XI",
    "regno_12": "Kingdom XII",
    "regno_13": "Kingdom XIII",
    "regno_14": "Kingdom XIV",
    "regno_15": "Kingdom XV",
    "regno_16": "Kingdom XVI",
    "regno_17": "Kingdom XVII",
    "regno_18": "Kingdom XVIII",
    "regno_19": "Kingdom XIX",
    "regno_20": "Kingdom XX",
    "regno_21": "Kingdom XXI",
    "regno_22": "Kingdom XXII",
    "regno_23": "Kingdom XXIII",
    "regno_24": "Kingdom XXIV",
    "regno_25": "Kingdom XXV",
    "regno_26": "Kingdom XXVI",
    "regno_27": "Kingdom XXVII",
    "regno_28": "Kingdom XXVIII",
    "regno_29": "Kingdom XXIX",
    "regno_30": "Kingdom XXX",
    "consulta_nazionale": "Consulta Nazionale",
    "assemblea_costituente": "Assemblea Costituente",
    "repubblica_01": "Republic I",
    "repubblica_02": "Republic II",
    "repubblica_03": "Republic III",
    "repubblica_04": "Republic IV",
    "repubblica_05": "Republic V",
    "repubblica_06": "Republic VI",
    "repubblica_07": "Republic VII",
    "repubblica_08": "Republic VIII",
    "repubblica_09": "Republic IX",
    "repubblica_10": "Republic X",
    "repubblica_11": "Republic XI",
    "repubblica_12": "Republic XII",
}


leg_mapping_compact = {
    "regno_01": "K I",
    "regno_02": "K II",
    "regno_03": "K III",
    "regno_04": "K IV",
    "regno_05": "K V",
    "regno_06": "K VI",
    "regno_07": "K VII",
    "regno_08": "K VIII",
    "regno_09": "K IX",
    "regno_10": "K X",
    "regno_11": "K XI",
    "regno_12": "K XII",
    "regno_13": "K XIII",
    "regno_14": "K XIV",
    "regno_15": "K XV",
    "regno_16": "K XVI",
    "regno_17": "K XVII",
    "regno_18": "K XVIII",
    "regno_19": "K XIX",
    "regno_20": "K XX",
    "regno_21": "K XXI",
    "regno_22": "K XXII",
    "regno_23": "K XXIII",
    "regno_24": "K XXIV",
    "regno_25": "K XXV",
    "regno_26": "K XXVI",
    "regno_27": "K XXVII",
    "regno_28": "K XXVIII",
    "regno_29": "K XXIX",
    "regno_30": "K XXX",
    "consulta_nazionale": "CN",
    "assemblea_costituente": "AC",
    "repubblica_01": "R I",
    "repubblica_02": "R II",
    "repubblica_03": "R III",
    "repubblica_04": "R IV",
    "repubblica_05": "R V",
    "repubblica_06": "R VI",
    "repubblica_07": "R VII",
    "repubblica_08": "R VIII",
    "repubblica_09": "R IX",
    "repubblica_10": "R X",
    "repubblica_11": "R XI",
    "repubblica_12": "R XII",
}

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

                leg = file.split("-")[1]
                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Uncorrected", leg])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Uncorrected", leg])

        for file in corrected_base_files:
            if file == gold_file:
                with open(gold_standard_folder + "/" + file, "r", encoding="utf-8") as f2:
                    gold = f2.read()
                clean_gold = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", gold).replace("\n", " ").lower().split()[1:-1])

                with open(corrected_base_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", pred).replace("\n", " ").lower().split()[1:-1])

                leg = file.split("-")[1]
                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Base", leg])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Base", leg])

        for file in corrected_windowed_files:
            if file == gold_file:
                with open(gold_standard_folder + "/" + file, "r", encoding="utf-8") as f2:
                    gold = f2.read()
                clean_gold = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", gold).replace("\n", " ").lower().split()[1:-1])

                with open(corrected_windowed_folder + "/" + file, "r", encoding="utf-8") as f2:
                    pred = f2.read()
                    clean_pred = " ".join(re.sub(r"[^a-zA-ZÀ-ÿ\s]", "", pred).replace("\n", " ").lower().split()[1:-1])

                leg = file.split("-")[1]

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Windowed", leg])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Windowed", leg])

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

                leg = file.split("-")[1]

                res.append([jiwer.wer(clean_gold, clean_pred), "WER", "Windowed Lower Case", leg])
                res.append([jiwer.cer(clean_gold, clean_pred), "CER", "Windowed Lower Case", leg])

    res_data = pd.DataFrame(res, columns=["val", "cat", "set", "leg"])
    # plot trend of WER and CER over intervals of 5 legislatures using ordered_leg_names_short
    # values_interv = []
    sns.set_theme(style="ticks", palette="tab10")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = "Helvetica"

    if not args.split_eval:
        string_interval_mapping = {}
        for i in range(0, len(ordered_leg_names_short), 5):
            start = ordered_leg_names_short[i]
            end = ordered_leg_names_short[min(i + 4, len(ordered_leg_names_short) - 1)]
            interval = f"{leg_mapping_compact[start]} - {leg_mapping_compact[end]}"
            for string in ordered_leg_names_short[i : i + 5]:
                string_interval_mapping[string] = interval

        # Add a new column to the DataFrame with the corresponding intervals
        res_data["int"] = res_data["leg"].map(string_interval_mapping)

        # Group by 'Interval' and calculate the mean of 'Values'
        mean_values = res_data.groupby(["int", "cat"])["val"].mean().reset_index()

        mean_values = mean_values.reindex([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0, 1, 14, 15, 16, 17])

        # plot line chart of wer and cer over intervals
        plt.figure(figsize=(5, 4))
        # ValueError: Multi-dimensional indexing (e.g. `obj[:, None]`) is no longer supported. Convert to a numpy array before indexing instead.
        sns.lineplot(data=mean_values, x="int", y="val", hue="cat", linewidth=2)

        plt.xticks(rotation=45, ha="right")
        plt.legend(title="Metric")
        plt.ylabel("")
        plt.xlabel("")
        # plt.title("WER and CER over Legislative Periods")
        plt.tight_layout()
        plt.savefig(os.path.join(args.metrics_folder, "symspell_eval_intervals.png"), dpi=200)
        # values_interv.append(res_data[(res_data["leg"] >= ordered_leg_names_short[i]) & (res_data["leg"] <= ordered_leg_names_short[i+4])].mean())

        # for leg in

        # remove leg column
        print(mean_values)

        res_data = res_data.drop(columns=["int"])

    res_data = res_data.drop(columns=["leg"])

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

    if era == "all":
        title_wer = "WER for the Symspell-corrected texts (against the golden standard)"
        title_cer = "CER for the Symspell-corrected texts (against the golden standard)"
        file_name = "symspell_eval.png"
    if era == "pre":
        title_wer = "WER for the Symspell-corrected texts pre-WWII"
        title_cer = "CER for the Symspell-corrected texts pre-WWII"
        file_name = "symspell_eval_pre.png"
    if era == "post":
        title_wer = "WER for the Symspell-corrected texts post-WWII"
        title_cer = "CER for the Symspell-corrected texts post-WWII"
        file_name = "symspell_eval_post.png"

    fig, ax = plt.subplots(nrows=2, figsize=(7, 14))

    sns.set_theme(style="ticks", palette="pastel")

    # Draw a nested boxplot to show bills by day and time
    plot = sns.boxplot(
        x="set",
        y="val",
        color="darkgrey",
        data=res_data[res_data["cat"] == "WER"],
        ax=ax[0],
        flierprops={
            "marker": "D",
            "markerfacecolor": "darkgrey",
            "markeredgecolor": "black",
            "markersize": 5,
            "markeredgewidth": 0.5,
        },
    )
    # sns.despine( trim=True)
    if era != "all":
        plot.set_ylim(0, 0.35)

    plot.set_title(title_wer)
    plot.set_xlabel("Set")
    plot.set_ylabel("WER")
    # plot.figure.savefig("symspell_wer.png")
    plot1 = sns.boxplot(
        x="set",
        y="val",
        color="darkgrey",
        data=res_data[res_data["cat"] == "CER"],
        ax=ax[1],
        flierprops={
            "marker": "D",
            "markerfacecolor": "darkgrey",
            "markeredgecolor": "black",
            "markersize": 5,
            "markeredgewidth": 0.5,
        },
    )
    # sns.despine( trim=True)
    if era != "all":
        plot1.set_ylim(0, 0.175)
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
