import argparse
import os
from utils import Dictionary, ordered_leg_names_short
import re
import pandas as pd
import math


def checkDictionaries(dict_folder, people_folder, output_folder):
    """
    Checks the dictionaries for people names and save their frequency
    :param dict_folder: folder containing the dictionaries
    :param people_folder: folder containing the people dataset
    :param output_folder: folder where to save the modified dictionaries
    """

    os.makedirs(output_folder, exist_ok=True)

    for leg in ordered_leg_names_short:
        # create a pandas table with person and frequency
        present = pd.DataFrame(columns=["surname", "frequency"])
        missing = []

        diction = Dictionary()

        diction.load(os.path.join(dict_folder, leg + ".txt"))

        people = pd.read_csv(os.path.join(people_folder, leg + ".csv"), encoding="utf-8")

        for index, row in people.iterrows():
            name = row["surname"]
            is_present_lower = diction.find(name.lower())
            is_present = diction.find(name)
            if is_present_lower or is_present:
                num_lower = diction.get(name.lower()) if is_present_lower else 0
                num_upper = diction.get(name) if is_present else 0

                person_freq = num_lower + num_upper

                # append does not work
                present = pd.concat(
                    [
                        present,
                        pd.DataFrame(
                            [[name, person_freq]],
                            columns=["surname", "frequency"],
                            index=[index],
                        ),
                    ]
                )
            else:
                missing.append(name)

        people_mean = int(present["frequency"].mean().round())
        for surnmane in missing:
            diction.add_custom(surnmane, people_mean)

        diction.save(os.path.join(output_folder, leg + ".txt"))

        print("Mean frequency for " + leg + ": " + str(people_mean))

        print("Missing names for " + leg + ": " + str(len(missing)))

        print("Example of missing name for " + leg + ": " + missing[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--dict_folder",
        type=str,
        help="Folder containing dictionaries to use for the modification.",
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        help="Folder where to save the modified dictionaries.",
        required=False,
    )
    parser.add_argument(
        "--people_folder",
        type=str,
        help="Folder containing the people dataset.",
        required=False,
    )

    args = parser.parse_args()

    checkDictionaries(args.dict_folder, args.people_folder, args.output_folder)
