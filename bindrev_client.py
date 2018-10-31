#!/usr/bin/env python3

import sys
sys.path.append("/home/drew/src/arpc")
import arpc
import arpc.arpc

if (len(sys.argv) != 2):
    raise Exception("Please specify ip")

client = arpc.arpc.SrpcClient('127.0.0.1', 8888, None)
client.connect()

reply = client.sendRequest(sys.argv[1])
if (not reply):
    r = 1
else:
    r = 0
    print(reply)

client.bye()
client.close()
client.stop()

sys.exit(r)
