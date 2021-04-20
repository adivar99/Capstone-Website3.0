import nltk
from textblob import TextBlob

nltk.download('stopwords')
nltk.download('punkt')
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import sent_tokenize , word_tokenize
import glob
import re
import csv
import os
import numpy as np
import pandas as pd

from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

import sys
Stopwords = set(stopwords.words('english'))
porter = PorterStemmer()
import nltk
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet



lemmatizer = WordNetLemmatizer()
import time
import copy
import math
from nltk.corpus import wordnet
from spellchecker import SpellChecker
spell = SpellChecker()

path='image_desc.csv'
df=pd.read_csv(path)
# function to convert nltk tag to wordnet tag
def nltk_tag_to_wordnet_tag(nltk_tag):
    if nltk_tag.startswith('J'):
        return wordnet.ADJ
    elif nltk_tag.startswith('V'):
        return wordnet.VERB
    elif nltk_tag.startswith('N'):
        return wordnet.NOUN
    elif nltk_tag.startswith('R'):
        return wordnet.ADV
    else:
        return None

def lemmatize_sentence(sentence):
    #tokenize the sentence and find the POS tag for each token
    nltk_tagged = nltk.pos_tag(nltk.word_tokenize(sentence))
    #tuple of (token, wordnet_tag)
    wordnet_tagged = map(lambda x: (x[0], nltk_tag_to_wordnet_tag(x[1])), nltk_tagged)
    lemmatized_sentence = []
    for word, tag in wordnet_tagged:
        if tag is None:
            #if there is no available tag, append the token as is
            lemmatized_sentence.append(word)
        else:
            #else use the tag to lemmatize the token
            lemmatized_sentence.append(lemmatizer.lemmatize(word, tag))
    return " ".join(lemmatized_sentence)

#Preprocessing

def get_terms(line):
    '''given a stream of text, get the terms from the text'''
    line = line.lower()
    line = re.sub(r'[^a-z0-9 ]', ' ', line)  # put spaces instead of non-alphanumeric characters
    line = re.sub(' +', ' ', line)
    words_tokens = word_tokenize(line)
    line = [w for w in words_tokens if not w in Stopwords]
    return line

def preprocess(line):
    line = re.sub(r"(\.|,|\?|\(|\)|\[|\]|\!|\'|\||\%|\:)", " ", line)
    line = re.sub(r'[^a-z0-9 ]', ' ', line)  # put spaces instead of non-alphanumeric characters
    line = re.sub('(?<=[a-z])\'(?=[a-z])', '', line)
    line = line.replace("-", "")
    line = line.replace("gonna", "going to")
    return line

contractions = {
"ain't": "are not",
"aren't": "am not",
"can't": "cannot",
"can't've": "cannot have",
"'cause": "because",
"could've": "could have",
"couldn't": "could not",
"couldn't've": "could not have",
"didn't": "did not",
"doesn't": "does not",
"don't": "do not",
"hadn't": "had not",
"hadn't've": "had not have",
"hasn't": "has not",
"haven't": "have not",
"he'd": "he would",
"he'd've": "he would have",
"he'll": "he will",
"he'll've": "he will have",
"he's": "he is",
"how'd": "how did",
"how'd'y": "how do you",
"how'll": "how will",
"how's": "how is",
"i'd": "i had",
"i'd've": "i would have",
"i'll": "i will",
"i'll've": "i will have",
"i'm": "i am",
"i've": "i have",
"isn't": "is not",
"it'd": "it would",
"it'd've": "it would have",
"it'll": "it will",
"it'll've": "it will have",
"it's": "it is",
"let's": "let us",
"ma'am": "madam",
"mayn't": "may not",
"might've": "might have",
"mightn't": "might not",
"mightn't've": "might not have",
"must've": "must have",
"mustn't": "must not",
"mustn't've": "must not have",
"needn't": "need not",
"needn't've": "need not have",
"o'clock": "of the clock",
"oughtn't": "ought not",
"oughtn't've": "ought not have",
"shan't": "shall not",
"sha'n't": "shall not",
"shan't've": "shall not have",
"she'd": "she would",
"she'd've": "she would have",
"she'll": "she will",
"she'll've": "she will have",
"she's": "she is",
"should've": "should have",
"shouldn't": "should not",
"shouldn't've": "should not have",
"so've": "so have",
"so's": "so is",
"that'd": "that had",
"that'd've": "that would have",
"that's": "that is",
"there'd": "there had",
"there'd've": "there would have",
"there's": "there is",
"they'd": "they had",
"they'd've": "they would have",
"they'll": "they will",
"they'll've": "they will have",
"they're": "they are",
"they've": "they have",
"to've": "to have",
"wasn't": "was not",
"we'd": "we would",
"we'd've": "we would have",
"we'll": "we will",
"we'll've": "we will have",
"we're": "we are",
"we've": "we have",
"weren't": "were not",
"what'll": "what will",
"what'll've": "what will have",
"what're": "what are",
"what's": "what is",
"what've": "what have",
"when's": "when is",
"when've": "when have",
"where'd": "where did",
"where's": "where is",
"where've": "where have",
"who'll": "who will",
"who'll've": "who will have",
"who's": "who is",
"who've": "who have",
"why's": "why is",
"why've": "why have",
"will've": "will have",
"won't": "will not",
"won't've": "will not have",
"would've": "would have",
"wouldn't": "would not",
"wouldn't've": "would not have",
"y'all": "you all",
"y'all'd": "you all would",
"y'all'd've": "you all would have",
"y'all're": "you all are",
"y'all've": "you all have",
"you'd": "you would",
"you'd've": "you would have",
"you'll": "you will",
"you'll've": "you will have",
"you're": "you are",
"you've": "you have",
"I'am":"I am"
}



#Vector Query

def wcount(s):
    counts = dict()
    words = s
    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1
    return counts


def build_query_vector(keywords,inverted_index):
    count = wcount(keywords)
    vector = np.zeros((len(count),1))
    for i, word in enumerate(keywords):
        print(count, i, word)
        print('each' in inverted_index)
        vector[i] = float(count[word])/len(count) * (1+math.log(df.shape[0]/len(inverted_index[word])))
    return vector

#TF-IDF vector
def generateVectors(keywords,inverted_index):
  tf_idf_matrix = np.zeros((len(keywords),df.shape[0]))
  for i, s in enumerate(keywords):
      idf = math.log(df.shape[0]/len(inverted_index[s]))+1
      for j in range(df.shape[0]):
        if(j in inverted_index[s]):
        	tf_idf_matrix[i][j]=idf
  return tf_idf_matrix


def consine_similarity(v1, v2):
    return np.dot(v1,v2)/float(np.linalg.norm(v1)*np.linalg.norm(v2))


def compute_relevance(tf_idf_matrix,query_vector):
    results=[]
    c=0
    for doc in range(df.shape[0]):
        similarity = consine_similarity(tf_idf_matrix[:,c].reshape(1, len(tf_idf_matrix)), query_vector)
        if(similarity>0):
        	l=[doc,float(similarity[0])]
        else:
        	l=[doc,0]
        results.append(l)
        c+=1
    return results

""" **USER** **SEARCH**

"""
def input_query(keywords,inverted_index,idf):
    keywords=preprocess(keywords)
    keywords=lemmatize_sentence(keywords)
    keywords=get_terms(keywords)
    for keyword in range(len(keywords)):
        misspelled = spell.unknown([keywords[keyword]])
        if(misspelled!=set()):
        	keywords[keyword]=spell.correction(misspelled.pop())
        present=False
        if(keywords[keyword] in ['sleeve','color']):
          continue
        for term in inverted_index.keys():
          if(keywords[keyword] in term.split()):
            keywords[keyword]=term
            present=True
            break
        if(present==False):
          syns=wordnet.synsets(keywords[keyword])
          synonyms=set()
          for i in range(len(syns)):
            synonyms.add((syns[i].lemmas()[0].name()).lower())
          synonyms=list(synonyms)
          for synonym in synonyms:
            for term in inverted_index.keys():
              if(synonym in term.split()):
                present=True
                keywords[keyword]=term
                break
            if(present==True):
              break
    keywords = [x for x in keywords if x not in ['sleeve','color']]
    print(" ".join(keywords))
    query_vector = build_query_vector(keywords,inverted_index)
    tf_idf_matrix = generateVectors(keywords,inverted_index)

    res=compute_relevance(tf_idf_matrix,query_vector)
    res=sorted(res,key=lambda item: (item[1]),reverse=True)
    return res
