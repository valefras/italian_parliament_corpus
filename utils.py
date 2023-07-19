class Dictionary:
    def __init__(self):
        self.data = {}

    def add(self, word):
        if word not in self.data:
            self.data[word] = 1
        else:
            self.data[word] += 1

    def addMany(self, words):
        for word in words:
            self.add(word)

    def save(self, path):
        # save in txt as <word> <frequency>
        with open(path, "w", encoding="utf-8") as f:
            for word in self.data:
                f.write(word + " " + str(self.data[word]) + "\n")

    def freq_cutoff(self, threshold):
        # remove words with frequency < threshold
        self.data = {k: v for k, v in self.data.items() if v >= threshold}

    def keep_top_n(self, n):
        # keep top n words by frequency (return less if there are less than n words)
        if n > len(self.data):
            return

        self.data = dict(
            sorted(self.data.items(), key=lambda item: item[1], reverse=True)[:n]
        )

    def sort(self):
        # sort dictionary by frequency
        self.data = dict(
            sorted(self.data.items(), key=lambda item: item[1], reverse=True)
        )

    def load(self, path):
        # load from txt
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                word, freq = line.strip().split(" ")
                self.data[word] = int(freq)

    def merge(self, other):
        # merge two dictionaries
        for word in other.data:
            if word not in self.data:
                self.data[word] = other.data[word]
            else:
                self.data[word] += other.data[word]


    def __len__(self):
        return len(self.data)

    def __str__(self):
        return str(self.data)


ordered_legs = [
    ("regno_01", "regno_1"),
    ("regno_02", "regno_2"),
    ("regno_03", "regno_3"),
    ("regno_04", "regno_4"),
    ("regno_05", "regno_5"),
    ("regno_06", "regno_6"),
    ("regno_07", "regno_7"),
    ("regno_08", "regno_8"),
    ("regno_09", "regno_9"),
    ("regno_10", "regno_10"),
    ("regno_11", "regno_11"),
    ("regno_12", "regno_12"),
    ("regno_13", "regno_13"),
    ("regno_14", "regno_14"),
    ("regno_15", "regno_15"),
    ("regno_16", "regno_16"),
    ("regno_17", "regno_17"),
    ("regno_18", "regno_18"),
    ("regno_19", "regno_19"),
    ("regno_20", "regno_20"),
    ("regno_21", "regno_21"),
    ("regno_22", "regno_22"),
    ("regno_23", "regno_23"),
    ("regno_24", "regno_24"),
    ("regno_25", "regno_25"),
    ("regno_26", "regno_26"),
    ("regno_27", "regno_27"),
    ("regno_28", "regno_28"),
    ("regno_29", "regno_29"),
    ("regno_30", "regno_30"),
    ("consulta_nazionale", None),
    ("costituente", None),
    ("repubblica_01", "l_1", "cg_1", "1"),
    ("repubblica_02", "l_2", "cg_2", "2"),
    ("repubblica_03", "l_3", "cg_3", "3"),
    ("repubblica_04", "l_4", "cg_4", "4"),
    ("repubblica_05", "l_5", "cg_5", "5"),
    ("repubblica_06", "l_6", "cg_6", "6"),
    ("repubblica_07", "l_7", "cg_7", "7"),
    ("repubblica_08", "l_8", "cg_8", "8"),
    ("repubblica_09", "l_9", "cg_9", "9"),
    ("repubblica_10", "l_10", "cg_10", "10"),
    ("repubblica_11", "l_11", "cg_11", "11"),
    ("repubblica_12", "l_12", "cg_12", "12"),
]

ordered_leg_names = [
    "regno_01",
    "regno_02",
    "regno_03",
    "regno_04",
    "regno_05",
    "regno_06",
    "regno_07",
    "regno_08",
    "regno_09",
    "regno_10",
    "regno_11",
    "regno_12",
    "regno_13",
    "regno_14",
    "regno_15",
    "regno_16",
    "regno_17",
    "regno_18",
    "regno_19",
    "regno_20",
    "regno_21",
    "regno_22",
    "regno_23",
    "regno_24",
    "regno_25",
    "regno_26",
    "regno_27",
    "regno_28",
    "regno_29",
    "regno_30",
    "consulta_nazionale",
    "costituente",
    "repubblica_01",
    "repubblica_02",
    "repubblica_03",
    "repubblica_04",
    "repubblica_05",
    "repubblica_06",
    "repubblica_07",
    "repubblica_08",
    "repubblica_09",
    "repubblica_10",
    "repubblica_11",
    "repubblica_12",
]

leg_mapping = {
    "regno_1": "regno_01",
    "regno_2": "regno_02",
    "regno_3": "regno_03",
    "regno_4": "regno_04",
    "regno_5": "regno_05",
    "regno_6": "regno_06",
    "regno_7": "regno_07",
    "regno_8": "regno_08",
    "regno_9": "regno_09",
    "l_1": "repubblica_01",
    "cg_1": "repubblica_01",
    "1": "repubblica_01",
    "l_2": "repubblica_02",
    "cg_2": "repubblica_02",
    "2": "repubblica_02",
    "l_3": "repubblica_03",
    "cg_3": "repubblica_03",
    "3": "repubblica_03",
    "l_4": "repubblica_04",
    "cg_4": "repubblica_04",
    "4": "repubblica_04",
    "l_5": "repubblica_05",
    "cg_5": "repubblica_05",
    "5": "repubblica_05",
    "l_6": "repubblica_06",
    "cg_6": "repubblica_06",
    "6": "repubblica_06",
    "l_7": "repubblica_07",
    "cg_7": "repubblica_07",
    "7": "repubblica_07",
    "l_8": "repubblica_08",
    "cg_8": "repubblica_08",
    "8": "repubblica_08",
    "l_9": "repubblica_09",
    "cg_9": "repubblica_09",
    "9": "repubblica_09",
    "l_10": "repubblica_10",
    "cg_10": "repubblica_10",
    "10": "repubblica_10",
    "l_11": "repubblica_11",
    "cg_11": "repubblica_11",
    "11": "repubblica_11",
    "l_12": "repubblica_12",
    "cg_12": "repubblica_12",
    "12": "repubblica_12",
}
