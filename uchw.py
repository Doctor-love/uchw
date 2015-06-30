#!/usr/bin/env python

'''uchw - A wrapper for ugly/unpredictable Nagios-compatible check plugins'''

authors = 'Joel Rangsmo <joel@rangsmo.se>'
license = 'GPLv2'
version = 0.2

try:
    import argparse
    import subprocess
    import time
    import re

except ImportError as missing:
    exit_plugin('uchw: Failed to import required modules: "%s"' % missing)

def translate(state=None, result=None):
    '''Translates plugin exit codes to states and vice versa'''

    # Maps host and service states to textual meaning
    states = {'ok': 0, 'warning': 1, 'critical': 2, 'unknown': 3}

    # Loops through states and returns matching key or value
    for key, value in states.iteritems():
        if key == state or value == state:
            if result == 'exit_code':
                return value

            elif result == 'state':
                return key

    return False

def exit_plugin(output='No plugin output was provided', state='unknown'):
    '''Exits the plugin wrapper in Nagios-style'''

    print str(output)
    exit(translate(state=state, result='exit_code'))

def parse_arguments():
    '''Parses command line arguments'''

    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            'Developed in rage by %s - Licensed under %s'
            % (authors, license)))

    parser.add_argument(
        '-C', '--check-plugin',
        help='Check plugin command to be executed with shell',
        metavar='/path/to/plugin -a "1" -b "2"',
        type=str, required=True)

    parser.add_argument(
        '-p', '--pattern', dest='map_patterns',
        help='Regular expression pattern for state mapping',
        metavar=('regex', '{ok,warning,unknown,critical,passthrough}'),
        action='append', type=str, nargs=2)

    parser.add_argument(
        '-P', '--prefix',
        help='Append prefix/branding to plugin output',
        action='store_true', default=False)

    parser.add_argument(
        '-S', '--suffix',
        help='Append suffix to output with reason for wrapping decision',
        action='store_true', default=False)

    parser.add_argument(
        '-s', '--shell',
        help='Execute check plugin with specified shell',
        choices=['/bin/sh', '/usr/local/bin/bash', '/bin/bash'],
        default='/bin/bash')

    parser.add_argument(
        '-t', '--timeout',
        help='Timeout limit in seconds for check plugin execution',
        metavar='50', type=int, default=50)

    state_map = parser.add_argument_group('State mapping')
    states=['ok', 'warning', 'critical', 'unknown']

    state_map.add_argument(
        '-o', '--ok', dest='map_ok',
        help='Re-maps OK state',
        choices=states, default='ok')

    state_map.add_argument(
        '-w', '--warning', dest='map_warning',
        help='Re-maps warning state',
        choices=states, default='warning')

    state_map.add_argument(
        '-c', '--critical', dest='map_critical',
        help='Re-maps critical state',
        choices=states, default='critical')

    state_map.add_argument(
        '-u', '--unknown', dest='map_unknown',
        help='Re-maps unknown state',
        choices=states, default='unknown')

    parser.add_argument(
        '-v', '--version',
        help='Display plugin wrapper version',
        action='version', version=version)

    return parser.parse_args()

def execute_plugin(command=None, shell=None, timeout=None):
    '''Executes check plugin and returns dict with results'''

    shell_exec = subprocess.Popen(
        command, shell=True, executable=shell,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Checks if the plugin execution finishes in time
    while shell_exec.poll() is None and timeout:
        timeout = timeout - 1
        time.sleep(1)

    if not timeout:
        return False
    
    output = shell_exec.communicate()
    exit_code = shell_exec.returncode

    # Checks if plugin provides any output 
    stdout = output[0].strip()
    stderr = output[1].strip()

    output = ''

    if stdout:
        output = stdout

    if stderr:
        output = output + '\n-- uchw - stderr output:\n' + stderr

    return {'output': output, 'exit_code': exit_code}

def remap_exit_code(exit_code=None, ok=0, warning=1, critical=2, unknown=3):
    '''Re-maps the plugin exit code (if needed)'''

    reason = None

    if exit_code is 0:
        new_exit_code = ok

    elif exit_code is 1:
        new_exit_code = warning

    elif exit_code is 2:
        new_exit_code = critical

    elif exit_code is 3:
        new_exit_code = unknown

    else:
        new_exit_code = 'unknown'
        reason = '%i is not a valid Nagios plugin exit code' % exit_code

    # Checks if any reason for the mapping should be added
    exit_code = translate(state=exit_code, result='state')

    if new_exit_code != exit_code and not reason:
        reason = (
            'Plugin exit code %s was re-mapped to %s'
            % (exit_code, new_exit_code))

    return new_exit_code, reason

def match_pattern(string=None, pattern=None):
    '''Returns True if regular expression pattern matches string'''

    if re.match(pattern, str(string), re.DOTALL):
        return True

    else:
        return False

def main():
    '''Main application function'''

    # Parses command line arguments
    args = parse_arguments()

    # Executes check plugin
    command = execute_plugin(
        command=args.check_plugin, shell=args.shell, timeout=args.timeout)

    if not command:
        exit_plugin(
            'uchw: Execution timed out after %i seconds' % args.timeout)

    output = command['output']
    original_exit_code = command['exit_code']

    # Re-maps plugin return code/state
    state, reason = remap_exit_code(
        exit_code=original_exit_code,
        ok=args.map_ok, warning=args.map_warning,
        critical=args.map_critical, unknown=args.map_unknown)

    # Checks if any of the supplied matching patterns matches output
    if args.map_patterns:
        map_patterns = args.map_patterns

    else:
        map_patterns = []

    for map_pattern in map_patterns:
        re_pattern, map_state = map_pattern

        if map_state == 'passthrough':
            map_state = original_exit_code

        if match_pattern(string=output, pattern=re_pattern):
            state = map_state
            reason = 'Pattern "%s" was matched' % re_pattern

            break

    # Exits the plugin wrapper
    if args.prefix:
        output = 'uchw: ' + output

    if args.suffix and reason:
        output += ' (%s)' % str(reason)

    exit_plugin(output=output, state=state)

if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:
        exit_plugin('\nuchw: Command execution was interrupted by keyboard')

    except:
        raise
        exit_plugin('uchw: Plugin wrapper threw an unhandled exception')
