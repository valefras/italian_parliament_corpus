# Italian_Parliament_Symspell
## Steps
Scripts should be executed in order:
- first raw dataframes are preprocessed
- dictionaries for the symspell phase are created based on the dataframes
- dictionaries are merged in windows around the legislature in order to make correction more robust
- the evaluation is conducted with the gold standard: uncorrected texts, symspell-corrected texts using the base it-100k dictionary and the symspell-corrected texts using the window dictionaries are compared
- the correction of all documents is conducted
## Suggested project directory structure:
```bash
project/
│
├── README.md
│
├── data/                                  # data
│   ├── raw_data/ 
│   ├── preprocessed_data/ 
│   └── corrected_data/   
│
├── scripts/                               # Rest of the code in the repo
│   ├── cleaning_utils/
│   ├── requirements.txt
│   ├── 0-preprocessing.py   
│   ├── 1-create_dict.py   
│   └── ...         
│   
└── evaluation/                            #folder containing evaluation sets
    ├── gold_standard/
    │   ├── cam-leg-date-doc-page.txt
    │   ├── cam-leg-date-doc-page.txt   
    │   └── ...
    ├── uncorrected_set/
    │   ├── cam-leg-date-doc-page.txt   
    │   ├── cam-leg-date-doc-page.txt  
    │   └── ...
    ├── base_symspell_set/
    │   ├── cam-leg-date-doc-page.txt
    │   ├── cam-leg-date-doc-page.txt
    │   └── ...
    └── window_dict_symspell_set/
        ├── cam-leg-date-doc-page.txt  
        ├── cam-leg-date-doc-page.txt 
        └── ...
```
## Metrics
[Word Error Rate](https://en.wikipedia.org/wiki/Word_error_rate) and [Character Error Rate](https://torchmetrics.readthedocs.io/en/stable/text/char_error_rate.html) were used as evaluation metrics
## ToDo
- Add more gold standard documents (50 total at least)
- Implement t-test in evaluation phase
- Test different confidence cutoffs and cut criteria of dictionaries
