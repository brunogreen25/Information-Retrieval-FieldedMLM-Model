# Imports and downloads
import os
import json
import nltk
from nltk.corpus import stopwords
import settings
from Fields import Fields
from nltk.stem import WordNetLemmatizer
import time
import pickle
from import_metadata import import_csv_metadata
import enchant
import pymongo

nltk.download('stopwords')
nltk.download('wordnet')

# Global variables (global both read/write)
index_doc_per_word_freq = dict()
index_doc_freq = dict()
index_col_per_word_freq = dict()
index_col_freq = [0] * Fields.get_length()
output = list()

skipped_files = []

def add_to_col_freq(full_field):
    global index_col_freq
    field_pos = Fields.get_position(full_field)
    index_col_freq[field_pos] += 1


def add_to_col_per_word_freq(clean_word, full_field):
    global index_col_per_word_freq
    field_pos = Fields.get_position(full_field)

    if clean_word not in index_col_per_word_freq.keys():
        index_col_per_word_freq[clean_word] = [0] * Fields.get_length()

    index_col_per_word_freq[clean_word][field_pos] += 1


def add_to_doc_freq(doc_id, full_field):
    global index_doc_freq
    field_pos = Fields.get_position(full_field)

    if doc_id not in index_doc_freq.keys():
        index_doc_freq[doc_id] = [0] * Fields.get_length()

    index_doc_freq[doc_id][field_pos] += 1


def save_to_collections(index, db, collection_name, suffix):
    ind_db = db[collection_name + suffix]
    ind_db.delete_many({})

    items = index.items() if type(index) is dict else enumerate(index)
    for key, val in items:
        chunk = dict()
        chunk['key'] = key
        chunk['val'] = val
        ind_db.insert(chunk)


def save_index_in_mongo(index_instance_location, database_location):
    collection_name = index_instance_location.split('/')[-1]
    myclient = pymongo.MongoClient(database_location)
    db = myclient[settings.database_name]

    save_to_collections(index_doc_per_word_freq, db, collection_name, '_doc_per_word_freq')
    save_to_collections(index_doc_freq, db, collection_name, '_doc_freq')
    save_to_collections(index_col_per_word_freq, db, collection_name, '_col_per_word_freq')
    save_to_collections(index_col_freq, db, collection_name, '_col_freq')


def add_new_entry(doc_id, word, field_num):
    global index_doc_per_word_freq
    index_doc_per_word_freq[word][doc_id][field_num] += 1


def create_new_entry(word):
    global index_doc_per_word_freq
    index_doc_per_word_freq[word] = dict()


def create_document_for_word(doc_id, word):
    global index_doc_per_word_freq
    index_doc_per_word_freq[word][doc_id] = Fields.get_length() * [0]


def add_word_to_index(doc_id, word, field):
    global index_doc_per_word_freq
    field_pos = Fields.get_position(field)

    # Add word to index if it does not exist        #(and the word bound has not passed)
    if word not in index_doc_per_word_freq.keys():
        create_new_entry(word)

    # Add this document to the word if this is the first time the word appears in this document
    if doc_id not in index_doc_per_word_freq[word].keys():
        create_document_for_word(doc_id, word)

    add_new_entry(doc_id, word, field_pos)
    return

eng_word_dict = set()
def isSpletCorrectly(corpus, medical_corpus, word):
    global eng_word_dict
    if word in eng_word_dict:
        return True
    elif (not corpus.check(word)) and (not corpus.check(word.capitalize())) and (
            word not in ['covid', 'corona']) and (word not in medical_corpus) and (word.capitalize() not in medical_corpus):
        return False
    else:
        eng_word_dict.add(word)
        return True


def import_json_index(path_to_json, path_to_xml, path_to_metadata_file, fields, delimeter, punct, stop_words, word_lemmatizer, corpus, medical_corpus, break_indexing = -1):
    global output

    current_file_index = 0
    # Default of break_indexing is -1, because that means that it will never stop
    section_time = 0

    # Import csv metadata
    metadata = import_csv_metadata(path_to_metadata_file)


    # For skipping (in case there are same documents in both dataset directories)
    cord_pmcpdf_tuple = [(d[Fields.MetaCordUid.value], d[Fields.MetaPdfJson.value], d[Fields.MetaPmcJson.value]) for d in metadata.values()]

    # Get all files
    files_in_dir = [path_to_json + '/' + file for file in os.listdir(path_to_json) if file.endswith('.json')] # Adding pdf_json files
    files_in_dir += [path_to_xml + '/' + file for file in os.listdir(path_to_xml) if file.endswith('.json')] # Adding pmc_json files
    file_length = len(files_in_dir)

    start = time.time()
    for file_name in files_in_dir:
        # region Prograss Tracking
        output.append(
            "Current Progress: " + str(round(current_file_index / file_length * 100, 2)) + "% | Files scanned: " +
            str(current_file_index) + "/" + str(file_length) + " | Elapsed time: " + str(round(time.time() - start, 2)) + "s | Word count in index: " +
            str(len(index_doc_per_word_freq)) + ' | Section time: ' + str(round(section_time, 4)))
        print(output[-1])
        current_file_index += 1
        if current_file_index == break_indexing:
            break
        # endregion

        # Iterate over every file
        with open(file_name) as json_file:
            data = json.load(json_file)
            doc_id = data["paper_id"]
            cord_uid = ''

            # region Skip files already scanned in the previous directory
            skip_this_file = True
            for i, x in enumerate(cord_pmcpdf_tuple):
                if doc_id in x[1] or doc_id in x[2]:
                    cord_uid = x[0]
                    cord_pmcpdf_tuple.pop(i)
                    skip_this_file = False
            if skip_this_file:
                skipped_files.append(file_name)
                print("File " + file_name + " skipped.")
                continue
            doc_id = cord_uid # Cord-id is the real unique value
            if doc_id == '':
                raise Exception('No doc-id in' + current_file_index)
            # endregion

            # Save field, it will be lost in parsing, but needed for later
            for field in fields:
                full_field = field

                # 1 - PARSING
                # Recursively parse sub-fields (probably works only for 1 splitting, recursion is probably needed to acheive multiple splittings)

                d = data  # Need because it is going to change

                next_field = False
                while field:
                    # If it is a list of attributes, create a list, otherwise raise the count
                    if isinstance(d, list):
                        dat = list()
                        for d_ in d:

                            # If it does not contain that field
                            if field.split(delimeter)[0] not in d_.keys():
                                next_field = True
                                break
                            dat.append(d_[field.split(delimeter)[0]])
                        d = dat
                    else:
                        # If it does not contain that field
                        if field.split(delimeter)[0] not in d.keys():
                            next_field = True
                            break
                        d = d[field.split(delimeter)[0]]
                    field = field.split(delimeter, 1)[1] if delimeter in field else ''

                # Skip fields which do not exist (And add 0 for all those words)
                if next_field == True:
                    continue


                # 2 - PUT IT IN INDEX
                if not isinstance(d, list):
                    # Format it all into a list for lesser complexity
                    d = [d]

                # For each list item, perform indexing
                for el_sentence in d:
                    # region Remove punctuation
                    for sign in punct:
                        el_sentence = el_sentence.replace(sign, ' ')
                    el_sentence_no_punct = ' '.join(el_sentence.split())  # Removes multiple whitespaces
                    # endregion

                    # region Remove stop-words
                    el_bag_of_words = [word for word in el_sentence_no_punct.split(" ") if not word in stop_words]
                    # endregion

                    # region Perform lemmatization
                    el_bag_of_words = [word_lemmatizer.lemmatize(word) for word in el_bag_of_words]
                    # endregion


                    # Index the words
                    for clean_word in el_bag_of_words:

                        # Skip the empty words which maybe got created due to punctuation (but probably won't)
                        if clean_word == '':
                            continue

                        # If it is not abbreviation(all upper), then turn it to lowercase and check if the word exists
                        if not clean_word.isupper():
                            # Turn words to lowercase
                            clean_word = clean_word.lower()

                            # Skip the words not in english vocabulary
                            if not isSpletCorrectly(corpus, medical_corpus, clean_word):
                                continue
                        else:
                            # Turn abbreviations to lowercase also
                            clean_word = clean_word.lower()

                        add_word_to_index(doc_id, clean_word, full_field) #This "index" is "index_doc_per_word_freq"
                        add_to_doc_freq(doc_id, full_field)
                        add_to_col_per_word_freq(clean_word, full_field)
                        add_to_col_freq(full_field)


# region METADATA INDEXING - not needed for this project
# TODO: delete this (metadata indexer)
def import_metadata_index(path_to_file, punct, wordnet_lemmatizer, break_indexing = -1):
    # Default of break_indexing is -1, because that means that it will never stop
    current_file_index = 0
    metadata = import_csv_metadata(path_to_file)
    instance_num = len(metadata.keys())
    fields = Fields.get_fields() # Second get_fields function

    start = time.time()
    # For each list item perform indexing
    for doc_id, doc_props in metadata.items():

        # region Prograss Tracking
        print(
            "Current Progress: " + str(round(current_file_index / instance_num * 100, 2)) + "% | Files scanned: " + str(
                current_file_index) + "/" + str(instance_num) + " | Elapsed time: " + str(
                time.time() - start) + " | Word count in index: " + str(len(index_doc_per_word_freq)))
        current_file_index += 1
        if current_file_index == break_indexing:
            break
        # endregion

        for field in fields:
            data = doc_props[field]

            # PUT IT IN INDEX

            # region Remove punctuation
            for sign in punct:
                data = data.replace(sign, ' ')
            data = ' '.join(data.split())  # Removes multiple whitespaces
            # endregion

            # region Remove stop-words, turn words to lowercase
            data = [word.lower() for word in data.split(" ") if not word in stopwords.words()]
            # endregion

            # region Perform lemmatization
            data = [wordnet_lemmatizer.lemmatize(word) for word in data]
            # endregion

            # Index the words
            for word in data:
                # Skip the empty words which maybe got created due to punctuation (but probably won't)
                if word == '':
                    continue

                add_word_to_index(doc_id, word, field)
# endregion

def get_medical_corpus(medical_corpus_location):
    with open(medical_corpus_location) as file:
        lines = file.readlines()
    return [line.strip() for line in lines]



if __name__ == '__main__':
    fields = Fields.get_fields()
    cached_stop_words = stopwords.words("english")
    wordnet_lemmatizer = WordNetLemmatizer()
    corpus = enchant.Dict("en_US")
    medical_corpus = get_medical_corpus(settings.medical_corpus_location)

    import_json_index(settings.path_to_json_folder, settings.path_to_xml_folder, settings.metadata_location, fields, settings.delimeter_between_fields, settings.punct, cached_stop_words, wordnet_lemmatizer, corpus, medical_corpus, -1)

    # Save duplicate files in a txt (files which were skipped)
    start_time_interval = time.time()
    pickle_out = open(settings.duplicates_txt, "wb")
    pickle.dump(skipped_files, pickle_out)
    pickle_out.close()
    print("Duplicates saved in " + str(round(time.time()-start_time_interval, 3)) + "s")

    # Save index as mongo_db
    start_time_interval = time.time()

    # Save output to txt
    log_file = settings.output_print_file
    with open(log_file) as log_file:
        for item in output:
            log_file.write("%s\n" % item)


    # Dump index instance in the pickle (so there is no need for recreation
    start_time_interval = time.time()
    save_index_in_mongo(settings.index_instance_location, settings.mongo_database_location)
    print("Index saved in MongoDB in " + str(round(time.time()-start_time_interval,3)) + "s")
