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

import configparser


__author__ = 'Evan Williams'


RESERVED_KEYS = ['destination', 'template', 'parent']


class WebhookHubRoute():
    def __init__(self, config):
        global_meta = config['global-meta']

        self.agent = global_meta['agent']
        self.destination = global_meta.get('destination', None)
        self.template = global_meta.get('template', None)
        self.key_from_header = global_meta.get('key-from-header', None)
        self.key_from_payload = global_meta.get('key-from-payload', None)

        self.configurations = {
            event_key: EventConfiguration(event_key, config[event_key]) for event_key in config.sections() if event_key != 'global-meta'
        }

        # Set parents for all event configurations
        for event_key in self.configurations:
            if 'parent' in config[event_key] and config[event_key]['parent'] in self.configurations:
                self.configurations[event_key].parent = self.configurations[config[event_key]['parent']]
            elif 'default' in self.configurations and event_key != 'default':
                self.configurations[event_key].parent = self.configurations['default']
            else:
                self.configurations[event_key].parent = None

    def __str__(self):
        s = 'WebhookHubRoute({0})'.format(self.agent)
        for event_key in self.configurations:
            s += '\n- {0}'.format(str(self.configurations[event_key]))
        return s

    def get_destination(self, event_key):
        if event_key in self.configurations and self.configurations[event_key].get_destination():
            return self.configurations[event_key].get_destination()
        elif 'default' in self.configurations and self.configurations['default'].get_destination():
            return self.configurations['default'].get_destination()
        elif self.destination:
            return self.destination
        else:
            raise WebhookHubRouteError('no valid destination for event "{0}" defined for route "{1}"'.format(event_key, self.agent))

    def get_template(self, event_key):
        if event_key in self.configurations and self.configurations[event_key].get_template():
            return self.configurations[event_key].get_template()
        elif 'default' in self.configurations and self.configurations['default'].get_template():
            return self.configurations['default'].get_template()
        elif self.template:
            return self.template
        else:
            raise WebhookHubRouteError('no valid template for event "{0}" defined for route "{1}"'.format(event_key, self.agent))

    def get_event_configuration(self, event_key):
        if event_key in self.configurations:
            return self.configurations[event_key]
        elif 'default' in self.configurations:
            return self.configurations['default']
        else:
            return None

    @staticmethod
    def from_file(filepath):
        config = configparser.ConfigParser()
        config.read(filepath)
        return WebhookHubRoute(config)
            

class EventConfiguration():
    def __init__(self, event_key, config):
        self.event_key = event_key
        self.parent = None
        self.destination = config.get('destination', None)
        self.template = config.get('template', None)

        self.variables = {key.lower(): config[key] for key in config if key.lower() not in RESERVED_KEYS}

    def __str__(self):
        return 'EventConfiguration({0}, {1} variables{2})'.format(self.event_key, len(self.variables), ', parent={0}'.format(self.parent.event_key) if self.parent else '')

    def get_variable(self, name):
        if name.lower() in self.variables:
            return self.variables[name.lower()]
        elif self.parent is not None:
            return self.parent.get_variable(name)
        else:
            return None

    def get_destination(self):
        if self.destination:
            return self.destination
        elif self.parent is not None:
            return self.parent.get_destination()
        else:
            return None

    def get_template(self):
        if self.template:
            return self.template
        elif self.parent is not None:
            return self.parent.get_template()
        else:
            return None


class WebhookHubRouteError(Exception):
    def __init__(self, message):
        super().__init__(message)
