import os


os.chdir("C:/Users/Valentino/Desktop/Tirocinio_2023/Italian_Parliament_Symspell/evaluation")

complete_path = os.getcwd()


print(complete_path)

for file in os.listdir("gold_standard_ocr"):
    if ".txt" in file:
        name_old = os.path.join("gold_standard_ocr", file)
        name_new = os.path.join("gold_standard_ocr", file.replace(".txt", ""))
        os.rename(name_old, name_new)
