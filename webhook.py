from time import sleep
import logging
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from constants import PORT, PUBLIC_URL
from bot import bot
from telebot import types

_logger = logging.getLogger(__name__)


class HTTPHandler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        body = json.loads(post_data.decode())

        bot.process_new_updates([types.Update.de_json(body)])

        self.send_response(204)
        self.end_headers()


def run_server():
    httpd = HTTPServer(("", PORT), HTTPHandler)
    _logger.info("Starting httpd ...\n")
    sleep(1)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    _logger.info("Stopping httpd...\n")


if __name__ == "__main__":
    bot.set_webhook(url=PUBLIC_URL)
    run_server()
