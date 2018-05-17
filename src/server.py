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

import json
import os
import requests
import sys

from http.server import BaseHTTPRequestHandler

from src.reformat import reformat_payload, evaluate_expression, WebhookHubReformattingError
from src.route import WebhookHubRouteError


__author__ = 'Evan Williams'


def make_WebhookHubRequestHandler_class(routes, templates_dir, debug=False):
    def debug_log(text):
        if debug:
            print(text)

    class WebhookHubRequestHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            debug_log('new POST request, headers:\n{0}'.format(str(self.headers)))

            try:
                debug_log('read payload...')
                self.read_payload()
                debug_log(str(self.payload))

                route = self.get_route()
                if not route:
                    debug_log('invalid user agent')
                    self.error_response(403, b'No compatible route is defined for this User-Agent')
                    return
                debug_log('webhook route = {0}'.format(route.agent))

                event_key = self.get_event_key(route)
                if not event_key:
                    self.error_response(400, b'Unable to determine the event key for this webhook event')
                    return
                debug_log('webhook event key = {0}'.format(event_key))

                event_config = route.get_event_configuration(event_key)
                if not event_config:
                    self.error_response(400, b'No compatible event configuration for this webhook event')
                    return

                destination = route.get_destination(event_key)
                template = os.path.join(templates_dir, route.get_template(event_key))

                debug_log('reformat payload...')
                reformatted_payload = reformat_payload(self.payload, template, event_config)
                debug_log('reformatted payload={0}'.format(reformatted_payload))

                debug_log('routing webhook event to {0}'.format(destination))
                headers = {
                    'Content-Type': 'application/json'
                }
                response = requests.post(destination, json=reformatted_payload, headers=headers)

                debug_log('responding to origin...')

                self.send_response(response.status_code)
                for key, header in response.headers.items():
                    self.send_header(key, header)
                self.end_headers()
                self.wfile.write(response.content)

            except WebhookHubRouteError as e:
                sys.stderr.write('{0}\n'.format(e))
                self.error_response(400, bytes(str(e), 'utf-8'))

            except WebhookHubReformattingError as e:
                sys.stderr.write('{0}\n'.format(e))
                sys.stderr.write('{0}\n'.format(e.data))
                self.error_response(400, bytes(str(e), 'utf-8'))

            except json.decoder.JSONDecodeError:
                debug_log('unable to read payload')
                self.error_response(400, b'Unable to read webhook event payload')

        def read_payload(self):
            if 'Content-Length' in self.headers:
                self.payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
            else:
                self.payload = json.loads(self.rfile.read().decode('utf-8'))

        def get_route(self):
            # Look for any known agent that is a substring of the User-Agent header
            if 'User-Agent' in self.headers:
                user_agent_header = self.headers['User-Agent'].lower()
                for agent in routes:
                    if agent.lower() in user_agent_header:
                        return routes[agent]
            # If no user agent, look for a match in any of the sent header keys
            else:
                for agent in routes:
                    for header_key in self.headers:
                        if agent.lower() in header_key.lower():
                            return routes[agent]

            return None

        def get_event_key(self, route):
            if route.key_from_header and route.key_from_header in self.headers:
                return self.headers[route.key_from_header]
            elif route.key_from_payload:
                return evaluate_expression(route.key_from_payload, self.payload, self)

        def error_response(self, status, bytes_data):
            self.send_response(status)
            self.send_header('Content-Length', len(bytes_data))
            self.end_headers()
            self.wfile.write(bytes_data)

    return WebhookHubRequestHandler
