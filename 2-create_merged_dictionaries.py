from utils import Dictionary, ordered_leg_names
import math
import os
import argparse


def createMergedDictionaries(
    span, cutoff_method, cutoff_value, dict_folder, output_folder
):
    """
    Merges span dictionaries into one in a window surrounding the leg (inclusive)
    :param leg: leg to create the merged dictionary for
    :param span: span of legislatures to merge around leg
    :param cutoff_method: method with which to cut the dictionary (0 = keep top n, 1 = keep words with frequency > freq_cutoff)
    :param cutoff_value: value to use for the cutoff
    :param dict_folder: folder containing the single dictionaries to merge
    :param output_folder: folder where to save the merged dictionary
    """

    global ordered_leg_names

    os.makedirs(os.path.dirname(output_folder), exist_ok=True)

    # create merged dictionaries
    for leg in ordered_leg_names:
        # get index of leg in ordered_leg_names
        idx = ordered_leg_names.index(leg)

        # get the surrounding legs
        surrounding_legs = ordered_leg_names[
            max(0, idx - math.floor(span / 2)) : min(
                len(ordered_leg_names), idx + math.floor(span / 2) + 1
            )
        ]
        print(surrounding_legs)

        # create a dictionary for each leg
        leg_dicts = []
        for sub_leg in surrounding_legs:
            leg_dict = Dictionary()
            leg_dict.load(os.path.join(dict_folder, sub_leg + ".txt"))
            leg_dicts.append(leg_dict)

        # merge dictionaries
        merged_dict = Dictionary()
        for leg_dict in leg_dicts:
            merged_dict.merge(leg_dict)

        merged_dict.sort()

        # cut dictionary
        if cutoff_method == 0:
            merged_dict.keep_top_n(cutoff_value)
        else:
            merged_dict.freq_cutoff(cutoff_value)

        print(os.path.join(output_folder, leg + ".txt"))

        merged_dict.save(os.path.join(output_folder, leg + ".txt"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--span",
        type=int,
        default=5,
        help="Span of legislatures dictionaries to merge.",
        required=False,
    )
    parser.add_argument(
        "--dict_folder",
        type=str,
        help="Folder containing the single dictionaries to merge.",
    )
    parser.add_argument(
        "--dict_output_folder",
        type=str,
        default="window_dictionaries",
        help="Folder where to save the merged dictionaries.",
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

    createMergedDictionaries(
        args.span,
        cut_method,
        cut_value,
        args.dict_folder,
        args.dict_output_folder,
    )
