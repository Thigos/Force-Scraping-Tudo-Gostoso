import nltk
from nltk import tokenize
import spacy
import json

def _filter(token):
    if len(token) < 2:
        return False
    if token.is_stop:
        return False
    if token.text[0].islower():
        return False
    if token.is_digit:
        return False
    if token.like_num:
        return False
    return True


def _clean(text):
    text = text.replace("(", "")
    text = text.split("/")[0]
    return text


def get_labels(ingredients, tokenized_instructions):
    labels = []
    for ing, ti in zip(ingredients, tokenized_instructions):
        l_i = []
        ci = [_clean(t.text) for i in ing for t in nlp(i) if _filter(t) and len(_clean(t.text)) >= 2]
        label = []
        for token in ti:
            l_i.append(any((c == token.text or c == token.text[:-1] or c[:-1] == token.text) for c in ci))
        labels.append(l_i)
    return labels


PATH_DATA = "data/DATA.json"

def read_data_json():
    with open(PATH_DATA, "r") as file:
        data = json.load(file)
    return data


nlp = spacy.load('de_core_news_sm', disable=['parser', 'tagger', 'ner'])


data = read_data_json()
ingredients = []

for category in data:
    for recipe in category["recipes"]:
        for ingredient in recipe["ingredients"]:
            ingredients.append(ingredient)

tokenized = [nlp(t) for t in ingredients]

clean = [_clean(t.text) for i in ingredients for t in nlp(i) if _filter(t) and len(_clean(t.text)) >= 2]

print(clean)
