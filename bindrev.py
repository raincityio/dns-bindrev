#!/usr/bin/env python3

import signal
import shelve
import struct
import dnstap_pb2
import asyncio
import ipaddress
import logging
import dns.message
import dns.rdatatype
import code
import ipaddress
import uvloop

import sys 
sys.path.append("/home/drew/src/arpc")
import arpc
import arpc.arpc

class Frame:

    control = 0
    data = 1

    def __init__(self, frame_type):
        self.type = frame_type

    @staticmethod
    async def decodeFromWire(reader):
        frame_sz_raw = await reader.readexactly(4)
        (frame_sz,) = struct.unpack("!I", frame_sz_raw)
        if (frame_sz == 0):
            frame = await ControlFrame.decodeFromWire(reader)
        else:
            frame = await DataFrame.decodeFromWire(reader, frame_sz)
        return frame

class ControlFrame(Frame):

    accept = 0x01
    start = 0x02
    stop = 0x03
    ready = 0x04
    finish = 0x05

    def __init__(self, control_frame_type):
        Frame.__init__(self, Frame.control)
        self.control_type = control_frame_type

    def encodeToWire(self, writer):
        data = struct.pack("!I", self.control_type)
        writer.write(struct.pack("!II", 0, len(data)))
        writer.write(data)

    @staticmethod
    async def decodeFromWire(reader):
        cframe_header = await reader.readexactly(8)
        (cframe_sz, cframe_type,) = struct.unpack("!II", cframe_header)
        cframe_len = cframe_sz - 4
        data = await reader.readexactly(cframe_len)
        return ControlFrame(cframe_type)

class DataFrame(Frame):

    def __init__(self, payload):
        Frame.__init__(self, Frame.data)
        self.payload = payload

    @staticmethod
    async def decodeFromWire(reader, frame_sz):
        payload = await reader.readexactly(frame_sz)
        return DataFrame(payload)

class FrameStreamReader:

    def __init__(self, callback, reader, writer):
        self.callback = callback
        self.reader = reader
        self.writer = writer
        self.bi = True

    async def loop(self):
        processStream = True
        while processStream:
            frame = await Frame.decodeFromWire(self.reader)
            if (frame.type == Frame.control):
                if (frame.control_type == ControlFrame.start):
                    pass
                elif (frame.control_type == ControlFrame.stop):
                    if (self.bi):
                        finish = ControlFrame(ControlFrame.finish)
                        finish.encodeToWire(self.writer)
                    processStream = False
                elif (frame.control_type == ControlFrame.ready):
                    if (self.bi):
                        accept = ControlFrame(ControlFrame.accept)
                        accept.encodeToWire(self.writer)
                else:
                    raise Exception("Unexpected control frame: %s" % type(frame))
            elif (frame.type == Frame.data):
                try:
                    self.callback(frame)
                except Exception as e:
                    logging.error(e)
            else:
                raise Exception("Unknown frame type: %s" % type(frame))

class UnixFrameStreamServer:

    def __init__(self, path, callback):
        self.path = path
        self.callback = callback

    async def start(self):
        await asyncio.start_unix_server(self.__handle__, path=self.path)

    async def __handle__(self, reader, writer):
        handler = FrameStreamReader(self.callback, reader, writer)
        await handler.loop()

class ReverseLookup:

    def __init__(self, dbfilename):
        self.lookup = {}
        self.db = shelve.open(dbfilename)

    def close(self):
        self.db.close()
        
    def add(self, ip_, domain):
        ip = ipaddress.ip_address(ip_).compressed
        if (ip in self.lookup):
            current = self.lookup[ip]
            if (not current == domain):
                print("Replacing %s[%s] -> %s [count=%s]" % (ip, current, domain, len(self.lookup)))
                self.lookup[ip] = domain
                self.db[ip] = domain
        else:
            print("%s -> %s [count=%s]" % (ip, domain, len(self.lookup)))
            self.lookup[ip] = domain
            self.db[ip] = domain

    def get(self, ip_):
        ip = ipaddress.ip_address(ip_).compressed
        if (ip in self.lookup):
            return self.lookup[ip]
        elif (ip in self.db):
            domain = self.db[ip]
            self.lookup[ip] = domain
            return domain
        return None

async def setup(dbfilename):

    lookup = ReverseLookup(dbfilename)

    def callback(frame):
        dnstap = dnstap_pb2.Dnstap()
        if (not dnstap.type == dnstap_pb2.Dnstap.MESSAGE):
            logging.warn("Unknown dnstap message type: %s" % dnstap.type)
            return
        dnstap.ParseFromString(frame.payload)
        message = dnstap.message
        if (message.type == dnstap_pb2.Message.CLIENT_RESPONSE):
            m = dns.message.from_wire(message.response_message)
            linker = {}
            for answer in m.answer:
                name = str(answer.name)
                if (not name in linker):
                    linker[name] = []
                for item in answer.items:
                    linker[name].append(item)
            for question in m.question:
                if (not len(question.items) == 0):
                    raise Exception("Unexpected items under question: %s" % question)
                if (not question.rdtype in [dns.rdatatype.A, dns.rdatatype.AAAA]):
                    continue
                q = []
                questionname = str(question.name)
                q.append(questionname)
                while (not len(q) == 0):
                    name = q.pop()
                    if (not name in linker):
                        continue
                    for item in linker[name]:
                        itemname = str(item)
                        if (item.rdtype in [dns.rdatatype.A, dns.rdatatype.AAAA]):
                            lookup.add(itemname, questionname)
                        elif (item.rdtype in [dns.rdatatype.PTR, dns.rdatatype.CNAME]):
                            q.append(itemname)
                        else:
                            pass

    frameStreamServer = UnixFrameStreamServer("/tmp/test.sock", callback)
    await frameStreamServer.start()

    async def requestHandler(session, ip):
        try:
            return lookup.get(ip)
        except:
            return None

    loop = asyncio.get_event_loop()
    requestServer = arpc.arpc.ArpcServer(loop, '0.0.0.0', 8888, requestHandler)
    await requestServer.start()

    def signal_handler(sig, frame):
        lookup.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

dbfilename = "/home/drew/bindrev"

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
loop = asyncio.get_event_loop()
loop.run_until_complete(setup(dbfilename))
loop.run_forever()
