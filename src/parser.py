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

import itertools
import json
import ply.yacc as yacc
import re
import sys

from src.lexer import WebhookHubLexer


__author__ = 'Evan Williams'


CONFIG_PATTERN = re.compile(r'^config\.')
KEY_PATTERN = re.compile(r'^key\.')


class WebhookHubParser:
    # Top-level nonterminal to parse
    start = 'items'

    # Used to ensure text is parsed correctly before an INJ_START token
    precedence = (
        ('left', 'INJ_START'),
        ('left', 'TEXT')
    )

    def __init__(self, payload=None, event_config=None):
        self.payload = payload
        self.event_config = event_config

        # Configure this parser as a wrapper around a PLY lexer and parser
        self.lexer = WebhookHubLexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self)

        # For-loop key indexing information
        self.index_symbol_table = {}
        self.index_symbol_stack = []
        self.num_index_combinations = 1

    def parse(self, text):
        """
        Parse some text using the WebhookHub template syntax.
        Returns None if there is an error or no text is provided.

        >>> payload = {'a': {'b': 'Foo'}}
        >>> parser = WebhookHubParser(payload=payload)
        >>> parser.parse('$data.a.b')
        'Foo'
        >>> parser.parse('$data.x.y')
        None
        """
        if not text:
            return None
        try:
            result = self.parser.parse(text, lexer=self.lexer)
            if type(result) == list and len(result) == 1:
                return result[0]
            elif result is None:
                return None
            else:
                sys.stderr.write('For-loop branching error during parsing: {0}\n'.format(str(result)))
                return None
        except WebhookHubParserError as e:
            sys.stderr.write('Failed to parse input: {0}\n'.format(e))
            return None
        except SyntaxError as e:
            sys.stderr.write('SyntaxError: {0}\n'.format(e))
            return None

    # Symbol evaluation methods

    def evaluate_symbol(self, symbol, index_context={}, stringify=False):
        if not symbol:
            return '' if stringify else None

        first_component = symbol.split('.')[0]
        
        if first_component == 'data':
            return self.evaluate_data_symbol(symbol, index_context=index_context, stringify=stringify)
        elif first_component == 'config':
            return self.evaluate_config_symbol(symbol, stringify=stringify)
        elif first_component == 'key':
            return self.evaluate_key_symbol(symbol, index_context=index_context, stringify=stringify)
        else:
            raise WebhookHubParserError('symbol is "{0}" neither a data symbol nor a config symbol'.format(symbol))

    def evaluate_data_symbol(self, symbol, index_context={}, stringify=False):
        if not symbol:
            return None

        data = None

        components = symbol.split('.')

        try:
            # pylint: disable=E1136
            for component in components:
                # The first "data" token
                if data is None and component == 'data':
                    data = self.payload
                # Dictionary indexing token
                elif type(data) == dict and component in data:
                    data = data[component]
                # Dictionary indexing token as for-key from index_context
                elif type(data) == dict and component in index_context:
                    data = data[index_context[component]]
                # List "length" token
                elif type(data) == list and component == 'length':
                    data = len(data)
                # List indexing token as for-key from index_context
                elif type(data) == list and component in index_context:
                    data = data[index_context[component]]
                # List indexing token
                elif type(data) == list:
                    data = data[int(component)]
                # Unknown token, raise error
                else:
                    raise KeyError()
        except (KeyError, IndexError, ValueError):
            return ''
        
        if stringify:
            if data is None:
                data = ''

            if type(data) in [dict, list, bool, int, float]:
                data = json.dumps(data)

        return data

    def evaluate_config_symbol(self, symbol, stringify=False):
        if not self.event_config:
            raise WebhookHubParserError('this parsing context has no event configuration')

        config_property = re.sub(CONFIG_PATTERN, '', symbol)
        variable = self.event_config.get_variable(config_property)

        parser = WebhookHubParser(payload=self.payload, event_config=self.event_config)
        value = parser.parse(variable)
        
        if value is None:
            return '' if stringify else None

        return value

    def evaluate_key_symbol(self, symbol, index_context={}, stringify=False):
        if len(index_context) == 0:
            raise WebhookHubParserError('cannot reference a for-loop key in this context')

        key = re.sub(KEY_PATTERN, '', symbol)
        return index_context.get(key, '' if stringify else None)

    # Methods to handle for-loop key indexing

    def put_index_symbol(self, symbol, indexes):
        """Adds a for-loop key to the stack."""
        if symbol in self.index_symbol_table:
            raise WebhookHubParserError('cannot add index symbol "{0}", it already exists'.format(symbol))

        self.index_symbol_table[symbol] = indexes
        self.index_symbol_stack.append(symbol)
        self.num_index_combinations *= len(indexes)

    def remove_index_symbol(self, symbol):
        """Removes a for-loop key from the stack."""
        if symbol not in self.index_symbol_table:
            raise WebhookHubParserError('cannot remove index symbol "{0}", it doesn\'t exist'.format(symbol))

        self.num_index_combinations //= len(self.index_symbol_table[symbol])
        self.index_symbol_stack.pop()
        del self.index_symbol_table[symbol]

    def get_index_context(self, combination_index):
        """Get the values of all present for-loop keys for some for-loop context."""
        if combination_index < 0 or combination_index >= self.num_index_combinations:
            raise WebhookHubParserError('invalid for-loop combination index: {0}'.format(combination_index))

        if len(self.index_symbol_stack) == 0:
            return {}

        index_lists = [self.index_symbol_table[symbol] for symbol in self.index_symbol_stack]
        index_combination = list(itertools.product(*index_lists))[combination_index]
        return {symbol: index_combination[i] for i, symbol in enumerate(self.index_symbol_stack)}

    # Parsing grammar definitions

    def p_items_multiple(self, p):
        'items : items item'
        p[0] = ['{0}{1}'.format(p[1][i], p[2][i]) for i in range(self.num_index_combinations)]

    def p_items_one(self, p):
        'items : item'
        p[0] = p[1]

    def p_item_text(self, p):
        'item : TEXT'
        p[0] = [str(p[1])] * self.num_index_combinations

    def p_item_escaped(self, p):
        'item : ESCAPED_CHAR'
        if len(p[1]) != 2:
            raise WebhookHubParserError('escaped character "{0}" is invalid'.format(p[1]))
        p[0] = [p[1][1]] * self.num_index_combinations

    def p_item_injection(self, p):
        'item : injection'
        p[0] = p[1]

    def p_item_shortcut(self, p):
        'item : SHORTCUT_VARIABLE'
        p[0] = [self.evaluate_symbol(p[1].replace('$', '', 1), index_context=self.get_index_context(i), stringify=True) for i in range(self.num_index_combinations)]

    def p_injection_variable(self, p):
        'injection : INJ_START VARIABLE INJ_END'
        p[0] = [self.evaluate_symbol(p[2], index_context=self.get_index_context(i), stringify=True) for i in range(self.num_index_combinations)]

    def p_injection_if(self, p):
        'injection : INJ_START IF VARIABLE INJ_END items INJ_START ENDIF INJ_END'
        p[0] = [p[5][i] if self.evaluate_symbol(p[3], index_context=self.get_index_context(i)) else '' for i in range(self.num_index_combinations)]

    def p_injection_if_not(self, p):
        'injection : INJ_START IF NOT VARIABLE INJ_END items INJ_START ENDIF INJ_END'
        p[0] =  ['' if self.evaluate_symbol(p[4], index_context=self.get_index_context(i)) else p[6][i] for i in range(self.num_index_combinations)]

    def p_injection_if_else(self, p):
        'injection : INJ_START IF VARIABLE INJ_END items INJ_START ELSE INJ_END items INJ_START ENDIF INJ_END'
        p[0] = [p[5][i] if self.evaluate_symbol(p[3], index_context=self.get_index_context(i)) else p[9][i] for i in range(self.num_index_combinations)]

    def p_injection_for(self, p):
        'injection : beginfor items INJ_START ENDFOR INJ_END'

        self.remove_index_symbol(p[1]['symbol'])

        # Join chunks for this for loop (e.g. [0, 1, 2, 3, 4, 5] -> [01, 23, 45])
        n = len(p[2]) // self.num_index_combinations  # Size of each chunk
        p[0] = [''.join(p[2][i * n : i * n + n]) for i in range(self.num_index_combinations)]

    def p_injection_begin_for(self, p):
        'beginfor : INJ_START FOR INDEX_VAR IN VARIABLE INJ_END'

        # TODO: Allow using for-loop keys to create other for-loops, currently not possible

        l = self.evaluate_symbol(p[5])
        if type(l) not in [list, dict]:
            raise WebhookHubParserError('symbol "{0}" is neither a list nor a dictionary'.format(p[5]))

        if type(l) == list:
            self.put_index_symbol(p[3], tuple(range(len(l))))
        elif type(l) == dict:
            self.put_index_symbol(p[3], tuple(l.keys()))

        p[0] = {
            'symbol': p[3]
        }


class WebhookHubParserError(Exception):
    def __init__(self, message):
        super().__init__(message)
