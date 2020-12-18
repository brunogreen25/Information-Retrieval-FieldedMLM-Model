import csv
from Fields import Fields

# Exports dictionary of metadata where each document has a dictionary of: title, abstract, publish_date, authors, url
def import_csv_metadata(path_to_file):
    metadata = dict()
    with open(path_to_file, encoding='utf8') as csv_file:
        reader = csv.DictReader(csv_file)
        for i, row in enumerate(reader):
            doc_id = row['cord_uid']
            metadata[doc_id] = {
                    Fields.MetaTitle.value: row['title'],
                    Fields.MetaAbstract.value: row['abstract'],
                    Fields.MetaTime.value: row['publish_time'],
                    Fields.MetaCordUid.value: row['cord_uid'],
                    Fields.MetaAuthors.value: row['authors'],
                    Fields.MetaUrl.value: row['url'],
                    Fields.MetaPdfJson.value: row['pdf_json_files'],
                    Fields.MetaPmcJson.value: row['pmc_json_files']
                }
    return metadata
