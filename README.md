# Webhook Hub
A simple HTTP server for reformatting and routing webhook events.

## Overview

Webhook Hub solves the problem of having multiple webhook event-emitting services 
and potentially multiple applications or services where you'd like these events to be displayed. 
This is further complicated by the fact that these "output" and "input" services often emit and accept
payload data formatted in very different ways.

In some cases, this problem is solved as some developers support reformatting the event payloads 
of their services to suit the needs of the destination service (e.g. GitHub to Discord). 
Unfortunately, this is not true for most cases.

Webhook Hub acts as a proxy endpoint that allows users to configure:
- How to translate payload data from a webhook event-emitting service to a format acceptable for another service
- Where to route webhook events on a per-source and per-event basis

## Usage
```
usage: webhookhub.py [-h] {start,parse} ...

A simple HTTP server to reformat and route webhook events.

optional arguments:
  -h, --help     show this help message and exit

commands:
  {start,parse}
    start        start server instance
    parse        parse text in an interactive shell
```

### Server

To run a server instance locally on port `8000`:

`python webhookhub.py start -p 8000`

To run a server instance locally on port `8000` with extra debug logging:

`python webhookhub.py start -p 8000 --debug`

Of course, this is of no practical use running locally. To deploy it on a web-hosting service, 
ensure that the appropriate deployment files are present and configured so that the service starts 
a Webhook Hub server instance using commands similar to the examples above. For convenience, we've provided
the `Procfile` used by Heroku to deploy the server. The file contains this command, which makes use of
Heroku's environment variables:

`web: python webhookhub.py start -p $PORT`

### Parser Shell

To familiarize yourself with the Webhook Hub template syntax, you can use the provided interactive parser shell:

`python webhookhub.py parse`

To run the parser shell with a simulated webhook event payload, you can specify the raw payload in JSON as an argument:

`python webhookhub.py parse -r '{"a": {"b": "Foo", "num": 123}}'`

Or, you can specify the payload to use by providing the path to a file containing the payload in JSON format:

`python webhookhub.py parse -p path/to/payload.json`

# Configuration

TODO: define config files and payload templates

# Syntax

There are three data sources that can be used when reformatting the incoming payload using the Webhook Hub template syntax:

Data Source | Result
------------|--------------
`data`      | Data will be extracted from the webhook event payload.
`config`    | Data will be extracted from the variables defined in the configuration files in the `config/` folder.
`env`       | The value of a specified environment variable will be used.
`key`       | The value of the for-loop key will be used. This will result in an integer index for lists and a string key for dictionary objects.

For example, if the incoming payload data is `{"a": {"b": "Foo"}}`, then the expression `$data.a.b` 
will be evaluated as `Foo`

For the same payload, if the configuration file for this event defines a variable `title = Hello, $data.a.b`, 
then the expression `$config.title` will be evaluated as `Hello, Foo`

The expression `$env.HOSTNAME` will be evaluated as the value of the `HOSTNAME` environment variable.

In the for-loop expression `${for i in $data.z}Key is $key.i, ${endif}` with the incoming payload data 
being `{"z": ["a", "b", "c"]}`, then the expression will be evaluated as `Key is 0, Key is 1, Key is 2`

Refer to the following table for a more detailed list of expressions that can be used:

 Expression        | Result
-------------------|--------------------------
`${data.a.b}` | `payload_data['a']['b']`
`$data.a.b`   | Shortcut for `payload_data['a']['b']`
`${if data.x}` ... `${endif}` | Renders the text inside this statement if `payload_data['x']` exists, and is truthy
`${if not data.x}` ... `${endif}` | Renders the text inside this statements if `payload_data['x']` either doesn't exist, or exists and is falsy
`${if data.x}` ... `${else}` ... `${endif}` | Renders the first set of text inside this statement if `payload_data['x']` exists and is truthy, renders the second set of text otherwise
`${for i in data.z}` ... `${endfor}` | Renders the text inside this statement for each index in `payload_data['z']` when it is a list or each key when it is a dictionary object. Note that the index variable `i` can then be used to extract data (e.g. `$data.z.i`, `$key.z`)
`$data.z.length` | `len(payload_data['z'])` when `payload_data['z']` is a list
`$data.z.0` | `payload_data['z'][0]` when `payload_data['z']` is a list. Any other integer index can be used as well

*Note that the above statements mostly extract data from `data`, but the other data sources can be used as well!*

You can escape the `$` character as `\$` to avoid parsing it as an injection, so that expressions such as `\${data.a}` 
will be rendered in plain text as `${data.a}`

# Issues

If there are any issues with Webhook Hub, please don't be afraid to open a ticket. 
If there are any changes you'd like to contribute to this project, open a pull request. 
We here at Brethren Studios pride ourselves on responding to the needs of the open source community.
