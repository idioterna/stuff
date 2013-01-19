nagios plugins
=====

`simple_http_check` is what the name suggests

In a little over 100 lines of code, the plugin reads lines from
a text file, fetches supplied urls in parallel, checks returned
stuff against supplied data and returns nagios plugin compatible
status and tersely formatted output intended to be sent over SMS
when things go wrong. Sample check definition file is included.

