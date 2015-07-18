#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2015 Geoff Wright <geoff.wright@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: icinga2_feature
short_description: enables/disables icinga2 features
description:
   - Enables or disables a specified feature of Icinga2
options:
   name:
     description:
        - name of the feature to enable/disable
     required: true
   state:
     description:
        - indicate the desired state of the feature
     choices: ['present', 'absent']
     default: present
'''

EXAMPLES = '''
# enables the Icinga2 "gelf" feature
- icinga2_feature: name=gelf state=present

# disables the Icinga2 "gelf" feature
- icinga2_feature: name=gelf state=absent
'''

import re

def _disable_feature(module):
    name = module.params['name']
    icinga2_binary = module.get_bin_path("icinga2")
    if icinga2_binary is None:
        module.fail_json(msg="icinga2 not found. Icinga2 may not be installed.")

    result, stdout, stderr = module.run_command("%s feature disable %s" % (icinga2_binary, name))

    if re.match(r'critical/cli: This command must be run as root', stdout, re.S):
        module.fail_json(msg="icinga2 modules must be run as root")
    elif re.match(r'critical/cli: Cannot disable feature.*', stdout, re.S):
        module.exit_json(changed = False, result = "Success")
    elif result != 0:
        module.fail_json(msg="Cannot disable feature %s: %s" % (name, stdout))
    else:
        module.exit_json(changed = True, result = "Disabled")

def _enable_feature(module):
    name = module.params['name']
    icinga2_binary = module.get_bin_path("icinga2")
    if icinga2_binary is None:
        module.fail_json(msg="icinga2 not found. Icinga2 may not be installed. Set icinga2_path if it is installed to a non-standard path")

    result, stdout, stderr = module.run_command("%s feature enable %s" % (icinga2_binary, name))

    if re.match(r'warning/cli: Feature \'' + name + r'\' already enabled', stdout, re.S):
        module.exit_json(changed = False, result = "Success")
    elif re.match(r'critical/cli: This command must be run as root', stdout, re.S):
        module.fail_json(msg="icinga2 modules must be run as root")
    elif result != 0:
        module.fail_json(msg="Cannot enable feature %s: %s" % (name, stdout))
    else:
        module.exit_json(changed = True, result = "Enabled")

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name  = dict(required=True),
            state = dict(default='present', choices=['absent', 'present']),
        ),
    )

    icinga2_features = ['api', 'checker', 'command', 'compatlog', 'debuglog',
        'gelf', 'graphite', 'icingastatus', 'livestatus', 'mainlog', 'notification',
        'opentsdb', 'perfdata', 'statusdata', 'syslog']

    if module.params['name'] not in icinga2_features:
        module.fail_json(msg="%s is not a recognised Icinga2 feature" % module.params['name'])

    if module.params['state'] == 'present':
        _enable_feature(module)

    if module.params['state'] == 'absent':
        _disable_feature(module)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
