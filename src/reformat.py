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
import re
import sys

from src.parser import WebhookHubParser


__author__ = 'Evan Williams'


INJECTION_PATTERN = re.compile(r'\${([\w\-]+)}')  # ${(variable)}


def reformat_payload(payload, template_filepath, event_config):
    evaluated_template = evaluate_template(payload, template_filepath, event_config)
    try:
        return json.loads(evaluated_template, strict=False)
    except json.decoder.JSONDecodeError:
        raise WebhookHubReformattingError('Unable to deserialize evaluated template', evaluated_template)

def evaluate_template(payload, template_filepath, event_config):
    with open(template_filepath, 'r') as fin:
        template = fin.read()
    # return re.sub(INJECTION_PATTERN, lambda x: evaluate_expression(event_config.get_variable(x.group(1)), payload) or x.group(0), template)
    return evaluate_expression(template, payload, event_config)

def evaluate_expressions(expressions, payload, event_config):
    """
    Evaluate a dictionary of expressions, each containing variable references:

    >>> payload = {'a': {'b': 'world', 'c': 'person'}}
    >>> expressions = {'foo': 'Hello, ${data.a.b}!', 'bar': 'I am a ${data.a.c}'}
    >>> evaluate_expressions(expressions, payload)
    {'foo': 'Hello, world!', 'bar': 'I am a person'}

    """

    return {key: evaluate_expression(expressions[key], payload, event_config) for key in expressions}

def evaluate_expression(expression, payload, event_config):
    """
    Evaluate an expression containing variable references:

    >>> payload = {'a': {'b': 'world'}}
    >>> evaluate_expression('Hello, ${data.a.b}!', payload)
    'Hello, world!'

    """
    if not expression:
        return None

    parser = WebhookHubParser(payload=payload, event_config=event_config)
    value = parser.parse(expression)

    return value


class WebhookHubReformattingError(Exception):
    def __init__(self, message, data):
        super().__init__(message)
        self.data = data
