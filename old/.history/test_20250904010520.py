from convokit import Corpus, download

def progress_hook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    percent = min(100, downloaded * 100 // total_size) if total_size > 0 else 0
    print(f"\rDownloading: {percent}% ({downloaded // 1024}KB/{total_size // 1024 if total_size > 0 else '?'}KB)", end='')

corpus = Corpus(download("switchboard-corpus", verbose=True, progress_bar=progress_hook))
print("\nDownload complete.")
print(corpus)