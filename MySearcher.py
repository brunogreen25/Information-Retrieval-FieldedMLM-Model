import numpy as np
from IndexRepository import IndexRepository
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import settings
nltk.download('stopwords')
nltk.download('wordnet')
wordnet_lemmatizer = WordNetLemmatizer()
cached_stop_words = stopwords.words("english")

# Change name to MLMSearcher
class MySearcher:

    def __init__(self, index: IndexRepository, field_weights=None, smoothing_weights=None):
        self.index = index
        self.field_weights = field_weights if field_weights is not None else np.full((index.word_num()), 1/index.word_num())
        if len(self.field_weights) != self.index.field_num:
            raise ValueError("There should be the same amount of field weights as the number of fields in index.")

        self.smoothing_weights = smoothing_weights if smoothing_weights is not None else np.full((index.word_num()), 0.5)
        if len(self.smoothing_weights) != self.index.field_num:
            raise ValueError("There should be the same amount of smoothing weights as the number of fields in index.")

    def set_field_weights(self, field_weights = None):
        self.field_weights = field_weights if field_weights is not None else np.full((self.index.word_num()),
                                                                                     1 / self.index.word_num())
        if len(self.field_weights) != self.index.field_num:
            raise ValueError("There should be the same amount of field weights as the number of fields in index.")

    def set_smoothing_weights(self, smoothing_weights=None):
        self.smoothing_weights = smoothing_weights if smoothing_weights is not None else np.full((self.index.word_num()),
                                                                                                 0.5)
        if len(self.smoothing_weights) != self.index.field_num:
            raise ValueError("There should be the same amount of smoothing weights as the number of fields in index.")


    def search(self, query, n=None):
        hits = list()

        # Remove punctuation from query
        for sign in settings.punct:
            query = query.replace(sign, ' ')
        query = ' '.join(query.split())  # Removes multiple whitespaces

        # Remove stopwords and turn to lowercase
        query = ' '.join([word.lower() for word in query.split(" ") if not word in cached_stop_words])

        # Lemmatization
        query = ' '.join([wordnet_lemmatizer.lemmatize(word) for word in query.split(' ')])

        # Load the index dataset (in the RAM) for the neccessary words
        self.index.set_word_collections(query)

        for doc_id in self.index.get_doc_ids():
            hits.append((doc_id, self.calculate_score(query, doc_id)))
        hits = sorted(hits, key=lambda x: x[1], reverse=True)
        hits = hits[:n] if n != None else hits
        return hits

    def calculate_score(self, query, doc_id):
        score = 1
        for word in query.split(' '):
            word_score = 0
            if word not in self.index.get_words():
                continue
            for field_id in range(len(self.field_weights)):
                smooth_id = field_id

                r1 = self.index.get_count(word, doc_id, field_id) / self.index.get_D_field_num(doc_id, field_id) if self.index.get_D_field_num(doc_id, field_id) != 0 else 0
                r2 = self.index.get_col_count(word, field_id) / self.index.get_C_field_num(field_id) if self.index.get_C_field_num(field_id) != 0 else 0
                result = self.field_weights[field_id] * ((1-self.smoothing_weights[smooth_id]) * r1
                                                       + self.smoothing_weights[smooth_id] * r2)
                word_score += result
            score *= word_score
        score = np.log(score)
        return score
