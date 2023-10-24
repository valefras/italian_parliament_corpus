import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from lxml import etree
from utils import ordered_leg_names_short, pre_war, post_war

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

    metrics = []

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

        metrics.append(
            [
                temp_true_positives / (temp_true_positives + temp_false_positives),
                "precision",
                gold_file.split("-")[1],
            ]
        )
        metrics.append(
            [
                temp_true_positives / (temp_true_positives + temp_false_negatives),
                "recall",
                gold_file.split("-")[1],
            ]
        )
        metrics.append(
            [
                2
                * (temp_true_positives / (temp_true_positives + temp_false_positives))
                * (temp_true_positives / (temp_true_positives + temp_false_negatives))
                / (
                    (temp_true_positives / (temp_true_positives + temp_false_positives))
                    + (temp_true_positives / (temp_true_positives + temp_false_negatives))
                ),
                "f1",
                gold_file.split("-")[1],
            ]
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

        res_data.to_csv(os.path.join(args.metrics_folder, "tags_eval.csv"), index=False)

        metrics_complete = pd.DataFrame(metrics, columns=["val", "cat", "leg"])
        sns.set_theme(style="ticks", palette="tab10")
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = "Helvetica"

        string_interval_mapping = {}
        for i in range(0, len(ordered_leg_names_short), 5):
            start = ordered_leg_names_short[i]
            end = ordered_leg_names_short[min(i + 4, len(ordered_leg_names_short) - 1)]
            interval = f"{leg_mapping_compact[start]} - {leg_mapping_compact[end]}"
            for string in ordered_leg_names_short[i : i + 5]:
                string_interval_mapping[string] = interval

        # Add a new column to the DataFrame with the corresponding intervals
        metrics_complete["int"] = metrics_complete["leg"].map(string_interval_mapping)

        # Group by 'Interval' and calculate the mean of 'Values'
        mean_values = metrics_complete.groupby(["int", "cat"])["val"].mean().reset_index()

        mean_values = mean_values.reindex(
            [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0, 1, 14, 15, 16, 17, 18, 19, 20, 1, 2, 3, 21, 22, 23, 24, 25, 26]
        )

        # plot line chart of wer and cer over intervals
        plt.figure(figsize=(5, 4))
        # ValueError: Multi-dimensional indexing (e.g. `obj[:, None]`) is no longer supported. Convert to a numpy array before indexing instead.
        sns.lineplot(data=mean_values, x="int", y="val", hue="cat", linewidth=2)

        plt.xticks(rotation=45, ha="right")
        plt.legend(title="Metrics")
        plt.ylabel("")
        plt.xlabel("")
        # plt.title("WER and CER over Legislative Periods")
        plt.tight_layout()
        plt.savefig(os.path.join(args.metrics_folder, "tags_eval_intervals.png"), dpi=200)
        # empty plot
        plt.clf()
        # plot line chart of wer and cer over intervals
        plt.figure(figsize=(5, 4))
        # ValueError: Multi-dimensional indexing (e.g. `obj[:, None]`) is no longer supported. Convert to a numpy array before indexing instead.
        mean_values = mean_values[mean_values["cat"] == "f1"]
        sns.lineplot(data=mean_values, x="int", y="val", hue="cat", linewidth=2)

        plt.xticks(rotation=45, ha="right")
        plt.legend(title="Metrics")
        plt.ylabel("")
        plt.xlabel("")
        # plt.title("WER and CER over Legislative Periods")
        plt.tight_layout()
        plt.savefig(os.path.join(args.metrics_folder, "tags_eval_intervals_f1_only.png"), dpi=200)

        # values_interv.append(res_data[(res_data["leg"] >= ordered_leg_names_short[i]) & (res_data["leg"] <= ordered_leg_names_short[i+4])].mean())

        # for leg in

        # remove leg column
        print(mean_values)

        print(res_data)
        print("total number of tags " + str(true_positives + false_positives + false_negatives))

    if era == "pre":
        # save results in a csv
        res_data = pd.DataFrame(
            [[precision, recall, f1]],
            columns=["precision", "recall", "f1"],
        )

        res_data.to_csv(os.path.join(args.metrics_folder, "tags_eval_pre.csv"), index=False)

        print(res_data)
        print("total number of tags PRE " + str(true_positives + false_positives + false_negatives))

    if era == "post":
        # save results in a csv
        res_data = pd.DataFrame(
            [[precision, recall, f1]],
            columns=["precision", "recall", "f1"],
        )

        res_data.to_csv(os.path.join(args.metrics_folder, "tags_eval_post.csv"), index=False)

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
    plot.figure.savefig(os.path.join(args.metrics_folder, file_name), dpi=200)

    # jaccard = round(counter_cosine_similarity(gold_speakers, pred_speakers), 3)

    # cosine_similarities.append(jaccard)
    # print(jaccard)

    # compute cosine similarity between the two counters

    # print(cosine_similarities)
    # print(statistics.mean(cosine_similarities))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "--gold_standard_folder",
        type=str,
        default="gold_standard",
        help="Folder containing the golden standard.",
        required=False,
    )

    parser.add_argument(
        "--tagged_set_folder",
        type=str,
        default="uncorrected_set",
        help="Folder containing the uncorrected set.",
        required=False,
    )

    parser.add_argument(
        "--metrics_folder",
        type=str,
        default="metrics",
        help="Folder where to save the windowed Symspell-corrected set.",
        required=False,
    )

    parser.add_argument(
        "--split_eval",
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

    os.makedirs(args.metrics_folder, exist_ok=True)

    if args.split_eval:
        evaluateTags(args.gold_standard_folder, args.tagged_set_folder, "pre")
        evaluateTags(args.gold_standard_folder, args.tagged_set_folder, "post")

    else:
        evaluateTags(args.gold_standard_folder, args.tagged_set_folder)
