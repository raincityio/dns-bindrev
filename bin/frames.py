#!/usr/bin/env python3.7

import asyncio
import struct
import logging

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
