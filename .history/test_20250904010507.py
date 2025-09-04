from convokit import Corpus, download

def progress_hook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    percent = min(100, downloaded * 100 // total_size) if total_size > 0 else 0
corpus = Corpus(download("switchboard-corpus"))
print(corpus)