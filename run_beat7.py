#!/usr/bin/env python3.8
"""Wrapper to run beat-localcoin EC2 test"""
import sys
import os

from gevent import monkey
monkey.patch_all()

import atexit
import math
from optparse import OptionParser
from os.path import expanduser

from adaptive.core.utils import initiateThresholdSig, initiateECDSAKeys, initiateThresholdEnc, getKeys, initiateRND
from adaptive.commoncoin.thresprf_gipc import initialize as initializeGIPC
from adaptive.test.honest_party_test_EC2 import client_test_freenet, prepareIPList, exit as _exit_handler

atexit.register(_exit_handler)

parser = OptionParser()
parser.add_option("-e", "--ecdsa-keys", dest="ecdsa")
parser.add_option("-k", "--threshold-keys", dest="threshold_keys")
parser.add_option("-c", "--threshold-enc", dest="threshold_encs")
parser.add_option("-s", "--hosts", dest="hosts", default="~/hosts")
parser.add_option("-n", "--number", dest="n", type="int")
parser.add_option("-b", "--propose-size", dest="B", type="int")
parser.add_option("-t", "--tolerance", dest="t", type="int")
parser.add_option("-x", "--transactions", dest="tx", type="int", default=-1)
parser.add_option("-v", "--version", dest="v", type="int")
parser.add_option("-a", "--negotiated-time", dest="delaytime", type="int", default=50)
(options, args) = parser.parse_args()

prepareIPList(open(expanduser(options.hosts), 'r').read())

if not options.B:
    options.B = int(math.ceil(options.n * math.log(options.n)))
if options.tx < 0:
    options.tx = options.B

client_test_freenet(options.n, options.t, options.v, options)
