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

import sys

from src.parser import WebhookHubParser


__author__ = 'Evan Williams'


def start_shell(opening_text, payload):
    """Start an interactive parser shell"""

    if opening_text:
        print(opening_text)

    print('Use "exit" or Ctrl-D (i.e. EOF) to exit')

    while True:
        try:
            input_text = input('> ')
            if input_text == 'exit':
                sys.exit(0)
            parser = WebhookHubParser(payload=payload)
            result = parser.parse(input_text)
        except SyntaxError as e:
            sys.stderr.write('Failed to parse text: {0}\n'.format(e))
            result = ''
        except EOFError:
            print('')
            sys.exit(0)
        except KeyboardInterrupt:
            result = ''

        if result is not None:
            print(result)
