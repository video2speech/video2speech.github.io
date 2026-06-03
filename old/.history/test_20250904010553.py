from convokit import Corpus, download
import os

# Download the corpus and get the local path
corpus_path = download("switchboard-corpus")
corpus = Corpus(download("switchboard-corpus"))
print(corpus)