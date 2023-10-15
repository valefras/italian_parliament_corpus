import os

doc_num = 0
senato = 0
camera = 0

for cam in os.listdir("../../tagged_italian_parliament_corpus"):
    for leg in os.listdir(f"../../tagged_italian_parliament_corpus/{cam}"):
        if cam == "senato":
            senato += len(os.listdir(f"../../tagged_italian_parliament_corpus/{cam}/{leg}"))
        else:
            camera += len(os.listdir(f"../../tagged_italian_parliament_corpus/{cam}/{leg}"))
        doc_num += len(os.listdir(f"../../tagged_italian_parliament_corpus/{cam}/{leg}"))

print(doc_num, camera, senato)
# import pandas as pd

# stats = pd.read_csv("stats.csv", encoding="utf-8")

# total_tokens = stats["token_num"].sum()
# total_speeches = stats["speech_num"].sum()
# total_pages = stats["page_num"].sum()

# print(total_tokens, total_speeches, total_pages)