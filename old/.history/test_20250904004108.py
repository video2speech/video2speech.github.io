import nltk

# 下载 twitter_samples
nltk.download('twitter_samples')

from nltk.corpus import twitter_samples

print(twitter_samples.fileids())
# ['negative_tweets.json', 'positive_tweets.json', 'tweets.20150430-223406.json']

# 查看正面推文示例
print(twitter_samples.strings('positive_tweets.json')[:5])