#!/usr/bin/env python3.7

import sys
import ipaddress
import asyncio
import argparse

class BindrevClient:

    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port

    async def open(self):
        reader, writer = await asyncio.open_connection(self.host, self.port)
        self.reader = reader
        self.writer = writer

    async def close(self):
        try:
            self.writer.write((0).to_bytes(1, byteorder='big'))
            await self.reader.readexactly(1)
        finally:
            self.writer.close()
        await self.writer.wait_closed()

    async def get(self, ip):
        ip_sz = len(ip.packed).to_bytes(1, byteorder='big')
        self.writer.write(ip_sz)
        self.writer.write(ip.packed)
        domain_sz = int.from_bytes(await self.reader.readexactly(1), byteorder='big')
        if domain_sz == 0:
            domain = None
        else:
            domain = (await self.reader.readexactly(domain_sz)).decode('utf-8')
        return domain

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, *args):
        await self.close()

async def main():
    async with BindrevClient() as client:
        while True:
            line = sys.stdin.readline()
            if len(line) == 0:
                break
            line = line.strip()
            if len(line) == 0:
                continue
            try:
                ip = ipaddress.ip_address(line)
                print(await client.get(ip))
            except Exception as e:
                print(e)

async def __main():
    if len(sys.argv) != 2:
        raise Exception("Please specify ip")
    ip = ipaddress.ip_address(sys.argv[1])
    async with BindrevClient() as client:
        domain = await client.get(ip)
        if domain is None:
            raise Exception("unknown ip: %s" % ip)
        else:
            print(domain)

if __name__ == '__main__':
    asyncio.run(__main())
