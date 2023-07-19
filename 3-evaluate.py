import jiwer
from symspellpy.symspellpy import SymSpell
import string
from utils import leg_mapping
import pandas as pd
import argparse
import os
import seaborn as sns

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


def evaluate(
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

    computeSymspellBase(args.preprocessed_set_folder, args.symspell_base_set_folder, args.dict_folder, 2)

    computeSymspellWindowedDictionaries(
        args.preprocessed_set_folder,
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

    res_data = pd.DataFrame(res, columns=["val", "cat", "set"])

    print(res_data.groupby(["cat", "set"], as_index=False).mean())

    sns.set_theme(style="ticks", palette="pastel")

    # Draw a nested boxplot to show bills by day and time
    plot = sns.boxplot(x="set", y="val", hue="cat", palette=["m", "g"], data=res_data)
    sns.despine(offset=10, trim=True)
    plot.set_title("WER and CER for the Symspell-corrected texts (against the golden standard)")
    plot.set_xlabel("Set")
    plot.set_ylabel("WER/CER")
    plot.figure.savefig("symspell.png")

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
        "--preprocessed_set_folder",
        type=str,
        default="preprocessed_set",
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
    args = parser.parse_args()

    evaluate(
        args.gold_standard_folder,
        args.preprocessed_set_folder,
        args.symspell_base_set_folder,
        args.symspell_window_set_folder,
    )
