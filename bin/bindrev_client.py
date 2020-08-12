#!/usr/bin/env python3.7

import sys
import ipaddress
import asyncio
import argparse

class BindrevClient:

    def __init__(self, host='127.0.0.1', port=8888):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 8888
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

async def readline():
    loop = asyncio.get_event_loop()
    def _readline():
        return sys.stdin.readline()
    return await loop.run_in_executor(None, _readline) 

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', help='host')
    parser.add_argument('-p', type=int, help='port')
    parser.add_argument('-l', action='store_true', help='loop')
    parser.add_argument('ips', nargs='*')
    args = parser.parse_args()

    if args.l:
        await main_loop(args.host, args.p)
    else:
        if len(args.ips) == 0:
            raise Exception("please specify ip")
        await main_single(args.host, args.p, args.ips)

async def main_loop(host, port):
    async with BindrevClient(host=host, port=port) as client:
        while True:
            line = await readline()
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

async def main_single(host, port, ips):
    async with BindrevClient(host=host, port=port) as client:
        for _ip in ips:
            ip = ipaddress.ip_address(_ip)
            domain = await client.get(ip)
            if domain is None:
                raise Exception("unknown ip: %s" % ip)
            else:
                print(domain)

if __name__ == '__main__':
    asyncio.run(main())
