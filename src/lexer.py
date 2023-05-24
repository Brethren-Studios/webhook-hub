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

import ply.lex as lex


__author__ = 'Evan Williams'


class WebhookHubLexer:
	states = (
		('text', 'exclusive'),
		('inj', 'exclusive')
	)

	tokens = ('INJ_START', 'VARIABLE', 'IF', 'NOT', 'ELSE', 'ENDIF', 'FOR', 'INDEX_VAR', 'IN', 
		'ENDFOR', 'SHORTCUT_VARIABLE', 'INJ_END', 'TEXT', 'ESCAPED_CHAR')
	
	t_INITIAL_text_SHORTCUT_VARIABLE = r'\$(?:data|config|env|key)(?:\.[\w\-]+)*'
	t_INITIAL_text_TEXT = r'.|\s'
	t_inj_VARIABLE = r'(?:data|config|env|key)(?:\.[\w\-]+)*'
	t_inj_IF = r'if'
	t_inj_NOT = r'not'
	t_inj_ELSE = r'else'
	t_inj_ENDIF = r'endif'
	t_inj_FOR = r'for'
	t_inj_INDEX_VAR = r'\b\w\b'
	t_inj_IN = r'in'
	t_inj_ENDFOR = r'endfor'
	t_inj_ignore = ' '

	def __init__(self, **kwargs):
		self.lexer = lex.lex(module=self, **kwargs)

	def t_INITIAL_text_INJ_START(self, t):
		r'\$\{'
		t.lexer.push_state('inj')
		return t

	def t_INITIAL_text_ESCAPED_CHAR(self, t):
		r'\\\$'
		return t

	def t_inj_INJ_END(self, t):
		r'\}'
		t.lexer.pop_state()
		return t

	def t_text_INJ_END(self, t):
		r'\}'
		t.lexer.pop_state()
		t.lexer.pop_state()
		return t

	def t_ANY_error(self, t):
		raise SyntaxError('Illegal character "{0}"'.format(t.value[0]))

	def token(self):
		return self.lexer.token()

	def input(self, input_text):
		self.lexer.input(input_text)
