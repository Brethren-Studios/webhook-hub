#!/usr/bin/env python3

"""A simple HTTP server for reformatting and routing webhook events."""

# Copyright (c) 2018 Brethren Studios
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import json
import os
import sys

from http.server import HTTPServer

from src.route import WebhookHubRoute
from src.parser import WebhookHubParser
from src.server import make_WebhookHubRequestHandler_class
from src.shell import start_shell


__author__ = 'Evan Williams'
__copyright__ = "Copyright 2018, Brethren Studios"
__license__ = "MIT"
__version__ = "1.1.0"
__email__ = "evanw555@gmail.com"


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(ROOT_DIR, 'config')
TEMPLATES_DIR = os.path.join(ROOT_DIR, 'templates')


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='A simple HTTP server to reformat and route webhook events.')

    subparsers = arg_parser.add_subparsers(dest='command', title='commands')

    start_parser = subparsers.add_parser('start', description='Start WebhookHub server.', help='start server instance')
    start_parser.add_argument('-p', dest='port', required=True, help='port to run the server on')
    start_parser.add_argument('--debug', dest='debug', action='store_true', help='run with extra debug logging')

    parse_parser = subparsers.add_parser('parse', description='Parse text in an interactive shell using WebhookHub template syntax.', help='parse text in an interactive shell')
    parse_group = parse_parser.add_mutually_exclusive_group()
    parse_group.add_argument('-p', dest='payload_filepath', default=None, help='filepath of payload to use when evaluating variables')
    parse_group.add_argument('-r', dest='payload_raw', default=None, help='raw string payload to use when evaluating variables')
 
    args = arg_parser.parse_args()

    if args.command == 'start':
        config_files = [os.path.join(CONFIG_DIR, file) for file in os.listdir(CONFIG_DIR) if file.endswith('.ini')]

        routes = {route.agent: route for route in [WebhookHubRoute.from_file(file) for file in config_files]}

        if args.debug:
            for route in routes.values():
                print(route)

        request_handler_class = make_WebhookHubRequestHandler_class(routes, TEMPLATES_DIR, debug=args.debug)
        server = HTTPServer(('', int(args.port)), request_handler_class)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

        server.server_close()

    elif args.command == 'parse':
        try:
            if args.payload_filepath:
                with open(args.payload_filepath, 'r') as fin:
                    payload = json.load(fin, strict=False)
            elif args.payload_raw:
                payload = json.loads(args.payload_raw, strict=False)
            else:
                payload = None
        except FileNotFoundError as e:
            sys.stderr.write('No such file or directory: \'{0}\'\n'.format(e.filename))
            sys.exit(1)
        except json.decoder.JSONDecodeError:
            sys.stderr.write('Failed to deserialize payload\n')
            sys.exit(1)

        start_shell('WebhookHub {0} parser shell - {1}'.format(__version__, __copyright__), payload)

    else:
        arg_parser.print_help()

    sys.exit(0)
