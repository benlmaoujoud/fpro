import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def handle_client(self, reader, writer):
        try:
            request_line = await reader.readline()
            logger.info(f"Request: {request_line.decode().strip()}")
            method, url, version = request_line.decode().split()
            if not url.startswith(('http://', 'https://')):
                url = f'http://{url}'
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            host = parsed_url.hostname
            port = parsed_url.port or 80

            target_reader, target_writer = await asyncio.open_connection(host, port)

            target_writer.write(request_line)
            while True:
                line = await reader.readline()
                if line == b'\r\n':
                    break
                target_writer.write(line)
            await target_writer.drain()

            while True:
                data = await target_reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()

        except Exception as e:
            logger.error(f"Error handling request: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def run(self):
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port)

        addr = server.sockets[0].getsockname()
        logger.info(f'Serving on {addr}')

        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    proxy = ProxyServer('127.0.0.1', 8080)
    asyncio.run(proxy.run())