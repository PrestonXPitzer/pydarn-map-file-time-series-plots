# Copyright 2019 SuperDARN Canada, University of Saskatchewan
# Author: Marci Detwiller
"""
This file contains classes for reading, and 
writing of Borealis array file types. Array file 
types are restructured Borealis files. Files are restructured
after being written by the radar to condense all information 
from that time period into arrays. The other type of 
Borealis file is the site file. Site file types
are Borealis site files, ie. stored in a record-by-record
fashion, before being converted to array types.

Classes
-------
BorealisArrayRead: Reads array-style Borealis SuperDARN file types (hdf5). 
    These are the files commonly distributed and available.
BorealisArrayWrite: Writes array-style Borealis SuperDARN file types (hdf5).
    These are the files commonly distributed and available.

Exceptions
----------
BorealisFileTypeError
BorealisFieldMissingError
BorealisExtraFieldError
BorealisDataFormatTypeError
BorealisNumberOfRecordsError

See Also
--------
BorealisSiteRead
BorealisSiteWrite
borealis_site_to_array_file
borealis_array_to_site_file

For more information on Borealis data files and how they convert to dmap,
see: https://borealis.readthedocs.io/en/latest/ 

"""
import deepdish as dd
import h5py
import logging
import math
import numpy as np
import os

from collections import OrderedDict
from datetime import datetime
from typing import Union, List

from pydarn import borealis_exceptions, DarnWrite, borealis_formats, \
				   BorealisUtilities, code_to_stid, borealis_array_to_site_dict,
                   BorealisSiteRead, BorealisSiteWrite
from pydarn.utils.conversions import dict2dmap

pydarn_log = logging.getLogger('pydarn')


class BorealisArrayRead():
    """
    Class for reading Borealis 'array' filetypes. Array files have
    been restructured to no longer be read in record-by-record
    style. 

    See Also
    --------
    BorealisRawacf
    BorealisBfiq
    BorealisAntennasIq
    BorealisRawrf

    Attributes
    ----------
    filename: str
        The filename of the Borealis HDF5 file being read.
    borealis_filetype: str
        The type of Borealis file. Restructured types include:
        'bfiq'
        'antennas_iq'
        'rawacf'
    record_names: list(str)
    records: dict
    arrays: dict
    """

    def __init__(self, filename: str, borealis_filetype: str):
        """
        Reads Borealis array file types into a dictionary.

        Parameters
        ----------
        filename: str
            file name containing Borealis hdf5 data.
        borealis_filetype: str
            The type of Borealis file. Types include:
            'bfiq'
            'antennas_iq'
            'rawacf'
            'rawrf'

        Raises
        ------
        OSError
            Unable to open file
        """
        self.filename = filename

        if borealis_filetype not in ['bfiq', 'antennas_iq', 'rawacf', 'rawrf']:
            raise borealis_exceptions.BorealisFileTypeError(
                self.filename, borealis_filetype)
        self.borealis_filetype = borealis_filetype

        # Records are private to avoid tampering.
        self._arrays = {}
        self.read_file()

    def __repr__(self):
        """ for representation of the class object"""
        # __class__.__name__ allows to grab the class name such that
        # when a class inherits this one, the class name will be the child
        # class and not the parent class
        return "{class_name}({filename}, {borealis_filetype})"\
            "".format(class_name=self.__class__.__name__,
                      filename=self.filename, 
                      borealis_filetype=self.borealis_filetype)

    def __str__(self):
        """ for printing of the class object"""

        return "Reading from {filename}"\
            "".format(filename=self.filename)

    @property
    def record_names(self):
        """
        A sorted list of the set of record names in the HDF5 file read. 
        These correspond to Borealis file record write times (in ms), and
        are equal to the group names in the site file types.
        """
        return sorted(list(records.keys()))

    @property
    def records(self):
        """
        The Borealis data in a dictionary of records, according to the 
        site file format.
        """
        return borealis_array_to_site_dict(self.arrays, 
                                           self.borealis_filetype)

    @property 
    def arrays(self):
        """
        The Borealis data in a dictionary of arrays, according to the 
        restructured array file format.
        """
        return self._arrays

    def read_file(self) -> dict:
        """
        Reads the specified Borealis file using the other functions for 
        the proper file type.

        Reads the entire file.

        See Also
        --------
        read_bfiq
        read_rawacf
        read_antennas_iq

        Returns
        -------
        arrays: dict
            borealis data dictionary. Keys are data field names and
            unshared fields have a first dimension = number of records 
            in the file.

        Raises
        ------
        BorealisFileTypeError
        """
        if self.borealis_filetype == 'bfiq':
            return self.read_bfiq()
        elif self.borealis_filetype == 'rawacf':
            return self.read_rawacf()
        elif self.borealis_filetype == 'antennas_iq':
            return self.read_antennas_iq()
        else:
            raise borealis_exceptions.BorealisFileTypeError(
                self.filename, borealis_filetype)

    def read_bfiq(self) -> dict:
        """
        Reads Borealis bfiq file that has been structured into arrays.

        Returns
        -------
        arrays: dict
            The Borealis data in a dictionary of arrays, according to the 
            restructured array file format.
        """
        pydarn_log.debug("Reading Borealis bfiq file: {}"
                         "".format(self.filename))
        attribute_types = \
            borealis_formats.BorealisBfiq.array_single_element_types
        dataset_types = borealis_formats.BorealisBfiq.array_array_dtypes
        unshared_fields = borealis_formats.BorealisBfiq.unshared_fields
        self._read_borealis_arrays(attribute_types, dataset_types, 
            unshared_fields)
        return self._arrays

    def read_rawacf(self) -> dict:
        """
        Reads Borealis rawacf file that has been structured into arrays.

        Returns
        -------
        arrays: dict
            The Borealis data in a dictionary of arrays, according to the 
            restructured array file format.
        """
        pydarn_log.debug(
            "Reading Borealis rawacf file: {}".format(self.filename))
        attribute_types = \
            borealis_formats.BorealisRawacf.array_single_element_types
        dataset_types = borealis_formats.BorealisRawacf.array_array_dtypes
        unshared_fields = borealis_formats.BorealisRawacf.unshared_fields
        self._read_borealis_arrays(attribute_types, dataset_types, 
            unshared_fields)
        return self._arrays

    def read_antennas_iq(self) -> dict:
        """
        Reads Borealis antennas_iq file that has been structured into arrays.

        Returns
        -------
        arrays: dict
            The Borealis data in a dictionary of arrays, according to the 
            restructured array file format.
        """
        pydarn_log.debug("Reading Borealis antennas_iq file: {}"
                         "".format(self.filename))
        attribute_types = \
            borealis_formats.BorealisAntennasIq.array_single_element_types
        dataset_types = borealis_formats.BorealisAntennasIq.array_array_dtypes
        unshared_fields = borealis_formats.BorealisAntennasIq.unshared_fields
        self._read_borealis_arrays(attribute_types, dataset_types, 
            unshared_fields)
        return self._arrays

    def _read_borealis_arrays(self, attribute_types: dict,
                              dataset_types: dict, 
                              unshared_fields: List[str]):
        """
        Read the entire file while checking all data fields.

        Parameters
        ----------
        attribute_types: dict
            Dictionary with the required types for the attributes in the file.
        dataset_types: dict
            Dictionary with the require dtypes for the numpy arrays in the 
            file.
        unshared_fields: List[str]
            List of fields that are not shared between the records and 
            therefore should be an array with first dimension = number of 
            records

        Raises
        ------
        BorealisFieldMissingError - when a field is missing from the Borealis
                                file
        BorealisExtraFieldError - when an extra field is present in the
                                Borealis file
        BorealisDataFormatTypeError - when a field has the incorrect
                                field type for the Borealis file
        BorealisNumberOfRecordsError - when the number of records cannot 
                                be discerned from the arrays

        See Also
        --------
        BorealisUtilities
        """
        arrays = dd.io.load(self.filename)
        BorealisUtilities.check_arrays(self.filename, arrays, attribute_types,
            dataset_types, unshared_fields)
        self._arrays = arrays


class BorealisArrayWrite():
    """
    Class for writing Borealis 'array' filetypes. Array files have
    been restructured to no longer be read in record-by-record
    style. 

    See Also
    --------
    BorealisRawacf
    BorealisBfiq
    BorealisAntennasIq
    BorealisRawrf

    Attributes
    ----------
    filename: str
        The filename of the Borealis HDF5 file being written.
    borealis_filetype: str
        The type of Borealis file. Restructured types include:
        'bfiq'
        'antennas_iq'
        'rawacf'
    compression: str
        The type of compression to write the file as. Default zlib.
    arrays: dict
        The Borealis data in a dictionary of arrays, according to the 
        restructured array file format.
    """

    def __init__(self, filename: str, borealis_arrays: dict, 
                 borealis_filetype: str, compression: str = 'zlib'):
        """
        Write borealis records to a file.

        Parameters
        ----------
        filename: str
            Name of the file the user wants to write to
        borealis_arrays: dict
            borealis data dictionary. Keys are data field names and
            unshared fields have a first dimension = number of records 
            in the file.
        borealis_filetype: str
            The type of Borealis file. Restructured types include:
            'bfiq'
            'antennas_iq'
            'rawacf'
        compression: str
            String representing compression type. Default zlib.
        """
        self.filename = filename
        self.arrays = borealis_arrays
        self.borealis_filetype = borealis_filetype
        self.compression = compression
        self.write_file()

    def __repr__(self):
        """For representation of the class object"""

        return "{class_name}({filename}, {current_record_name})"\
               "".format(class_name=self.__class__.__name__,
                         filename=self.filename,
                         current_record_name=self.current_record_name)

    def __str__(self):
        """For printing of the class object"""

        return "Writing to filename: {filename} at record name: "\
               "{current_record_name}".format(filename=self.filename,
                    current_record_name=self.current_record_name)

    def write_file(self) -> str:
        """
        Write Borealis records to a file given filetype.

        Raises
        ------
        BorealisFileTypeError
        """

        if self.borealis_filetype == 'bfiq':
            self.write_bfiq()
        elif self.borealis_filetype == 'rawacf':
            self.write_rawacf()
        elif self.borealis_filetype == 'antennas_iq':
            self.write_antennas_iq()
        else:
            raise borealis_exceptions.BorealisFileTypeError(self.filename,
                                                            borealis_filetype)

    def write_bfiq(self) -> str:
        """
        Writes Borealis bfiq file

        Returns
        -------
        filename: str
            Filename of written file.
        """
        pydarn_log.debug(
            "Writing Borealis bfiq file: {}".format(self.filename))
        attribute_types = \
            borealis_formats.BorealisBfiq.array_single_element_types
        dataset_types = borealis_formats.BorealisBfiq.array_array_dtypes
        unshared_fields = borealis_formats.BorealisBfiq.unshared_fields
        self._write_borealis_arrays(attribute_types, dataset_types, 
            unshared_fields)
        return self.filename

    def write_rawacf(self) -> str:
        """
        Writes Borealis rawacf file

        Returns
        -------
        filename: str
            Filename of written file.
        """
        pydarn_log.debug(
            "Writing Borealis rawacf file: {}".format(self.filename))
        attribute_types = \
            borealis_formats.BorealisRawacf.array_single_element_types
        dataset_types = borealis_formats.BorealisRawacf.array_array_dtypes
        unshared_fields = borealis_formats.BorealisRawacf.unshared_fields
        self._write_borealis_arrays(attribute_types, dataset_types, 
            unshared_fields)
        return self.filename

    def write_antennas_iq(self) -> str:
        """
        Writes Borealis antennas_iq file

        Returns
        -------
        filename: str
            Filename of written file.
        """
        pydarn_log.debug(
            "Writing Borealis antennas_iq file: {}".format(self.filename))
        attribute_types = \
            borealis_formats.BorealisAntennasIq.array_single_element_types
        dataset_types = borealis_formats.BorealisAntennasIq.array_array_dtypes
        unshared_fields = borealis_formats.BorealisAntennasIq.unshared_fields
        self._write_borealis_arrays(attribute_types, dataset_types, 
            unshared_fields)
        return self.filename

    def _write_borealis_arrays(self, attribute_types: dict,
                              dataset_types: dict, 
                              unshared_fields: List[str]):
        """
        Write the entire file while checking all data fields.

        Parameters
        ----------
        attribute_types: dict
            Dictionary with the required types for the attributes in the file.
        dataset_types: dict
            Dictionary with the require dtypes for the numpy arrays in the 
            file.
        unshared_fields: List[str]
            List of fields that are not shared between the records and 
            therefore should be an array with first dimension = number of 
            records

        Raises
        ------
        BorealisFieldMissingError - when a field is missing from the Borealis
                                file
        BorealisExtraFieldError - when an extra field is present in the
                                Borealis file
        BorealisDataFormatTypeError - when a field has the incorrect
                                field type for the Borealis file
        BorealisNumberOfRecordsError - when the number of records cannot 
                                be discerned from the arrays

        See Also
        --------
        BorealisUtilities
        """
        BorealisUtilities.check_arrays(self.filename, self.arrays, 
            attribute_types, dataset_types, unshared_fields)
        dd.io.save(self.filename, self.arrays, compression=self.compression)
