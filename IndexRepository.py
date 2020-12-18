from Fields import Fields
import pymongo

class IndexRepository:
    def __init__(self, index_instance_location, mongo_database_location, db_name):
        self.db_name = db_name
        self.index_instance_location = index_instance_location
        self.mongo_database_location = mongo_database_location

        self.col_per_word_freq = list()
        self.doc_per_word_freq = list()
        self.doc_freq = self.get_mongo_collections('_doc_freq')
        self.col_freq = self.get_mongo_collections('_col_freq')
        self.col_freq = list(self.col_freq.values())

        self.doc_ids = list(self.doc_freq.keys())  # Be aware that documents are not in any order
        self.doc_num = len(self.doc_ids)
        self.field_num = Fields.get_length()

    def get_mongo_collections(self, collection_suffix, words = []):
        # Set up the connection to the mongo database
        collection_name = self.index_instance_location.split('/')[-1]
        myclient = pymongo.MongoClient(self.mongo_database_location)
        db = myclient[self.db_name]
        ind_db = db[collection_name + collection_suffix]

        # Load the document indexes
        cursor = ind_db.find() if len(words) == 0 else ind_db.find({'key': {'$in': words}})
        index = dict()
        for item in cursor:
            index[item['key']] = item['val']
        return index

    def set_word_collections(self, query):
        words = query.split(' ')

        self.words = list(words)
        self.word_num = len(self.words)

        self.col_per_word_freq = self.get_mongo_collections('_col_per_word_freq', words)
        self.doc_per_word_freq = self.get_mongo_collections('_doc_per_word_freq', words)

    def get_doc_ids(self):
        return self.doc_ids

    def get_words(self):
        return self.words

    def get_count(self, word, doc_n, field_n):
        if doc_n in self.doc_per_word_freq[word].keys():
            return self.doc_per_word_freq[word][doc_n][field_n]
        else:
            return 0

    def get_col_count(self, word, field_n):
        return self.col_per_word_freq[word][field_n]

    def get_D_field_num(self, doc_n, field_n):
        return self.doc_freq[doc_n][field_n]

    def get_C_field_num(self, field_n):
        return self.col_freq[field_n]
