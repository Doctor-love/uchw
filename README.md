uchw
========
###### _A wrapper for ugly/unpredictable Nagios-compatible check plugins_

Overview
========
_uchw_ is a small tool that helps you tame the wildest _Nagios_-compatible check plugins.
It is written in Python and allows you to re-map their exit codes and change them depending on the status output.

It can be really useful when an event-handler like [_notss-eh_](https://github.com/Doctor-love/notss-eh) is used to execute "dangerous changes".

Features
========
- Provides timeout support for all executed plugins
- Search status output for regular expression patterns and change the state if matched
- Statick state mappings (like Critical -> Warning)


Installation and dependencies
=============================
_uchw_ depends on nothing outside the Python 2.7 standard library.
If you are running Python 2.6 on RHEL/CentOS 6, you can install the argparse module with pip or yum if you have the EPEL repository installed:

```
# pip install argparse
# yum install python-argparse

```

Example use cases
=================

### Example 1 - Monitoring a temperature sensor
Imagine that you use a plugin called "check_temp" to monitor the temperature of your servers.
It has served you very well, but it was compiled back in the dark ages and the source code is since long gone.

There is only one issue - from time to time the communication module in the probe dies and the plugins throws all kinds of nasty errors.

In this scenario, _uchw_ can be used to re-map the "CRITICAL" state to "UNKNOWN" and only on match output actually telling the temperature:

```
command_name: check_temp_wrapped
command_line: /plugins/uchw.py --check-plugin '/plugins/check_temp -H "$HOSTADDRESS$" -w "$ARG1$" -c "$ARG2$"' --critical unknown --pattern 'Temperature is .*' passthrough --suffix
```

If the temperature would go above the configured threshold, _uchw_ would ouput something like this:

```
Temperature is 55 degrees Celsius (Pattern "Temperature is .*" was matched)
```
