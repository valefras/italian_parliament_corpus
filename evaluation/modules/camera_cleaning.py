from Levenshtein import distance as lev
import csv
import pandas as pd
from collections import Counter
import numpy as np


def frequency_count(numbers):
    counter = Counter(numbers)
    return counter.most_common(1)[0][0]


def assessDocType(df, date, page_num):
    """
    tries to assess the type of camera document based on the first 120 words of a page
    :param df: dataframe of the pagefre
    :param date: date of the document
    :param page_num: page number
    :return page type
    """
    sorted_df = df.sort_values("top")[:120]
    words_lst = sorted_df["text"]

    ### I legislatura repubblicana, 3 tipi di documenti: giunta, commissione e assemblea
    if date > 19490508 and date < 19530624:
        for word in words_lst:
            word = str(word)
            if lev(word, "GIUNTA") < 3:
                return 2
            if lev(word, "COMMISSIONE") < 3:
                return 1
        return 0

    ### II, III, IV, V, VI legislature repubblicane, 3 tipi di documenti: commissione, commissione speciale e assemblea
    if date > 19530624 and date < 19760704:
        for word in words_lst:
            word = str(word)
            if lev(word, "SPECIALE") < 3:
                return 2
            if lev(word, "COMMISSIONE") < 3:
                return 1
        return 0

    ### da VII legslatura repubblicana cominciano a esserci anche bollettini per le commissioni oltre ai resoconti stenografici

    ### VII, VIII  legislatura repubblicana
    if date > 19760705 and date < 19830711:
        for word in words_lst:
            word = str(word)
            ### resoconto stenografico commmissione
            if lev(word, "COMMISSIONE") < 3:
                return 2
            ### bollettino commissione
            if lev(word, "Bollettino") < 3:
                return 1
        ### resoconto stenografico assemblea
        return 0

    ### IX legislatura
    if date > 19830712 and date < 19870701:
        for word in words_lst:
            word = str(word)
            ### resoconto stenografico speciale: commissione parlamentare sul fenomeno della mafia
            if page_num == 1 and lev(word, "MAFIA") < 3:
                return 3
            ### resoconto stenografico commmissione
            if lev(word, "COMMISSIONE") < 3:
                return 2
            ### bollettino commissione
            if lev(word, "Bollettino") < 3:
                return 1
        ### resoconto stenografico assemblea
        return 0

    ### X legislatura
    if date > 19870702 and date < 19920422:
        count = 0

        for word in words_lst:
            word = str(word)
            is_found = False

            ### commissione singola o commissioni riuinite bollettino o resoconto stenografico
            if lev(word[:-1], "Commission") < 3:
                for word2 in words_lst[count:]:
                    word2 = str(word2)
                    if lev(word2, "LEGISLATURA") < 3:
                        ### same as COMMISSIONE
                        return 2
                ### normal bollettino
                return 9

            ### comitato paralmamentare bollettino
            if lev(word, "Comitato") < 3:
                return 8

            ### disegni di legge resoconto stenografico
            if lev(word, "DISEGNI") < 3:
                return 7

            ### resoconto stenografico commmissione parlamentare terremoto basilicata/campania
            if lev(word, "BASILICATA") < 3:
                return 6

            ### resoconto stenografico commmissione parlamentare:
            ### condizione giovanile
            ### forme obbligatorie di previdenza sociale
            ### vigilanza servizi radiotelevisivi
            ### riconversione industriale
            ### questioni regionali
            if (
                lev(word, "GIOVANILE") < 3
                or lev(word, "PREVIDENZA") < 3
                or lev(word, "RADIOTELEVISIVI") < 3
                or lev(word, "RICONVERSIONE") < 3
                or lev(word, "REGIONALI") < 3
            ):
                return 5

            ### resoconto stenografico commmissione speciale per le politiche comunitarie
            if lev(word, "COMUNITARIE") < 3:
                return 4

            ### bollettino giunta:
            ### delle elezioni
            ### regolamento
            ### per le autorizzazioni a procedere
            if lev(word, "Giunta") < 3:
                return 3

            ### resoconto stenografico commmissioni
            if lev(word, "COMMISSIONE") < 3:
                return 2

            if lev(word, "RIUNITE") < 3:
                return 1

            count += 1

        ### resoconto stenografico assemblea
        return 0

    ### XI, XII legislature
    if date > 19920423 and date < 19960508:
        for word in words_lst:
            word = str(word)
            ### comitato paralmamentare bollettino
            if lev(word, "Comitato") < 3:
                return 5
            ### commissioni riunite resoconto stenografico
            if lev(word, "RIUNITE") < 3:
                return 4
            ### commissione resoconto stenografico
            if lev(word, "COMMISSIONE") < 3:
                return 3
            ### commissione singola o commissioni riuinite bollettino
            if lev(word[:-1], "Commission") < 3:
                return 2
            ### giunta bollettino
            if lev(word, "Giunta") < 3:
                return 1

        ### resoconto stenografico assemblea
        return 0


def cameraRemoveIntest(df, date, year, leg, document_type, page_num):
    """
    removes intestation from a camera document, based on the date, year, legislature and document type
    :param df: dataframe of the page
    :param date: date of the document
    :param year: year of the document
    :param leg: legislature of the document
    :param document_type: document type of the document
    :param page_num: page number
    :return clean dataframe
    """
    sorted_df = df.sort_values("top")[:80]
    words_lst = sorted_df["text"]

    padding = 50

    ins_cost, del_cost, sub_cost = 1, 1, 1

    ### all other cases (between 1874 and 1992, EXCEPT for assemblea costituente and consulta nazionale)
    # if document_type == 0:
    target_word = "DISCUSSIONI"
    # if document_type == 1:
    #     target_word = "Commissioni"

    ### before 1874 (old intestation format and no bollettini)
    if date < 18741123:
        distances = words_lst.apply(lambda x: min(lev(str(x), "TORNATA"), lev(str(x), "SESSIONE")))
        min_dist = distances.idxmin()

        max_h = sorted_df.loc[min_dist]["top"] + 50

        return df[df["top"] > max_h].reset_index(drop=True)

    ### XXX legislatura del regno
    if date > 19390323 and date < 19430802:
        if page_num == 1:  ### no intestation in first page
            return df

        padding = 80

        target_word = "FASCI"

    ### consulta nazionale
    if date < 19460624 and date > 19450925:
        if page_num == 1:  ### no intestation in first page
            return df

        padding = 80

        if document_type == 0:
            target_word = "ASSEMBLEA"

        if document_type == 1:
            target_word = "COMMISSIONI"

    ### assemblea costituente
    if date < 19480131 and date > 19460625:
        if page_num == 1:  ### no intestation in first page
            return df

        padding = 80

        month_dict = {
            1: "GENNAIO",
            2: "FEBBRAIO",
            3: "MARZO",
            4: "APRILE",
            5: "MAGGIO",
            6: "GIUGNO",
            7: "LUGLIO",
            8: "AGOSTO",
            9: "SETTEMBRE",
            10: "OTTOBRE",
            11: "NOVEMBRE",
            12: "DICEMBRE",
        }

        month_num = int(str(date)[4:6])

        target_word = month_dict[month_num]

    ### I legislatura repubblicana
    if date > 19490508 and date < 19530624:
        padding = 80

        if document_type == 1:
            target_word = "COMMISSIONE"

        if document_type == 2:
            target_word = "GIUNTA"

    ### II, III, IV, V, VI legislature repubblicane, 3 tipi di documenti: commissione, commissione speciale e assemblea
    if date > 19530624 and date < 19760704:
        padding = 80

        if document_type == 1:
            target_word = "COMMISSIONE"

        if document_type == 2:
            target_word = "SPECIALE"

    ### VII, VIII  legislatura repubblicana
    if date > 19760705 and date < 19830711:
        if document_type == 2:
            target_word = "COMMISSIONE"

        if document_type == 1:
            target_word = "Bollettino"

    ### IX legislatura repubblicana
    if date > 19830712 and date < 19870701:
        ### no intestation in first 2 pages for resoconto stenografico (mafia)
        if document_type == 3 and page_num == 1 or page_num == 2:
            return df

        ### mafia resoconto stenografico intestation alternates each page
        if document_type == 3:
            distances = words_lst.apply(lambda x: min(lev(str(x), "SEDUTA"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

        if document_type == 2:
            target_word = "COMMISSIONE"

        if document_type == 1:
            target_word = "Bollettino"

    ### X legislatura
    if date > 19870702 and date < 19920422:
        if (document_type == 6 or document_type == 5) and (page_num == 1 or page_num == 2):
            return df

        if document_type == 9:
            ins_cost = 0
            target_word = "Commission"

        if document_type == 8:
            target_word = "Comitato"

        if document_type == 7:
            target_word = "DISEGNI"

        if document_type == 6:
            distances = words_lst.apply(lambda x: min(lev(str(x), "SEDUTA"), lev(str(x), "TERREMOTI")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

        if document_type == 5:
            distances = words_lst.apply(lambda x: min(lev(str(x), "SEDUTA"), lev(str(x), "COMMISSIONE")))
            min_dist = distances.idxmin()

            max_h = sorted_df.loc[min_dist]["top"] + 50

            return df[df["top"] > max_h].reset_index(drop=True)

        if document_type == 4:
            target_word = "COMUNITARIE"

        if document_type == 3:
            target_word = "Giunta"

        if document_type == 2:
            target_word = "COMMISSIONE"

        if document_type == 1:
            target_word = "RIUNITE"

    ### XI legislatura
    if date > 19920423 and date < 19960508:
        if document_type == 5:
            target_word = "Comitato"

        if document_type == 4:
            target_word = "RIUNITE"

        if document_type == 3:
            target_word = "COMMISSIONE"

        if document_type == 2:
            ins_cost = 0
            target_word = "Commission"

        if document_type == 1:
            target_word = "Giunta"

    distances = words_lst.apply(lambda x: lev(str(x), target_word, weights=(ins_cost, del_cost, sub_cost)))
    min_dist = distances.idxmin()

    max_h = sorted_df.loc[min_dist]["top"] + padding

    return df[df["top"] > max_h].reset_index(drop=True)


def cameraDocType(date, page_num, page_list):
    """
    assesses the document type of a camera document based on the date and the first 3 pages
    :param date: date of the document
    :param page_num: page number
    :param page_list: list of pages
    :return document type
    """
    document_type = None

    # check document type from first 3 pages (necessary only starting from 1943, since all documents were equal before)
    if date > 19430802:
        document_type_list = []
        # check first three pages or less if there are less than 3 pages
        num_pages_check = min(len(page_list), 5)
        for page in np.random.choice(page_list, num_pages_check):
            dataframe = pd.read_csv(page, sep="\t", quoting=csv.QUOTE_NONE, encoding="utf-8")
            # if page is empty skip it
            if dataframe.shape[0] < 3:
                continue

            ########### special cases ################

            ### special format for mafia resoconti stenografici of IX legislatura
            if date > 19830712 and date < 19870701 and 3 in document_type_list:
                continue

            ### special formats for X legislatura
            if date > 19870702 and date < 19920422 and (5 in document_type_list or 6 in document_type_list):
                continue

            ##########################################

            document_type_list.append(assessDocType(dataframe, date, page_num))

        # document type is the most frequent one in first three pages
        if len(document_type_list) > 0:
            return frequency_count(document_type_list)
        return None
