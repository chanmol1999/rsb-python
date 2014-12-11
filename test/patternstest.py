# ============================================================
#
# Copyright (C) 2011, 2012, 2014 Jan Moringen <jmoringe@techfak.uni-bielefeld.DE>
#
# This file may be licensed under the terms of the
# GNU Lesser General Public License Version 3 (the ``LGPL''),
# or (at your option) any later version.
#
# Software distributed under the License is distributed
# on an ``AS IS'' basis, WITHOUT WARRANTY OF ANY KIND, either
# express or implied. See the LGPL for the specific language
# governing rights and limitations.
#
# You should have received a copy of the LGPL along with this
# program. If not, go to http://www.gnu.org/licenses/lgpl.html
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# The development of this software was supported by:
#   CoR-Lab, Research Institute for Cognition and Robotics
#     Bielefeld University
#
# ============================================================

import unittest
import rsb
from rsb import ParticipantConfig
import time
from threading import Condition

inProcessNoIntrospectionConfig = ParticipantConfig.fromDict({
    'introspection.enabled':        '0',
    'transport.inprocess.enabled' : '1'
})

class LocalServerTest (unittest.TestCase):
    def testConstruction(self):

        # Test creating a server without methods
        with rsb.createServer('/some/scope',
                              inProcessNoIntrospectionConfig) \
            as server:
            self.assertEqual(server.methods, [])

        with rsb.createServer(rsb.Scope('/some/scope'),
                              inProcessNoIntrospectionConfig) \
            as server:
            self.assertEqual(server.methods, [])

        # Test creating a server with directly specified methods
        with rsb.createServer(rsb.Scope('/some/scope'),
                              methods = [ ('foo', lambda x: x, str, str) ],
                              config  = inProcessNoIntrospectionConfig) \
            as server:
            self.assertEqual([ m.name for m in server.methods ], [ 'foo' ])

        # Test creating a server that exposes method of an existing
        # object
        class SomeClass (object):
            def bar(x):
                pass

        someObject = SomeClass()
        with rsb.createServer(rsb.Scope('/some/scope'),
                              object = someObject,
                              expose = [ ('bar', str, None) ],
                              config = inProcessNoIntrospectionConfig) \
            as server:
            self.assertEqual([ m.name for m in server.methods ], [ 'bar' ])

            # Cannot supply expose without object
            self.assertRaises(ValueError,
                              rsb.createServer,
                              '/some/scope',
                              expose  = [ ('bar', str, None) ])

            # Cannot supply these simultaneously
            self.assertRaises(ValueError,
                              rsb.createServer,
                              '/some/scope',
                              object  = someObject,
                              expose  = [ ('bar', str, None) ],
                              methods = [ ('foo', lambda x: x, str, str) ])

class RoundTripTest (unittest.TestCase):
    def testRoundTrip(self):

        with rsb.createServer('/roundtrip',
                              methods = [ ('addone', lambda x: long(x + 1), long, long) ],
                              config  = inProcessNoIntrospectionConfig) \
            as localServer:
            with rsb.createRemoteServer('/roundtrip',
                                        inProcessNoIntrospectionConfig) \
                as remoteServer:

                # Call synchronously
                self.assertEqual(map(remoteServer.addone, range(100)),
                                 range(1, 101))

                # Call asynchronously
                self.assertEqual(map(lambda x: x.get(),
                                     map(remoteServer.addone.async, range(100))),
                                 range(1, 101))

    def testVoidMethods(self):

        with rsb.createServer('/void', inProcessNoIntrospectionConfig) \
             as localServer:
            def nothing(e):
                pass
            localServer.addMethod("nothing", nothing, str)

            with rsb.createRemoteServer('/void',
                                        inProcessNoIntrospectionConfig) \
                 as remoteServer:
                future = remoteServer.nothing.async("test")
                future.get(1)

    def testParallelCallOfOneMethod(self):

        class Counter(object):
            def __init__(self):
                self.value = 0
        maxParallelCalls = Counter()
        currentCalls = []
        callLock = Condition()

        with rsb.createServer('/takesometime',
                              inProcessNoIntrospectionConfig) \
            as localServer:
            def takeSomeTime(e):
                with callLock:
                    currentCalls.append(e)
                    maxParallelCalls.value = max(maxParallelCalls.value, len(currentCalls))
                    callLock.notifyAll()
                time.sleep(2)
                with callLock:
                    currentCalls.remove(e)
                    callLock.notifyAll()
            localServer.addMethod("takeSomeTime", takeSomeTime, str, allowParallelExecution=True)

            with rsb.createRemoteServer('/takesometime',
                                        inProcessNoIntrospectionConfig) \
                as remoteServer:

                remoteServer.takeSomeTime.async("test1")
                remoteServer.takeSomeTime.async("test2")
                remoteServer.takeSomeTime.async("test3")

                numCalled = 0
                with callLock:
                    while maxParallelCalls.value < 3 and numCalled < 5:
                        numCalled = numCalled + 1
                        callLock.wait()
                    if numCalled == 5:
                        self.fail("Impossible to be called in parallel again")
                    else:
                        self.assertEqual(3, maxParallelCalls.value)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(LocalServerTest))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(RoundTripTest))
    return suite
