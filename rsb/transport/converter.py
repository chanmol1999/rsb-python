# ============================================================
#
# Copyright (C) 2010 by Johannes Wienke <jwienke at techfak dot uni-bielefeld dot de>
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation;
# either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# ============================================================

class Converter(object):
    """
    Base class for converters to a certain target type.

    @author: jwienke
    """

    def __init__(self, wireType, dataType, wireSchema):
        """
        Constructor.

        @param wireType: Python type to/from which the converter
                         serializes/deserializes
        @type wireType: type
        @param dataType: Python type of data accepted by the converter
                         for serialization (also Python type of
                         deserialized data)
        @type dataType: type
        @param wireSchema: Wire-schema understood by the converter
                           when deserializing (also wire-schema of
                           data serialized with the converter)
        @type wireSchema: str
        """
        self.__wireType = wireType
        self.__dataType = dataType
        self.__wireSchema = wireSchema

    def getWireType(self):
        '''
        Returns the type of the wire-type to/from this converter
        serializes/deserializes.

        @return: A type object.
        @rtype: type
        '''
        return self.__wireType

    wireType = property(getWireType)

    def getDataType(self):
        '''
        Returns the data type this converter is applicable for.

        @return: A type object.
        @rtype: type
        '''
        return self.__dataType

    dataType = property(getDataType)

    def getWireSchema(self):
        '''
        Returns the name of the wire schema this converter can
        (de)serialize from/to.

        @return: A string designating the wire schema from/to this
                 converter can (de)serialize
        @rtype: str
        '''
        return self.__wireSchema

    wireSchema = property(getWireSchema)

    def serialize(self, input):
        raise NotImplementedError()

    def deserialize(self, input, wireSchema):
        raise NotImplementedError()

class UnknownConverterError(KeyError):
    """
    Raised if a converter for a target type is not available.

    @author: jwienke
    """

    def __init__(self, sourceType, wireSchema):
        KeyError.__init__(self, "No converter from type %s to type %s available" % (sourceType, wireSchema))

class ConverterSelectionStrategy(object):
    """
    This class defines the interface for converter selection strategy
    classes.

    @author: jmoringe
    """
    def hasConverterForWireSchema(self, wireSchema):
        if self._getConverterForWireSchema(wireSchema):
            return True
        else:
            return False

    def getConverterForWireSchema(self, wireSchema):
        converter = self._getConverterForWireSchema(wireSchema)
        if converter:
            return converter
        raise KeyError, wireSchema

    def hasConverterForDataType(self, dataType):
        if self._getConverterForDataType(dataType):
            return True
        else:
            return False

    def getConverterForDataType(self, dataType):
        converter = self._getConverterForDataType(dataType)
        if converter:
            return converter
        raise KeyError, dataType

class ConverterMap(ConverterSelectionStrategy):
    """
    A class managing converters for for a certain target type.

    @author: jwienke
    """

    def __init__(self, wireType):
        self._wireType = wireType
        self._converters = {}

    def getWireType(self):
        return self._wireType

    def addConverter(self, converter, replaceExisting=False):
        key = (converter.getWireSchema(), converter.getDataType())
        if key in self._converters and not replaceExisting:
            raise RuntimeError("There already is a converter with wire-schema `%s' and data-type `%s'"
                               % key)
        self._converters[key] = converter

    def _getConverterForWireSchema(self, wireSchema):
        for ((converterWireSchema, ignored), converter) in self._converters.items():
            if converterWireSchema == wireSchema:
                return converter

    def _getConverterForDataType(self, dataType):
        for ((ignored, converterDataType), converter) in self._converters.items():
            if dataType is converterDataType:
                return converter

    def getConverters(self):
        return self._converters

    def __str__(self):
        s = "ConverterMap(wireType = %s):\n" % self._wireType
        for converter in self._converters.values():
            s = s + ("\t%s <-> %s\n" % (converter.getWireSchema(), converter.getDataType()))
        return s[:-1]

class PredicateConverterList (ConverterMap):
    """
    Objects of this class are used to perform converter selection via
    a chain-of-responsibility strategy.

    A list of predicates and associated converters is
    maintained. Converter selection queries are processed by
    traversing the list and selected the first converter the
    associated predicate of which matches the query wire-schema or
    data-type.

    @author: jmoringe
    """
    def __init__(self, wireType) :
        super(PredicateConverterList, self).__init__(wireType)
        self._list = []

    def addConverter(self, converter,
                     wireSchemaPredicate=None,
                     dataTypePredicate=None,
                     replaceExisting=True):
        if wireSchemaPredicate is None:
            wireSchemaPredicate = lambda wireSchema: wireSchema == converter.getWireSchema()
        if dataTypePredicate is None:
            dataTypePredicate = lambda dataType: dataType == converter.getDataType()
        key = (wireSchemaPredicate, dataTypePredicate)
        self._converters[key] = converter
        self._list.append((key, converter))

    def _getConverterForWireSchema(self, wireSchema):
        for ((predicate, ignored), converter) in self._list:
            if predicate(wireSchema):
                return converter

    def _getConverterForDataType(self, dataType):
        for ((ignored, predicate), converter) in self._list:
            if predicate(dataType):
                return converter

class UnambiguousConverterMap (ConverterMap):
    def __init__(self, wireType):
        super(UnambiguousConverterMap, self).__init__(wireType)

    def addConverter(self, converter, replaceExisting=False):
        for (wireSchema, dataType) in self.getConverters().keys():
            if wireSchema == converter.getWireSchema():
                if dataType == converter.getDataType():
                    super(UnambiguousConverterMap, self).addConverter(converter, replaceExisting)
                else:
                    raise RuntimeError("Trying to register ambiguous converter with data type `%s' for wire-schema `%s' (present converter is for data type `%s')."
                                       % (converter.getDataType(), wireSchema, dataType))
        super(UnambiguousConverterMap, self).addConverter(converter, replaceExisting)

__globalConverterMaps = {}

def registerGlobalConverter(converter, replaceExisting=False):
    """
    Register B{converter} as a globally available converter.

    @param converter: converter to register
    @param replaceExisting: controls whether an existing converter for
                            the same data-type and/or wire-type should
                            be replaced by the new converter. If this
                            is C{False} and such a converter exists,
                            an error is raised.
    """
    if not converter.getWireType() in __globalConverterMaps:
        __globalConverterMaps[converter.getWireType()] = ConverterMap(converter.getWireType())
    __globalConverterMaps[converter.getWireType()].addConverter(converter, replaceExisting)

def getGlobalConverterMap(wireType):
    """
    Get a map with all globally known converters for the desired target
    serialization type.

    @param wireType: python type for target serialization
    @return: converter map constantly updated
    """

    if not wireType in __globalConverterMaps:
        __globalConverterMaps[wireType] = ConverterMap(wireType)
    return __globalConverterMaps[wireType]

# --- converters with bytearray as serialization type ---

class NoneConverter (Converter):
    """
    This converter produces a serialized value that represents
    instances of C{NoneType}.

    Such a converter is required for serializing "results" of RPC
    calls that do not return a value.

    @author: jmoringe
    """
    def __init__(self):
        super(NoneConverter, self).__init__(bytearray, type(None), 'void')

    def serialize(self, input):
        return bytearray(), self.wireSchema

    def deserialize(self, input, wireSchema):
        assert wireSchema == self.wireSchema

        pass

class StringConverter(Converter):
    """
    An converter to serialize strings to bytearrays with a specified encoding

    @author: jwienke
    """

    def __init__(self, wireSchema="utf-8-string", dataType=unicode, encoding="utf_8"):
        Converter.__init__(self, bytearray, dataType, wireSchema)
        self.__encoding = encoding

    def serialize(self, input):
        return bytearray(input.encode(self.__encoding)), self.wireSchema

    def deserialize(self, input, wireSchema):
        type = self.getDataType()
        if type == unicode:
            return type(str(input), self.__encoding)
        elif type == str:
            return str(input)
        else:
            raise ValueError("Inacceptable dataType %s" % type)

class ProtocolBufferConverter(Converter):
    """
    This converter serializes and deserializes objects of protocol
    buffer data-holder classes.

    These data-holder classes are generated by the protocol buffer
    compiler protoc.

    @author: jmoringe
    """
    def __init__(self, messageClass):
        super(ProtocolBufferConverter, self).__init__(bytearray,
                                                      messageClass,
                                                      '.%s' % messageClass.DESCRIPTOR.full_name)

        self.__messageClass = messageClass

    def getMessageClass(self):
        return self.__messageClass

    messageClass = property(getMessageClass)

    def getMessageClassName(self):
        return self.messageClass.DESCRIPTOR.full_name

    def serialize(self, input):
        return bytearray(input.SerializeToString()), self.wireSchema

    def deserialize(self, input, wireSchema):
        assert wireSchema == self.wireSchema

        output = self.messageClass()
        output.ParseFromString(input)
        return output

    def __str__(self):
        return '<%s for %s at %s>' \
            % (type(self).__name__, self.getMessageClassName(), id(self))

    def __repr__(self):
        return str(self)

registerGlobalConverter(StringConverter(wireSchema="utf-8-string", dataType=str, encoding="utf_8"))
registerGlobalConverter(NoneConverter())
