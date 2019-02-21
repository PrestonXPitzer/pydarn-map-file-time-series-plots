# Authors: Keith Kotyk and Marina Schmidt
import logging
pydarn_logger = logging.getLogger('pydarn')


class SuperDARNFileTypeError(Exception):
    """
    """
    def __init__(self, filename, file_type):
        self.filename = filename
        self.file_type = file_type
        self.message = "Error: {file_type} is not a DMAP file format type."\
            "{filename} was not created. Please check the spelling of"\
            " the file type is correct or is"\
            " implemented.".format(file_type=self.file_type,
                                   filename=self.filename)


class SuperDARNFieldMissingError(Exception):
    """
    """
    def __init__(self, filename, record_num, fields):
        self.filename = filename
        self.record_number = record_num
        self.fields = fields
        self.message = "Error: Cannot write to {filename}."\
            " The following fields in record {num} are missing:"\
            " {fields}".format(filename=self.filename,
                               num=self.record_number,
                               fields=self.fields)


class SuperDARNExtraFieldError(Exception):
    """
    """
    def __init__(self, filename, record_num, fields):
        self.filename = filename
        self.record_number = record_num
        self.fields = fields
        self.message = "Error: Cannot write to {filename}."\
            " The following fields in record {num} are not allowed:"\
            " {fields}".format(filename=self.filename,
                               num=self.record_number,
                               fields=self.fields)


class SuperDARNDataFormatTypeError(Exception):
    """
    """
    def __init__(self, incorrect_types, record_num):
        self.incorrect_params = incorrect_types
        self.record_number = record_num
        self.message = "Error: In record {num}, following parameters"\
            " need to be the data type:"\
            " {incorrect}".format(num=self.record_number,
                                  incorrect=self.incorrect_params)
