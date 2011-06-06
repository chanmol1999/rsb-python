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

import logging

import rsb.filter
import converter

from Queue import Queue, Empty
from rsb import util
from rsb.util import getLoggerByClass
from threading import RLock

class Port(object):
    """
    Interface for transport-specific ports.

    @author: jwienke
    """

    def __init__(self, wireType, converterMap):
        """
        Creates a new port with a serialization type wireType.

        @param wireType: the type of serialized data used by this port.
        @param converterMap: map of converters to use. If None, the global
                             map of converters for the selected targetType is
                             used
        """

        self.__logger = getLoggerByClass(self.__class__)

        if wireType == None:
            raise ValueError("Wire type must be a class or primitive type, None given")

        self.__logger.debug("Using specified converter map for wire-type %s" % wireType)
        self.__converterMap = converterMap
        assert(self.__converterMap.getWireType() == wireType)
        self.__wireType = wireType

    def getWireType(self):
        """
        Returns the serialization type used for this port.

        @return: python serialization type
        """
        return self.__wireType

    def _getConverterForDataType(self, dataType):
        """
        Returns a converter that can convert the supplied data to the
        wire-type.

        @param dataType: the type of the object for which a suitable
                         converter should returned.
        @return: converter
        @raise KeyError: no converter is available for the supplied data.
        """
        #self.__logger.debug("Searching for converter for data '%s' in map %s" % (data, self.__converterMap))
        return self.__converterMap.getConverterForDataType(dataType)

    def _getConverterForWireSchema(self, wireSchema):
        """
        Returns the converter for the wire-schema.

        @param wireSchema: the wire-schema to or from which the returned converter should convert
        @return: converter
        @raise KeyError: no converter is available for the specified wire-schema
        """
        self.__logger.debug("Searching for converter with wireSchema '%s' in map %s" % (wireSchema, self.__converterMap))
        return self.__converterMap.getConverterForWireSchema(wireSchema)

    def _getConverterMap(self):
        return self.__converterMap

    def activate(self):
        raise NotImplementedError()
    def deactivate(self):
        raise NotImplementedError()
    def publish(self, event):
        """
        Sends the specified event and adapts its meta data instance with the
        actual send time.
        
        @param event: event to send
        """
        raise NotImplementedError()
    def filterNotify(self, filter, action):
        raise NotImplementedError()
    def setQualityOfServiceSpec(self, qos):
        raise NotImplementedError()

    def setObserverAction(self, observerAction):
        """
        Sets the action used by the port to notify about incomming events.
        The call to this method must be thread-safe.

        @param observerAction: action called if a new message is received from
                               the port. Must accept an RSBEvent as parameter.
        """
        pass
