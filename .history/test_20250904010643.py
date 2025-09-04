from convokit import Corpus, download
import os

# Download the corpus and get the local path
corpus_path = download("switchboard-corpus")
print("Corpus downloaded to:", corpus_path)

# Show the files in the downloaded directory
print("Files in corpus directory:")
corpus = Corpus(download("switchboard-corpus"))
print(corpus)