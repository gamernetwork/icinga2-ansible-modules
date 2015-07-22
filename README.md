# icinga2-ansible-modules

Modules for the Icinga2 cli. Implemented so far:

 * feature
 * pki

Tested on Debian 8 with Icinga2 from [Debmon](http://debmon.org/).

# Using the pki module to create a CA signed certificate.

Tasks in a play to create a CA signed client certificate:

    - name: create temp cert
      icinga2_pki:
        action: new-cert
        common_name: "{{ ansible_fqdn }}"

    - name: save trusted master cert
      icinga2_pki:
        action: save-cert
        master_host: icinga2.example.com
        common_name: "{{ ansible_fqdn }}"

    - name: get pki ticket
      icinga2_pki:
        action: ticket
        common_name: "{{ ansible_fqdn }}"
      register: icinga_
      delegate_to: icinga2.example.com

    - name: get csr signed by icinga master
      icinga2_pki:
        action: request
        master_host: icinga2.example.com
        zone: test.example.com
        ticket: "{{ icinga.ticket }}"
        common_name: "{{ ansible_fqdn }}"

Alternatively the three client side actions can be rolled up into the
`CA-signed-cert` action:

    - name: CA signed cert for client
      icinga2_pki:
        action: CA-signed-cert
        common_name: "{{ ansible_fqdn }}"
        master_host: icinga2.example.com
        force: yes
        ticket: "{{ icinga.ticket }}"

You'll still need to provide the pki ticket.

# Notes

Icinga2 requires all tasks must be run as root.

Make sure the client pki directory and the master Icinga2 host CA directory are
both writeable by the 'nagios' user. This is required by Icinga2 even though
the tasks are run as root.
