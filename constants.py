API_KEY = "6b1e12**************************"

expected_header = ["Name", "Address"]


verbose = True
similarity_score_threshold = 50
data_street_main = {
    "data": [
        ["street ", "ul.", "str.", "ul ", "str ", "ulitsa"],
        ["avenue ", "ave.", "ave "],
        ["boulevard ", "bul." "blvd.", "boulevard  ", "bulevard "],
        ["road ", "rd.", "rd "],
        ["lane ", "ln.", "ln "],
        ["drive ", "dr.", "dr "],
        ["place ", "pl." "pl "],
        ["court ", "ct.", "ct "],
        ["terrace ", "ter.", "ter "],
        ["parkway ", "pkwy.", "pkwy "],
    ]
}

# Define the Cyrillic to Latin transliteration dictionary
translit_dict = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sht",
    "ъ": "u",
    "ю": "yu",
    "я": "a",
}
