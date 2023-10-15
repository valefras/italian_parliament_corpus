import pandas as pd
import os
import xml.etree.ElementTree as ET
import re

stats = pd.DataFrame(columns=["legislature", "token_num", "speech_num"])

data_path = "../../tagged_italian_parliament_corpus"


def count_words(text):
    words = re.findall(r"\b\w+\b", text)
    return len(words)


for cam in os.listdir(data_path):
    for leg in os.listdir(os.path.join(data_path, cam)):
        for doc in os.listdir(os.path.join(data_path, cam, leg)):
            if doc.endswith(".xml"):
                print(doc)
                try:
                    xml_file_path = os.path.join(data_path, cam, leg, doc)
                    # Parse the XML document
                    tree = ET.parse(xml_file_path, parser=ET.XMLParser(encoding="utf-8"))
                    root = tree.getroot()
                    # count the number of words

                    # Extract text content and count words
                    text_content = "".join(element.text for element in root.iter() if element.text)
                    word_count = count_words(text_content)

                    speech_count = len(root.findall(".//speech"))

                    # Append the result to the DataFrame
                    if leg not in stats["legislature"].values:
                        stats = pd.concat(
                            [
                                stats,
                                pd.DataFrame(
                                    [[leg, word_count, speech_count]],
                                    columns=["legislature", "token_num", "speech_num"],
                                ),
                            ]
                        )
                        # append(
                        #     {"legislature": leg, "token_num": word_count, "speech_num": speech_count}, ignore_index=True
                        # )
                    else:
                        stats.loc[stats["legislature"] == leg, "speech_num"] += speech_count
                        stats.loc[stats["legislature"] == leg, "token_num"] += word_count

                except Exception as e:
                    print(f"Error processing {xml_file_path}: {e}")

stats.to_csv("stats_def.csv", index=False)
