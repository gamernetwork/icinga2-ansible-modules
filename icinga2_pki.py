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
module: icinga2_pki
short_description: icinga2 pki commands
description:
   - Run various icinga2 pki commands with some additional actions not provided by stock Icinga2. All file name are based on C(common-name).
options:
   action:
     choices: ['new-ca', 'new-cert', 'new-csr', 'new-key', 'new-signed-cert', 'request', 'save-cert', 'sign-csr', 'ticket']
     description:
        - C(new-ca) creates a new certificate authority.
        - C(new-cert) creates a new private key and self signed certificate.
        - C(new-csr) creates a new private key and csr.
        - C(new-key) creates a new private key.
        - C(new-signed-cert) creates key and certificate signed with CA cert
        - C(request) not implemented, use M(fetch) instead.
        - C(save-cert) not implemented, use M(fetch) instead.
        - C(sign-csr) sign an existing csr to with the CA cert
        - C(ticket) generates a new ticket.
     required: yes
   force: 
     choices: [ "yes", "no" ]
     default: "no"
     description:
       - remove existing CA or files assocatied with common_name

'''

EXAMPLES = '''
# create new CA
- icinga2_pki: action=new-ca

# create cert signed by CA
- icinga2_pki: action=new-signed-cert common_name=foo

# create self signed cert
- icinga2_pki: action=new-cert common_name=foo
'''

import os
import re
import shutil


def _new_ca(module):
    icinga2_binary = get_icinga2_binary(module)

    if module.boolean(module.params['force']):
        if os.path.islink(module.params['ca_path']):
            os.unlink(module.params['ca_path'])
        elif os.path.exists(module.params['ca_path']):
            shutil.rmtree(module.params['ca_path'])

    result, stdout, stderr = module.run_command("%s pki new-ca" %
                                                icinga2_binary)

    if re.match(r'critical/cli: setgroups.*', stdout, re.S):
        module.fail_json(
            msg="This command must be run as root or the 'nagios' user: %s" %
            stdout)
    elif re.match(r'critical/cli: CA directory.*', stdout, re.S):
        module.fail_json(
            msg="CA directory already exists. Use 'force=yes' to replace: %s" %
            stdout)
    elif result != 0:
        module.fail_json(msg=stdout)
    else:
        module.exit_json(changed=True, msg="new CA created at %s" %
            module.params['ca_path'], stdout=stdout)


def _new_cert(module):

    if not module.params['common_name']:
        module.fail_json(
            msg="common_name is required for the 'new-cert' action")

    remove_files(module)

    if module.params['action'] == "new-key":
        cmd = ("%s pki new-cert --cn %s --key %s" %
               (module.params['icinga2_binary'], module.params['common_name'],
                module.params['key_file']))
    elif (module.params['action'] == "new-csr" or
        module.params['action'] == "new-signed-cert"):
        cmd = ("%s pki new-cert --cn %s --key %s --csr %s" %
               (module.params['icinga2_binary'], module.params['common_name'],
                module.params['key_file'], module.params['csr_file']))
    elif module.params['action'] == "new-cert":
        cmd = ("%s pki new-cert --cn %s --key %s --cert %s" %
               (module.params['icinga2_binary'], module.params['common_name'],
                module.params['key_file'], module.params['crt_file']))
    run_cmd(module, cmd)
    return 0

def _request(module):
    module.exit_json(changed=False,
                     msg="Not implemented. Use 'fetch' module instead")

def _sign_csr(module):

    if not module.params['common_name']:
        module.fail_json(
            msg="common_name is required for the 'sign-csr' action")

    if not os.path.isfile(module.params['ca_file']):
        module.fail_json(
            msg="no ca.crt file is present at %s. Try 'action=new-ca'" %
            module.params['ca_file'])
    if not os.path.isfile(module.params['csr_file']):
        module.fail_json(
            msg="no csr file is present at %s. Try 'action=new-csr'" %
            module.params['csr_file'])
    if os.path.isfile(module.params['crt_file']) and not module.params['force'
                                                                       ]:
        module.fail_json(
            msg=
            "Certificate already exist for common_name '%s'. Use 'force=yes' to replace"
            % module.params['common_name'])

    cmd = "%s pki sign-csr --csr %s --cert %s" % (
        module.params['icinga2_binary'], module.params['csr_file'],
        module.params['crt_file'])
    run_cmd(module, cmd)
    return 0


def _ticket(module):
    icinga2_binary = get_icinga2_binary(module)
    if not module.params['common_name']:
        module.fail_json(msg="common_name is required for the ticket action")

    if module.params['salt']:
        result, stdout, stderr = module.run_command(
            "%s pki ticket --cn %s --salt %s" %
            (icinga2_binary, module.params['common_name'],
             module.params['salt']))
    else:
        result, stdout, stderr = module.run_command(
            "%s pki ticket --cn %s" %
            (icinga2_binary, module.params['common_name']))

    if re.match(r'critical/cli: Ticket salt.*', stdout, re.S):
        module.fail_json(
            msg="Icinga2 needs salt. Use 'salt=<salt>': %s" % stdout)

    module.exit_json(changed=True, ticket="%s" % stdout.rstrip())



def get_icinga2_binary(module):
    icinga2_binary = module.get_bin_path("icinga2")
    if icinga2_binary is None:
        module.fail_json(
            msg="icinga2 not found. Icinga2 may not be installed.")
    else:
        return icinga2_binary


def remove_files(module):

    if (os.path.isfile(module.params['key_file']) or
        os.path.isfile(module.params['csr_file']) or
        os.path.isfile(module.params['crt_file'])):
        if module.params['force']:
            if os.path.isfile(module.params['key_file']):
                os.unlink(module.params['key_file'])
            if os.path.isfile(module.params['csr_file']):
                os.unlink(module.params['csr_file'])
            if os.path.isfile(module.params['crt_file']):
                os.unlink(module.params['crt_file'])
        else:
            module.fail_json(
                msg=
                "Files already exist for common_name '%s'. Use 'force=yes' to replace"
                % module.params['common_name'])

def run_cmd(module, cmd):
    result, stdout, stderr = module.run_command(cmd)
    if re.match(r'critical/cli: setgroups.*', stdout, re.S):
        module.fail_json(
            msg="This command must be run as root or the 'nagios' user: %s" %
            stdout)
    elif result != 0:
        module.fail_json(msg="Couldn't create %s: %s" % (module.params['action'], stdout))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(
                required=True,
                choices=['new-ca', 'new-key', 'new-csr', 'new-cert',
                         'new-signed-cert', 'request', 'save-cert', 'sign-csr',
                         'ticket']),
            force=dict(type='bool', default='no'),
            common_name=dict(type='str', required=False),
            ca_path=dict(type='str',
                         required=False,
                         default='/var/lib/icinga2/ca'),
            salt=dict(type='str', required=False),
            ),
        )

    module.params['ca_file'] = "%s/ca.crt" % module.params['ca_path']
    module.params['key_file'] = "%s/%s.key" % (module.params['ca_path'],
        module.params['common_name'])
    module.params['csr_file'] = "%s/%s.csr" % (module.params['ca_path'],
        module.params['common_name'])
    module.params['crt_file'] = "%s/%s.crt" % (module.params['ca_path'],
        module.params['common_name'])
    module.params['icinga2_binary'] = get_icinga2_binary(module)

    if module.params['action'] == 'new-ca':
        _new_ca(module)
    if module.params['action'] == 'new-key':
        _new_cert(module)
    if module.params['action'] == 'new-csr':
        _new_cert(module)
    if module.params['action'] == 'new-cert':
        _new_cert(module)
    if module.params['action'] == 'ticket':
        _ticket(module)
    if (module.params['action'] == 'request' or
        module.params['action'] == 'save-cert'):
        _request(module)
    if module.params['action'] == 'sign-csr':
        _sign_csr(module)
    if module.params['action'] == 'new-signed-cert':
        _new_cert(module)
        _sign_csr(module)

    module.exit_json(changed=True)


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
