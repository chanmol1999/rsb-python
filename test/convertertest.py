# Copyright (C) 2011 Jan Moringen
#
# This Program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses>.

import unittest

from rsb.transport.converter import Converter, StringConverter, ConverterMap, UnambiguousConverterMap, PredicateConverterList

class ConflictingStringConverter(Converter):
    def __init__(self):
        Converter.__init__(self, wireType = str, wireSchema = "string", dataType = float)

    def serialize(self, input):
        return str(input)

    def deserialize(self, input):
        return str(input)

class ConverterMapTest(unittest.TestCase):
    def testAddConverter(self):
        map = ConverterMap(str)
        map.addConverter(StringConverter())
        map.addConverter(ConflictingStringConverter())
        self.assertRaises(Exception, map.addConverter, StringConverter())
        map.addConverter(StringConverter(), override = True)

class UnambiguousConverterMapTest(unittest.TestCase):
    def testAddConverter(self):
        map = UnambiguousConverterMap(str)
        map.addConverter(StringConverter())
        self.assertRaises(Exception, map.addConverter, ConflictingStringConverter())
        self.assertRaises(Exception, map.addConverter, ConflictingStringConverter(), True)
        map.addConverter(StringConverter(), override = True)


class PredicateConverterListTest(unittest.TestCase):
    def testAddConverter(self):
        list = PredicateConverterList(str)
        list.addConverter(StringConverter())
        list.addConverter(StringConverter(),
                          wireSchemaPredicate = lambda wireSchema: True)
        list.addConverter(StringConverter(),
                          dataTypePredicate = lambda dataType: True)

    def testGetConverter(self):
        pass

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ConverterMapTest))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(UnambiguousConverterMapTest))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(PredicateConverterListTest))
    return suite
