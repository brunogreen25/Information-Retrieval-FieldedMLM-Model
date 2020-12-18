import enum

class Fields(enum.Enum):

    # Have to be written with delimeter and full_text has to be included
    Title = 'metadata/title'
    Abstract = 'abstract/text'
    Authors = 'metadata/authors/last'
    Location = "metadata/authors/location/country"
    FullText = 'body_text/text'

    # Metadata
    MetaTitle = 'title'
    MetaAbstract = 'abstract'
    MetaAuthors = 'authors'
    MetaUrl = 'url'
    MetaCordUid = 'cord_uid'
    MetaTime = 'publish_time'
    MetaPdfJson = 'pdf_json'
    MetaPmcJson = 'pmc_json'

    #@classmethod
    #def get_delimeter(cls):
    #    return cls.delimeter.value

    @classmethod
    def get_fields(cls):
        # It is very important to always use this to get fields, because this saves the order of the fields which is important throughtout the implementation
        return [cls.Title.value, cls.Abstract.value, cls.Authors.value, cls.Location.value, cls.FullText.value]

    @classmethod
    def get_position(cls, val):
        return cls.get_fields().index(val)

    @classmethod
    def get_length(cls):
       return len(cls.get_fields())

