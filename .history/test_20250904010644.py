from convokit import Corpus, download
import os

# Download the corpus and get the local path
corpus_path = download("switchboard-corpus")
print("Corpus downloaded to:", corpus_path)

# Show the files in the downloaded directory
print("Files in corpus directory:")
for root, dirs, files in os.walk(corpus_path):
    for name in files:
        print(os.path.join(root, name))

# Load the corpus
corpus = Corpus(corpus_path)
print(corpus)
# Show the first few utterances' text
