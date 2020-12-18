index_version = 'v1.1'
index_location = 'Database/dataset_from_covid_notes/custom_index/index'+index_version
index_location_json = 'Database/dataset_from_covid_notes/custom_index/json_version/index' + index_version
metadata_location = 'Database/dataset_from_covid_notes/collections/cord19-2020-07-16/metadata.csv'
punct = '''!()-[]{};:'"\, <>./?@#$%^&*_~µω⁰1234567890'''
medical_corpus_location = 'Database/medical_corpus/medical_corpus.txt'
path_to_json_folder = 'Database/dataset_from_covid_notes/collections/cord19-2020-07-16/document_parses/pdf_json'
path_to_xml_folder = 'Database/dataset_from_covid_notes/collections/cord19-2020-07-16/document_parses/pmc_json'
output_print_file = "Database/dataset_from_covid_notes/collections/cord19-2020-07-16/output_log_file.txt"
delimeter_between_files = "\\"
delimeter_between_fields = "/"

# Evaluation files
path_to_topics_xml = 'Database/evaluation/topics-rnd5.xml'
path_to_results = 'Database/evaluation/qrels-covid_d5_j0.5-5.txt'
duplicates_txt = 'Database/duplicates/duplicates.txt'

# Evaluation results
precision_k_directory = 'Database/evaluation/results'

# Database
index_instance_location = 'Database/dataset_from_covid_notes/custom_index/index_instance/index' + index_version

mongo_database_location = 'mongodb://localhost:27017/'
database_name = 'inf_ret'

