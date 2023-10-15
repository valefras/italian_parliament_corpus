from symspellpy.symspellpy import SymSpell
import os
from utils import Dictionary, ordered_leg_names, leg_mapping
import argparse
import string
import math
import re
import tqdm

string.punctuation += "«»–"
string.punctuation


def correctDoc(doc_path, output_path, dictionary, max_edit_distance):
    """
    Corrects a single document using the given dictionary
    :param doc_path: path to the document to correct
    :param output_path: path to the output file
    :param dictionary: dictionary to use for correction
    :param max_edit_distance: max edit distance for correction
    """
    sym_spell = SymSpell(max_dictionary_edit_distance=max_edit_distance)

    sym_spell.load_dictionary(
        dictionary,
        term_index=0,
        count_index=1,
        separator=" ",
        encoding="utf-8",
    )

    with open(doc_path, "r", encoding="utf-8") as f1:
        lines = f1.readlines()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(output_path)

    with open(output_path, "w", encoding="utf-8") as f2:
        for line in lines:
            suggestions = sym_spell.lookup_compound(
                line,
                max_edit_distance=max_edit_distance,
                transfer_casing=True,
            )
            corrected_line = ""
            for suggestion in suggestions:
                corrected_line += suggestion.term + " "
            f2.write(corrected_line + "\n")


def correctLeg(leg, max_edit_distance, dict_folder, input_folder, output_folder):
    """
    Corrects all documents in a leg using the merged dictionaries
    :param leg: leg to correct
    :param max_edit_distance: max edit distance for correction
    :param dict_folder: folder containing the merged dictionaries
    :param output_folder: folder where to save the corrected documents
    """
    global ordered_leg_names
    global leg_mapping

    os.makedirs(os.path.dirname(output_folder), exist_ok=True)

    dict_leg = leg_mapping[leg] if leg in leg_mapping else leg

    # correct documents
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith(".txt"):
                doc_path = os.path.join(root, file)
                output_path = os.path.join(output_folder, file[:-4] + "_corrected.txt")
                correctDoc(
                    doc_path,
                    output_path,
                    os.path.abspath(os.path.join(dict_folder, dict_leg + ".txt")),
                    max_edit_distance,
                )


def correct(
    data_path,
    output_folder,
    dict_folder,
):
    """
    Corrects all documents in data_path using the merged dictionaries
    :param data_path: path to the data to process
    :param output_path: where to output corrected documents
    :param dict_folder: folder containing the merged dictionaries
    """
    os.makedirs(os.path.dirname(output_folder), exist_ok=True)

    for cam in os.listdir(data_path):
        for leg in os.listdir(os.path.join(data_path, cam)):
            correctLeg(
                leg,
                2,
                dict_folder,
                os.path.join(data_path, cam, leg),
                os.path.join(output_folder, cam, leg),
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--data_path", type=str, default="data/", help="Path to the data to process.")
    parser.add_argument(
        "--output_path",
        type=str,
        default="data/",
        help="Where to output corrected documents.",
    )
    parser.add_argument(
        "--dict_folder",
        type=str,
        default="window_dictionaries",
        help="Folder containing dictionaries.",
        required=False,
    )

    args = parser.parse_args()

    # method with which to cut the dictionary (0 = keep top n, 1 = keep words with frequency > freq_cutoff)

    correct(
        args.data_path,
        args.output_path,
        args.dict_folder,
    )
