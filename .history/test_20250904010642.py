from convokit import Corpus, download

corpus = Corpus(download("switchboard-corpus"))
print(corpus)