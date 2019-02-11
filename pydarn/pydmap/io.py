# Copyright 2018 SuperDARN
# Authors: Marina Schmidt and Keith Kotyk
"""
This file contains classes to reading and writing of DMAP file formats used by
SuperDARN.

Classes:
--------
DmapRead : Reads DMAP files
DmapWrite : writes DMAP Record structure into a DMAP file

Exceptions:
-----------
EmptyFileError
CursorError
DmapDataError
DmapDataTypeError
ZeroByteError
MismatchByteError
ValueError

Future work
-----------
Organization
    rethink public and private methods? <--- discussion

Notes
-----
DmapRead and DmapWrite are updated and improved versions of
backscatter's pydmap:
git@github.com:SuperDARNCanada/backscatter.git
written by Keith Kotyk
"""

import os
import struct
import numpy as np
import logging
import collections

from typing import Union, List

from pydarn import pydmap_exceptions
from pydarn import superdarn_formats
from pydarn import DmapArray
from pydarn import DmapScalar

# Keeping these global definitions for readability purposes
# Data types use in DMAP files
DMAP = 0
CHAR = 1
SHORT = 2
INT = 3
FLOAT = 4
DOUBLE = 8
STRING = 9
LONG = 10
UCHAR = 16
USHORT = 17
UINT = 18
ULONG = 19

# Dictionary of DMAP types (key) to quickly convert the format and byte size
# (value-tuple)
DMAP_DATA_TYPES = {DMAP: ('', 0),
                   CHAR: ('c', 1),
                   SHORT: ('h', 2),
                   INT: ('i', 4),
                   FLOAT: ('f', 4),
                   DOUBLE: ('d', 8),
                   STRING: ('s', 1),
                   LONG: ('q', 8),
                   UCHAR: ('B', 1),
                   USHORT: ('H', 2),
                   UINT: ('I', 4),
                   ULONG: ('Q', 8)}

pydarn_logger = logging.getLogger('pydarn')


class DmapRead():
    """
    Reading and testing the integrity of DMAP files/stream.
    ...

    Attributes
    ----------
    dmap_file : str
        DMAP file name or data stream (give data_stream=True)
    cursor : int
        Current position in the byte array
    dmap_end_bytes : int
        The length of the byte array

    Methods
    --------
    test_initial_data_integrity()
        Quickly reads the byte array for any errors
    read_records()
        Reads the byte array to obtain the DMAP records
    zero_negative_check(element, element_name)
        Checks if the element is equal to zero
    check_data_type(data_type, data_name)
        Checks if the data_type exists in DMAP_DATA_TYPE dictionary
    read_record()
        Reads a record from the byte array
    read_scalar()
        Reads a scalar from the byte array
    read_array(record_size)
        Reads an array from the byte array
    read_string_DMAP_array(Shape, array_type)
        Reads an array of strings/DMAP types into an array
    read_data()
        Reads the data type from the byte array
    read_numerical_array(data_type, shape, total_number_cells)
        Reads an array into a numpy array
    """

    def __init__(self, dmap_file: Union[str,bytes], data_stream=False):
        """
        Reads the dmap file/stream into a byte array for further reading of the
        dmap records.

        Parameters
        ----------
        dmap_file : str or bytes
                    file name or data stream (given data_stream=True)
                    containing dmap data.
        data_stream : bool
                 default to false, boolean that indicates if dmap_file is a
                 data stream
        Raises
        ------
        EmptyFileError
            dmap_file is empty
        FileNotFoundError
            dmap_file path does not exist

        See Also
        --------
        read_records : to obtain dmap_records
        """

        self.cursor = 0  # Current position in bytes
        self.dmap_end_bytes = 0  # total number of bytes in the dmap_file

        """
        Dmap records are stored in a deque data structure for
        memory efficiency and performance. Acts the same as a stack/list.
        See DEVELOPER_README.md for more information.
        """

        # __dmap_records are private to avoid tampering.
        self.__dmap_records = collections.deque()
        self.dmap_file = dmap_file

        # read the whole file/stream into a byte array
        if data_stream is False:
            # check if the file is empty
            if os.path.getsize(self.dmap_file) == 0:
                raise pydmap_exceptions.EmptyFileError(self.dmap_file)

            # Read binary dmap file
            with open(self.dmap_file, 'rb') as f:
                self.dmap_bytearr = bytearray(f.read())
            pydarn_logger.debug("DMAP Read file: {}".format(self.dmap_file))

        else:
            if len(dmap_file) == 0:
                raise pydmap_exceptions.EmptyFileError("data stream")

            self.dmap_bytearr = bytearray(self.dmap_file)
            self.dmap_file = "stream"
            pydarn_logger.debug("DMAP Read file: Stream")
        self.dmap_buffer = memoryview(self.dmap_bytearr)
        self.dmap_end_bytes = len(self.dmap_bytearr)
        if self.dmap_end_bytes == 0:
            raise pydmap_exceptions.EmptyFileError(self.dmap_file)

    def zero_negative_check(self, element: int, element_name: str):
        """
        Checks if the element <= 0 bytes. If true then raise a ZeroByteError.

        Parameter
        ---------
        element : int
            An element to check if it is zero
        element_name : str
            The element's name title for a more detailed exception message

        Raises
        ------
        ZeroByteError
            if element <= 0
        """

        if element == 0:
            element_info = "{name} {size}".format(name=element_name,
                                                  size=element)
            raise pydmap_exceptions.ZeroByteError(self.dmap_file, element_info,
                                                  self.cursor)
        elif element < 0:
            element_info = "{name} {size}".format(name=element_name,
                                                  size=element)
            raise pydmap_exceptions.NegativeByteError(self.dmap_file,
                                                      element_info,
                                                      self.cursor)

    def bytes_check(self, element: int, element_name: str, byte_check: int,
                    byte_check_name: str):
        """
        Checks if the element greater than the value comparing against
        (byte_check).

        Parameter
        ---------
        element : int
            An element to check if it is greater than another value in bytes
        element_name : str
            Name of the element for a more detailed exception message
        byte_check : int
            The byte value for the element to compare against
        byte_check_name : str
            Name of the byte value to be compared too for a more detailed
            exception message

        Raises
        ------
        MismatchByteError
             if element > byte_check
        """
        if element > byte_check:
            element_info = "{name} {size} >"\
                    " {check_name} {check}".format(name=element_name,
                                                   size=element,
                                                   check_name=byte_check_name,
                                                   check=byte_check)
            raise pydmap_exceptions.MismatchByteError(self.dmap_file,
                                                      element_info,
                                                      self.cursor)

    def check_data_type(self, data_type: int, data_name: str):
        """
        Check if the data_type is a DMAP data type.

        Parameter
        ----------
        data_type : int
            Data_type read in by the byte array
        data_name : str
            Name of the data trying to read in

        Raises
        -------
        DmapDataTypeError
            if the data_type is not in the DMAP_DATA_TYPES dictionary
        """
        if data_type not in DMAP_DATA_TYPES.keys():
            raise pydmap_exceptions.DmapDataTypeError(self.dmap_file,
                                                      data_name,
                                                      data_type,
                                                      self.cursor)

    def test_initial_data_integrity(self):
        """
        Quick method for testing the integrity of the dmap data.

        Raises
        ------
        CursorError
            If the cursor is not set to an expected value.
        DmapDataError
            If the data is corrupted by some byte offset.

        See Also
        --------
        zero_check : raises ZeroByteError
        byte_check : raises MistmatchByteError
        """
        pydarn_logger.debug("Testing the integrity of the dmap file/stream")
        total_block_size = 0  # unit of bytes
        if self.cursor != 0:
            raise pydmap_exceptions.CursorError(self.cursor, 0)

        while self.cursor < self.dmap_end_bytes:
            """
            DMAP files headers contain the following:
                - encoding identifier: is a unique 32-bit integer that
                  indicates how the block was constructed.
                  It is used to differentiate between the possible future
                  changes to the DataMap format.
                - block size: 32-bit integer that represents the total size of
                  block including the header and the data.
                - Number of Scalars: number of scalar variables
                - Scalar data: the scalar data of the record.
                  Please see DmapScalar for more information on scalars.
                - Number of arrays: number of array variables
                  Please see DmapArray for more information on arrays.
            """
            # This is an unused variable but is need to move the cursor to the
            # next offset.
            # TODO: Possible check that uses the encoding identifier
            # encoding_identifier = self.read_data('i',4)
            self.cursor += 4
            block_size = self.read_data('i', 4)
            self.zero_negative_check(block_size, "block size")

            total_block_size += block_size
            self.bytes_check(total_block_size, "total block size",
                             self.dmap_end_bytes, "total bytes in file")

            # 2 is to include the encoding_identifier and size of data which
            # are both int types.
            self.cursor = self.cursor + block_size - 2 *\
                    DMAP_DATA_TYPES[INT][1]

        if total_block_size != self.dmap_end_bytes:
            message = "Error: Initial integrity check shows"\
                    " total block size: {total_size} < end bytes {end_bytes}."\
                    " Cursor: {cursor}."\
                    " Data is likely corrupted"\
                    "".format(total_size=total_block_size,
                              end_bytes=self.dmap_end_bytes,
                              cursor=self.cursor)
            raise pydmap_exceptions.DmapDataError(self.data_file, message)
        self.cursor = 0

    def read_records(self) -> collections.deque:
        """
        This method reads the records from the dmap file/stream passed
        into the instance.


        Return
        -------
        __dmap_records : collections.Deque
                Deque list of DmapRecords (ordered dictionary)


        See Also
        --------
        DmapRecord : dmap record's data structure
        DmapScalar : dmap record's scalar data structure
        DmapArray  : dmap record's array data structure

        See DEVELOPER_README.md for more information on
        DmapRecords data structure.
        """

        # read bytes until end of byte array
        pydarn_logger.debug("Reading DMAP records")
        while self.cursor < self.dmap_end_bytes:
            new_record = self.read_record()
            self.__dmap_records.append(new_record)

        self.bytes_check(self.cursor, "cursor",
                         self.dmap_end_bytes, "total bytes in the file")
        return self.__dmap_records

    def read_record(self) -> collections.OrderedDict:
        """
        Reads a single dmap record from the byte array.

        Return
        ------
        Ordered dict:
                Ordered dictionary containing DmapScalars and DmapArrays from
                a dmap array. The key is the name of the scalar/array and
                value is the DmapScalar/DmapArray data structure

        Raises
        ------
        CursorError
           if the beginning value of the cursor -
           the current position != block size

        See Also
        --------
        read_scalar : reads dmap scalars to be stored in the record
        read_array : reads dmap arrays to be stored in the record
        """
        # used in a cursor check.
        start_cursor_value = self.cursor

        # Need to get encoder for cursor movement though it is not moved.
        # encoding_identifier = self.read_data('i',4)
        # WARNING: normally would call encoding_identifier but since it is not
        # used the extra function call is point less so best just to move the
        # cursor for performance :)
        self.cursor += 4
        block_size = self.read_data('i', 4)

        pydarn_logger.debug("Reading Record {record}"
                            .format(record=len(self.__dmap_records)))

        # adding 8 bytes because code+size are part of the record.
        # 4 is the number bytes for int format
        remaining_bytes = self.dmap_end_bytes - self.cursor + 2 *\
                DMAP_DATA_TYPES[INT][1]
        self.bytes_check(block_size, "block size",
                         remaining_bytes, "remaining bytes")
        self.zero_negative_check(block_size, "block size")

        num_scalars = self.read_data('i', 4)
        num_arrays = self.read_data('i', 4)

        self.zero_negative_check(num_scalars, "number of scalars")
        self.zero_negative_check(num_arrays, "number of arrays")
        self.bytes_check(num_scalars + num_arrays,
                         "number of scalars + arrays",
                         block_size, "block size")

        pydarn_logger.debug("Reading record: reading scalars\n")
        # originally called DmapRecord but then was just returning the ordered
        # dict thus I am constructing it here instead
        # for better speed performance.
        record = collections.OrderedDict()
        for i in range(num_scalars):
            scalar = self.read_scalar()
            record[scalar.name] = scalar

        pydarn_logger.debug("Reading record: reading arrays\n")
        for i in range(num_arrays):
            array = self.read_array(block_size)
            record[array.name] = array

        # check for a cursor error
        if (self.cursor - start_cursor_value) != block_size:
            raise pydmap_exceptions.CursorError(self.cursor, block_size)

        return record

    def read_scalar(self) -> DmapScalar:
        """
        Reads a scalar and stores the properties into a namedtuple DmapScalar.

        Return
        ------
        DmapScalar: namedtuple
            data structure that contains the data properties of
            the scalar read in

        Raises
        ------
        DmapDataError
            if the data type format is DMAP
            NOTE: In RST, this is allowed, if an example shows up where this is
            allowed DMAP files raise as an issue in the GitHub so the code can
            be re-accessed.

        See Also
        --------
        check_data_type : for other possible raised exceptions
        read_data : reads the data stored in the byte array
        """

        # String and char have a byte size of 1
        scalar_name = self.read_data('s', 1)
        scalar_type = self.read_data('c', 1)

        self.check_data_type(scalar_type, scalar_name)

        scalar_type_fmt = DMAP_DATA_TYPES[scalar_type][0]
        scalar_fmt_byte = DMAP_DATA_TYPES[scalar_type][1]

        if scalar_type_fmt != DMAP:
            scalar_value = self.read_data(scalar_type_fmt, scalar_fmt_byte)
        else:
            message = "Error: Trying to read DMAP data type for a scalar."\
                    " cursor at {}".format(self.cursor)
            # Not sure when this is used in a dmap file
            # so better to raise an error if used re-access the code.
            raise pydmap_exceptions.DmapDataError(self.dmap_file, message)

        return DmapScalar(scalar_name, scalar_value,
                          scalar_type, scalar_type_fmt)

    def read_array(self, record_size) -> DmapArray:
        """
        Reads an array from a dmap record the byte arrays and
        stores the data properties in a DmapArray structure.

        Return
        ------
        DmapArray : namedtuple
             data structure that contains the data properties of
             the array read in.

        Raises
        -------
            DmapDataError
                if the array properties (like a dimension size == 0)
                are incorrect.

        See Also
        --------
        read_data : reads the data in the byte array
        read_numerical_array : reads in a numerical array from the byte array
        read_string_array: reads in a string/DMAP array
        """
        array_name = self.read_data('s', 1)
        array_type = self.read_data('c', 1)

        self.check_data_type(array_type, array_name)

        array_type_fmt = DMAP_DATA_TYPES[array_type][0]
        array_fmt_bytes = DMAP_DATA_TYPES[array_type][1]

        array_dimension = self.read_data('i', 4)
        self.bytes_check(array_dimension, "array dimension",
                         record_size, "record size")
        self.zero_negative_check(array_dimension, "array dimension")

        array_shape = [self.read_data('i', 4)
                       for i in range(0, array_dimension)]
        array_shape.reverse()

        # if shape list is empty
        if len(array_shape) != array_dimension:
            message = "Error: Array shape {shape} could not be read."\
                    " cursor: {cursor}".format(shape=array_shape,
                                               cursor=self.cursor)
            raise pydmap_exceptions.DmapDataError(self.dmap_file, message)
        # slist is the array that holds the range gates that have valid data
        # when qflg is 1
        elif any(x <= 0 for x in array_shape) and array_name != "slist":
            message = "Error: Array shape {shape} contains "\
                    "dimension size <= 0."\
                    " Cursor: {cursor}".format(dim=array_shape,
                                               cursor=self.cursor)
            raise pydmap_exceptions.DmapDataError(self.filename, message)

        for i in range(array_dimension):
            if array_shape[i] >= record_size:
                message = "Error: Array {index}-dimension size {size}"\
                        " exceeds record size: {rec_size}."\
                        "".format(index=i,
                                  size=array_shape[i],
                                  rec_size=record_size)
                raise pydmap_exceptions.DmapDataError(self.dmap_file, message)

        # We could use np.prod(array_shape) but the for loop has a better
        # time performance. Note: cells can also be read as number of elements
        # depending on your background.
        total_num_cells = 1
        for i in array_shape:
            total_num_cells *= i
        self.bytes_check(total_num_cells, "total number of cells",
                         record_size, "record size")

        total_num_cells_bytes = total_num_cells * array_fmt_bytes
        self.bytes_check(total_num_cells_bytes,
                         "total number of cells in bytes",
                         record_size, "record size")

        # parsing an array of strings requires a different method. Numpy can't
        # parse strings or dmaps into arrays the way it can for other
        # types because it doesn't
        # know the sizes. They have to be manually read the slow way.
        # Because chars
        # are encoded as hex literals, they have to be read one at a
        # time to make sense.

        if array_type_fmt == 's' or array_type_fmt == 'c':
            array_value = self.read_string_array(array_shape,
                                                 array_type_fmt,
                                                 array_fmt_bytes)
        elif array_type == DMAP:
            message = "Error: Trying to read DMAP array data type."\
                    " cursor at {}".format(self.cursor)
            # Not sure when this is used in a dmap file
            # so better to raise an error if used re-access the code.
            raise pydmap_exceptions.DmapDataError(self.dmap_file, message)
        else:
            array_value = self.read_numerical_array(array_type_fmt,
                                                    total_num_cells,
                                                    array_fmt_bytes)

        return DmapArray(array_name, array_value, array_type, array_type_fmt,
                         array_dimension, array_shape)

    def read_data(self, data_type_fmt: str, data_fmt_bytes: int):
        """
        Reads in individual data type from the byte array
        Given a dmap data type.

        Parameter
        ---------
        data_type : int
            dmap data type numerical value for knowing how many bytes to read.

        Return
        ------
        data : data_type
            returns the data that was store in the byte array.
            Has the data type of the dmap data type passed in.

        Raises
        ------
        CursorError
            if cursor is not correctly aligned or at the correct position.
        DmapDataError
            if trying to read a DMAP data type

        See Also
        --------
        Struct.unpack : converts the bytes array values from a C structure to
        python objects

        See DEVELOPER_README.md for more information on DMAP data types and
        Struct.unpack.
        """
        if self.cursor >= self.dmap_end_bytes:
            message = "Error: Cursor {cursor} extends"\
                    " out of buffer {end_bytes}."\
                    "".format(cursor=self.cursor,
                              end_bytes=self.dmap_end_bytes)
            raise pydmap_exceptions.CursorError(self.cursor, message=message)

        cursor_offset = self.dmap_end_bytes - self.cursor
        if cursor_offset < data_fmt_bytes:
            message = "Error: Byte offsets {offset} into buffer {fmt}"\
                    " are not aligned.".format(offset=cursor_offset,
                                               fmt=data_fmt_bytes)
            raise pydmap_exceptions.CursorError(self.cursor, message=message)

        # struct.unpack is a python method the converts C struct
        # as python bytes to python values. See DEVELOPER_README.md
        # for more information.
        # TODO: how to handle this gracefully? Return None and check later than
        #       continue in the loop?
        if data_type_fmt == 'c':
            data = self.dmap_bytearr[self.cursor]
            self.cursor += data_fmt_bytes
            return data
        elif data_type_fmt == 's':
            byte_counter = 0
            while self.dmap_bytearr[self.cursor + byte_counter] != 0 or \
                    self.cursor + byte_counter >= self.dmap_end_bytes:
                # add 1 byte to byte_counter because
                # a string is a list of chars
                byte_counter += 1  # 1 is the number of bytes of a char

            self.bytes_check(self.cursor+byte_counter, 'cursor',
                             self.dmap_end_bytes, 'Total number of Bytes')

            # format byte counter to a string format for unpacking
            # WARNING: not using format for performance purposes
            char_count = '%ss' % byte_counter
            data = struct.unpack_from(char_count,
                                      self.dmap_buffer,
                                      self.cursor)
            # 1 is the number of bytes in a char
            self.cursor = self.cursor + byte_counter + 1
            return data[0].decode('utf-8')
        else:
            data = struct.unpack_from(data_type_fmt,
                                      self.dmap_buffer,
                                      self.cursor)
            self.cursor += data_fmt_bytes
            return data[0]

    def read_string_array(self, shape: list,
                          array_type_fmt: str,
                          array_fmt_bytes: int) -> np.ndarray:
        """
        Reads and builds a N-D array of string data types.

        Parameter
        ---------
        shape : list
            list of the arrays dimension size
        array_fmt_bytes : int
            String or char

        Return
        ------
        np.ndarray
            an numpy N-D array of string read in from the byte array
        """

        data = []
        # FIXME: still need to find a method for testing this... Or a file
        #        that contains a string/DMAP array
        for dim_size in shape:
            for i in range(dim_size):
                data.append(self.read_data(array_type_fmt, array_fmt_bytes))
        # try to avoid using recursion, it is slow
        # if not dim:
        #     dim_data = [self.read_data(data_type_fmt)
        #                 for i in range(0, dimension)]
        # else:
        #     dim_data = [self.build_n_dimension_list(list(dim), data_type_fmt)
        #                 for i in range(0, dimension)]
        return np.array(data)

    def read_numerical_array(self, data_type_fmt: str,
                             total_number_cells: int,
                             data_fmt_bytes: int) -> np.ndarray:
        """
        Reads in an array from the byte array into a N-D array.

        Parameter
        ---------
        shape : list
            A list of the array's dimension sizes
        data_type : int
            DMAP data type numeric value
        total_number_cells : int
            The number of cells in the N-D array being read in

        Return
        -------
        array : np.ndarray
            The numpy N-D array from the byte array

        Raises
        -------
        DmapDataError
            Mismatch on the data type and the size specified in the byte array.
        """
        array = np.frombuffer(self.dmap_buffer, data_type_fmt,
                              total_number_cells, self.cursor)
        self.cursor += total_number_cells * data_fmt_bytes

        return array


class DmapWrite(object):
    """
    Writes Dmap records to file or stream and writes SuperDARN file format.
    ...

    Attributes
    -----------
    dmap_records : List[dict]
        List of dmap records
    filename : str
        Name of the file the user wants to write to
    dmap_bytearr : bytearray
        Byte array representing the dmap records in bytes

    Methods
    -------
    write_iqdat(filename)
        Writes dmap records to SuperDARN IQDAT file structure
        with the given filename
    write_fitacf(filename)
        Write dmap records to SuperDARN RAWACF file structure
        with the given filename
    write_rawacf(filename)
        Writes dmap records to SuperDARN FITACF file structure
        with the given filename
    write_grid(filename)
        Writes dmap records to SuperDARN GRID file structure
        with the given filename
    write_map(filename)
        Writes dmap records to SuperDARN MAP file structure
        with the given filename
    write_dmap(filename)
        Writes dmap records to DMAP format with the given filename
    write_dmap_stream(dmap_records)
        Writes dmap records to DMAP format byte stream
    dict_key_diff(dict1, dict2)
        Returns a set of the difference between dict1 and dict2 keys
    missing_field_check(file_struct_list, record, rec_num)
        Checks if there is any missing fields in the record from a list of possible file fields
    extra_field_check(file_struct_list, record, rec_num)
        Checks if there is any extra fields in the record from a list of possible file fields
    incorrect_types_check(file_struct_list, record)
        Checks if there is any incorrect types in the record from a list of possible file
        fields and their data type formats
    dict_list2set(dict_list)
        Converts a list of dictionaries to a set containing their keys
    SuperDARN_file_structure_to_bytes(file_struct_list)
        Converts dmap records to SuperDARN file structure bytes based on file_struct_list
    dmap_records_to_bytes()
        Converts dmap records to byte array stored in dmap_bytearr
    dmap_scalar_to_bytes(scalar)
        Converts a DmapScalar to bytes
    dmap_array_to_bytes(array)
        Converts a DmapArray to bytes
    """
    def __init__(self, dmap_records: List[dict] = [], filename: str = "",
                 dmap_file_fmt: str = ""):
        """
        Writes dmap records to a given filename of byte array in DMAP format, this includes the
        following SuperDARN file types:
                                - Iqdat
                                - Rawacf
                                - Fitacf
                                - Grid
                                - Map

        Parameters
        ----------
        dmap_records : List[dict]
            list of dictionaries representing a list of dmap records containing DmapScalar and DmapArrays
        filename : str
            The path and name of the file the user wants to write to
        dmap_file_fmt : str
            Dmap file types, the following are supported:
                                                    - 'iqdat' : SuperDARN file type
                                                    - 'rawacf' : SuperDARN file type
                                                    - 'fitacf' : SuperDARN file type
                                                    - 'grid' : SuperDARN file type
                                                    - 'map' : SuperDARN file type
                                                    - 'dmap' : writes a file in DMAP format
                                                    - 'stream' : writing to dmap data stream

        Raises
        ------
        SuperDARNFileExtra
        SuperDARNFormatError
        DmapTypeError
        SuperDARNFieldMissing
        DmapFileFormatType
        FilenameRequiredError
        """
        self.dmap_records = dmap_records
        self.dmap_bytearr = bytearray()
        self.filename = filename

        if dmap_file_fmt is "":
            pass
        elif dmap_file_fmt == "iqdat":
            self.write_iqdat()
        elif dmap_file_fmt == "rawacf":
            self.write_rawacf()
        elif dmap_file_fmt == "fitacf":
            self.write_fitacf()
        elif dmap_file_fmt == "grid":
            self.write_grid()
        elif dmap_file_fmt == "map":
            self.write_map()
        elif dmap_file_fmt == "dmap":
            self.write_dmap()
        elif dmap_file_fmt == "stream":
            self.write_dmap_stream()
        else:
            raise pydmap_exceptions.DmapFileFormatType(dmap_file_fmt,
                                                       self.filename)

    # Methods are used and strings for versatility amongst users
    # some prefer string input some rather not due to typos :)
    def write_iqdat(self, filename: str = ""):
        """
        Writes SuperDARN file type IQDAT

        Parameters:
        -----------
        filename : str
            The name of the IQDAT file including path


        Raises:
        -------
        superDARNFieldExtra - if there is an extra field
        SuperDARNFieldMissing - if there is an missing field
        SuperDARNFormatError - if there is a formatting error
                               like an incorrect data type format

        See Also:
        ---------
        extra_field_check
        missing_field_check
        superdarn_formats.Iqdat - module contain the data types
                                 in each SuperDARN files types
        """
        self.__empty_record_check()
        self.__filename_check(filename)
        file_struct_list = [superdarn_formats.Iqdat.types]
        self.superDARN_file_structure_to_bytes(file_struct_list)
        with open(self.filename, 'wb') as f:
            f.write(self.dmap_bytearr)

    def write_rawacf(self, filename: str = ""):
        """
        Writes SuperDARN file type RAWACF

        Parameters:
        -----------
        filename : str
            The name of the RAWACF file including path


        Raises:
        -------
        superDARNFieldExtra - if there is an extra field
        SuperDARNFieldMissing - if there is an missing field
        SuperDARNFormatError - if there is a formatting error
                               like an incorrect data type format

        See Also:
        ---------
        extra_field_check
        missing_field_check
        superdarn_formats.Rawacf - module contain the data types
                                 in each SuperDARN files types
        """
        self.__empty_record_check()
        self.__filename_check(filename)
        file_struct_list = [superdarn_formats.Rawacf.types]
        self.superDARN_file_structure_to_bytes(file_struct_list)
        with open(self.filename, 'wb') as f:
            f.write(self.dmap_bytearr)

    def write_rawacf_stream(self, rawacf_data: List[dict] = []) -> bytearray:
        if rawacf_data != []:
            self.dmap_records = rawacf_data
        self.__empty_record_check()
        file_struct_list = [superdarn_formats.Rawacf.types]
        self.superDARN_file_structure_to_bytes(file_struct_list)
        return self.dmap_bytearr

    def write_fitacf(self, filename=""):
        """
        Writes SuperDARN file type FITACF

        Parameters:
        -----------
        filename : str
            The name of the FITACF file including path


        Raises:
        -------
        superDARNFieldExtra - if there is an extra field
        SuperDARNFieldMissing - if there is an missing field
        SuperDARNFormatError - if there is a formatting error
                               like an incorrect data type format

        See Also:
        ---------
        extra_field_check
        missing_field_check
        superdarn_formats.Fitacf - module contain the data types
                                 in each SuperDARN files types
        """
        self.__empty_record_check()
        self.__filename_check(filename)
        file_struct_list = [superdarn_formats.Fitacf.types]
        self.superDARN_file_structure_to_bytes(file_struct_list)
        with open(self.filename, 'wb') as f:
            f.write(self.dmap_bytearr)

    def write_fitacf_stream(self, fitacf_data: List[dict] = []) -> bytearray:
        if fitacf_data != []:
            self.dmap_records = fitacf_data
        self.__empty_record_check()
        file_struct_list = [superdarn_formats.Fitacf.types]
        self.superDARN_file_structure_to_bytes(file_struct_list)
        return self.dmap_bytearr

    def write_grid(self, filename=""):
        """
        Writes SuperDARN file type GRID

        Parameters:
        -----------
        filename : str
            The name of the GRID file including path


        Raises:
        -------
        superDARNFieldExtra - if there is an extra field
        SuperDARNFieldMissing - if there is an missing field
        SuperDARNFormatError - if there is a formatting error
                               like an incorrect data type format

        See Also:
        ---------
        extra_field_check
        missing_field_check
        superdarn_formats.Grid - module contain the data types
                                 in each SuperDARN files types
        """
        self.__empty_record_check()
        self.__filename_check(filename)
        # Grid files can have extra fields based on how they are processed.
        # If the command line option used in make_grid (See RST documentation)
        # uses the command line option -ext then power and spectral width fields
        # are included as well.
        file_struct_list = [superdarn_formats.Grid.types,
                            superdarn_formats.Grid.extra_fields]
        self.superDARN_file_structure_to_bytes(file_struct_list)
        with open(self.filename, 'wb') as f:
            f.write(self.dmap_bytearr)

    def write_grid_stream(self, grid_data: List[dict] = []) -> bytearray:
        if grid_data != []:
            self.dmap_records = grid_data
        self.__empty_record_check()
        file_struct_list = [superdarn_formats.Grid.types,
                            superdarn_formats.Grid.extra_fields]
        self.superDARN_file_structure_to_bytes(file_struct_list)
        return self.dmap_bytearr

    def write_map(self, filename=""):
        """
        Writes SuperDARN file type MAP

        Parameters:
        -----------
        filename : str
            The name of the MAP file including path


        Raises:
        -------
        superDARNFieldExtra - if there is an extra field
        SuperDARNFieldMissing - if there is an missing field
        SuperDARNFormatError - if there is a formatting error
                               like an incorrect data type format

        See Also:
        ---------
        extra_field_check
        missing_field_check
        superdarn_formats.Map - module contain the data types
                                 in each SuperDARN files types
        """
        self.__empty_record_check()
        self.__filename_check(filename)
        # Map files can have extra fields based on how they are processed.
        # If the command line option map_grid -ext (See RST documentation) is
        # used then power and spectral width is included into the fields.
        # Other fields are also included on which map_add<methods> are used on
        # the map file processing.
        file_struct_list = [superdarn_formats.Map.types,
                            superdarn_formats.Map.extra_fields,
                            superdarn_formats.Map.fit_fields,
                            superdarn_formats.Map.model_fields,
                            superdarn_formats.Map.hmb_fields]
        self.superDARN_file_structure_to_bytes(file_struct_list)
        with open(self.filename, 'wb') as f:
            f.write(self.dmap_bytearr)

    def write_map_stream(self, map_data: List[dict] = []) -> bytearray:
        if map_data != []:
            self.dmap_records = map_data
        self.__empty_record_check()
        file_struct_list = [superdarn_formats.Map.types,
                            superdarn_formats.Map.extra_fields,
                            superdarn_formats.Map.fit_fields,
                            superdarn_formats.Map.model_fields,
                            superdarn_formats.Map.hmb_fields]
        self.superDARN_file_structure_to_bytes(file_struct_list)
        return self.dmap_bytearr

    # HONEY BADGER method: Because dmap just don't care
    def write_dmap(self, filename=""):
        """
        Writes dmap record to dmap file format.

        Parameters:
        -----------
        filename : str
            The name of the DMAP file including path

        WARNING:
        --------
        No checks are done, this up to the user to ensure their fields are
        correct.
        """
        self.__empty_record_check()
        self.__filename_check(filename)
        self.dmap_records_to_bytes()
        with open(self.filename, 'wb') as f:
            f.write(self.dmap_bytearr)

    def write_dmap_stream(self, dmap_records: List[dict] = []) -> bytearray:
        """
        Writes dmap record to dmap file format.

        Return
        ------
        dmap_bytearr : bytearray
            Bytearray of the dmap records

        WARNING:
        --------
        No checks are done, this up to the user to ensure their fields are
        correct.
        """
        if self.dmap_records == []:
            self.dmap_records = dmap_records
        self.__empty_record_check()
        self.dmap_records_to_bytes()
        return self.dmap_bytearr

    def __empty_record_check(self):
        if self.dmap_records == []:
            raise pydmap_exceptions.DmapDataError(self.filename,
                                                  "Dmap record is empty "
                                                  "there is nothing to write.")



    def __filename_check(self, filename: str = ""):
        """
        Checks if a filename is given and overrides the current
        filename with the new one.

        Parameter:
        ----------
        filename : str
            Name of the file to write to

        Raises:
        ------
        FilenameRequireError - raised if no filename is given
        """
        if self.filename == "" and filename == "":
            raise pydmap_exceptions.FilenameRequiredError()
        elif filename != "":
            self.filename = filename

    # TODO: may move this to a utility class for future use
    def dict_key_diff(self, dict1: Union[dict, set],
                      dict2: Union[dict, set]) -> set:
        """
        Determines the difference in the key set from the first dictionary to the second dictionary.
        ex) Let A = {a, b, c} and B = {d, a, b}
        Then A - B = {c}

        Parameters:
        -----------
        dict1 : dict or set
            dictionary or set to subtract from
        dict2 : dict or set
            dictionary or set subtracting from dict1

        Return:
        ------
        dict_diff : set
            difference between dict1 and dict2 keys or the sets
        """
        diff_dict = set(dict1) - set(dict2)
        return diff_dict

    # TODO: might be moved to utility class as a static method
    # Also, might not be needed if we do not use the data types
    # in the structure  dictionaries
    def dict_list2set(self, dict_list: List[dict]) -> set:
        """
        Converts a list of dictionaries to list of sets

        Parameters:
        -----------
        dict_list : list
            list of dictionaries

        Return:
        ------
        complete_set : set
            set containing all dictionary key from the list of dicts
        """
        # convert dictionaries to set to do some set magic
        sets = [set(dic) for dic in dict_list]  # TODO: if data types don't matter in the structure format then they can become sets instead of dictionaries.
        # create a complete set list
        complete_set = set.union(*sets)
        return complete_set

    def missing_field_check(self, file_struct_list: List[dict],
                            record: dict, rec_num: int):
        """
        Checks if any fields are missing from the record compared to the file
        structure.

        Parameters:
        -----------
        file_struct_list : List[dict]
            List of dictionaries for the possible file structure fields
        record : dict
            Dictionary representing the dmap record
        rec_num : int
            Record number for better error message information

        Raises:
        -------
        SuperDARNFieldMissing
        """
        # Needed to get the intersection between the record and complete
        # file structure types
        complete_set = self.dict_list2set(file_struct_list)
        missing_fields = set()
        for file_struct in file_struct_list:
            # An intersection of a set returns what both sets have in common
            # then comparing the difference from the subset of types
            # you can determine what is missing.
            diff_fields = self.dict_key_diff(file_struct,
                                          set(record).
                                          intersection(complete_set))
            # For Grid and Map files this is needed because depending
            # on command line options to generate the grid and map files
            # some fields are added in.
            # If 0 nothing missing, if len(file_struct) then
            # that subset is missing only meaning that command option was
            # not used, not necessarily meaning that it is a record.
            if len(diff_fields) not in (0, len(file_struct)):
                missing_fields = missing_fields.union(diff_fields)

        if len(missing_fields) > 0:
            raise pydmap_exceptions.SuperDARNFieldMissing(self.filename,
                                                          rec_num,
                                                          missing_fields)

    def extra_field_check(self, file_struct_list: List[dict],
                          record: dict, rec_num: int):
        """
        Check if there is an extra field in the file structure list and record.

        Parameters
        -----------
        file_struct_list : List[dict]
            List of dictionary representing the possible fields
            in file structure
        record : dict
            Dmap record
        rec_num : int
            Record number for better error message information

        Raises
        -------
        SuperDARNFieldExtra

        """
        file_struct = self.dict_list2set(file_struct_list)
        extra_fields = self.dict_key_diff(record, file_struct)

        if len(extra_fields) > 0:
            raise pydmap_exceptions.SuperDARNFieldExtra(self.filename,
                                                        rec_num,
                                                        extra_fields)

    # TODO: Do we want to check this? If not, then change SuperDARN_format_structure types to sets to get rid of dict_list2set method.
    def incorrect_types_check(self, file_struct_list: List[dict], record: dict, rec_num: int):
        """
        Checks if the file structure fields data type formats are correct
        in the record.

        Parameters
        ----------
        file_struct_list : List[dict]
            List of dictionaries representing the possible fields
            in a file structure
        record : dict
            Dmap record
        rec_num : int
            Record number for a better error message information

        Raises
        ------
        SuperDARNFileFormatError
        """
        complete_dict = {}
        for file_struct in file_struct_list:
            complete_dict.update(file_struct)
        incorrect_types_check = {param: complete_dict[param] for param in record.keys() if record[param].data_type_fmt != complete_dict[param]}
        if len(incorrect_types_check) > 0:
            raise pydmap_exceptions.SuperDARNDataFormatError(incorrect_types_check,
                                                             rec_num)

    def superDARN_file_structure_to_bytes(self, file_struct_list: List[dict]):
        # TODO: might make rec_num a field in the class as it may be
        # useful in error messages for both DmapRead and DmapWrite
        for rec_num in range(len(self.dmap_records)):
            record = self.dmap_records[rec_num]
            # field checks
            self.extra_field_check(file_struct_list, record, rec_num)
            self.missing_field_check(file_struct_list, record, rec_num)
            self.incorrect_types_check(file_struct_list, record, rec_num)
            # start converting
            self.__dmap_record_to_bytes(record)

    def dmap_records_to_bytes(self):
        """
        Loops through the dmap records and calls dmap_record_to_bytes
        to convert the dmap records to a byte array.

        Future use of this function is for parallelization.
        """
        for record in self.dmap_records:
            self.__dmap_record_to_bytes(record)

    def __dmap_record_to_bytes(self, record: dict):
        """
        Converts dmap record to byte stream and stores in the
        dmap byte array

        Parameter
        ---------
        record : dict
            Dmap record

        Notes
        -----
        Might be useful to return bytes of records for potential
        writing into a data stream or real-time stream
        """

        encoding_identifier = 65537  # TODO: determine where this is documented for reference
        num_scalars = 0
        num_arrays = 0
        data_bytearray = bytearray()
        for name, data_info in record.items():
            if isinstance(data_info, DmapScalar):
                data_bytearray.extend(self.dmap_scalar_to_bytes(data_info))
                num_scalars += 1
            elif isinstance(data_info, DmapArray):
                data_bytearray.extend(self.dmap_array_to_bytes(data_info))
                num_arrays += 1
            else:
                raise pydmap_exceptions.DmapTypeError(self.filename,
                                                      type(data_info))

        # 16 = encoding_identifier (int - 4 bytes) + num_scalars (int - 4) +
        #      num_arrays (int - 4) + size of the block (int - 4)
        block_size = len(data_bytearray) + 16

        # TODO: potential performance increase by saving the extend object
        self.dmap_bytearr.extend(struct.pack('i', encoding_identifier))
        self.dmap_bytearr.extend(struct.pack('i', block_size))
        self.dmap_bytearr.extend(struct.pack('i', num_scalars))
        self.dmap_bytearr.extend(struct.pack('i', num_arrays))
        self.dmap_bytearr.extend(data_bytearray)

    def dmap_scalar_to_bytes(self, scalar: DmapScalar) -> bytes:
        """
        Converts a DmapScalar to byte format.
        Byte format: name, data type, data

        Parameter
        ---------
        scalar : DmapScalar
            Dmap scalar to be convert into byte format

        Return
        ------
        scalar_total_bytes : bytes
            Bytes of the scalar
        """

        scalar_name = "{0}\0".format(scalar.name)
        scalar_name_format = '{0}s'.format(len(scalar_name))
        scalar_name_bytes = struct.pack(scalar_name_format,
                                        scalar_name.encode('utf-8'))

        scalar_type_bytes = struct.pack('c',
                                        chr(scalar.data_type).encode('utf-8'))
        scalar_type_fmt = scalar.data_type_fmt

        if scalar_type_fmt == 's':
            scalar_data = "{0}\0".format(scalar.value)
            scalar_data_format = '{0}s'.format(len(scalar_data))
            scalar_data_bytes = struct.pack(scalar_data_format,
                                            scalar_data.encode('utf-8'))
        elif scalar_type_fmt == 'c':
            scalar_data_bytes = chr(scalar.value).encode('utf-8')
        else:
            scalar_data_bytes = struct.pack(scalar_type_fmt, scalar.value)

        scalar_total_bytes = scalar_name_bytes + scalar_type_bytes +\
            scalar_data_bytes

        return scalar_total_bytes

    def dmap_array_to_bytes(self, array: DmapArray) -> bytes:
        """
        Converts a DmapArray to the byte format.

        Byte format: name, data type, dimension, shape, data

        Parameter
        ---------
        array : DmapArray
            Dmap array to be converted to bytes

        Return
        -------
        array_total_bytes : bytes
            Total bytes of the array
        """

        array_name = "{0}\0".format(array.name)
        array_name_format = '{0}s'.format(len(array_name))
        array_name_bytes = struct.pack(array_name_format,
                                       array_name.encode('utf-8'))

        array_type_bytes = struct.pack('c',
                                       chr(array.data_type).encode('utf-8'))

        array_dim_bytes = struct.pack('i', array.dimension)
        array_shape_bytes = bytes()
        for size in array.shape:
            array_shape_bytes += struct.pack('i', size)

        array_data_bytes = array.value.tostring()

        array_total_bytes = array_name_bytes + array_type_bytes + \
            array_dim_bytes + array_shape_bytes + array_data_bytes

        return array_total_bytes
