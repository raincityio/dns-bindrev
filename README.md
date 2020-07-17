## bindrev

The bindrev program taps into dnstap and stores all
dns bindings that it receives, mapping ip to domain.

It stores the latest ip mapping in the storage, which
allows a caller of this program to retrieve the dns
name for an ip address.

The purpose of this program is to allow a caller to
retrieve a "friendly" name for an ip address.  Most
dns these days map to obfuscated names of hosts in ec2
or some other cloud provider, giving value to the
ability to retrieve a friendly version of it.

### requirements

dnstap is required to be running to get the dns entries.
This module can be found here:
 https://github.com/raincityio/dns-dnstap

In addition, mysql is used as the storage backend,
so a mysql module will need to be installed, and a
table setup.

### setup

In order to start the program, a sql table must be
created, the sql schema can be found and modified in
the bindrev/sql directory.

### config

The following is an example configuration, all that
is currently required is that mysql information be
provided.

 {
     "my_host": "mysql_host",
     "my_db": "mysql_db",
     "my_user": "mysql_username",
     "my_password": "mysql_password"
 }
