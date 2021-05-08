#!/usr/bin/env python

import yaml
import sys
import ssl
import xmltodict
import csv

sys.path.append("NetApp")
from NaServer import *

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

with open('config.yml') as stream:
    config = yaml.safe_load(stream)
    
try:
    s = NaServer(config['filer'], 1, 110)
    s.set_server_type("FILER")
    s.set_transport_type("HTTPS")
    s.set_port(443)
    s.set_style("LOGIN")
    s.set_admin_user(config['username'], config['password'])
    #s.set_vserver(config['vserver'])
    s.set_server_cert_verification("False")
    s.set_hostname_verification("False")

    api = NaElement("lun-get-iter")

    xi = NaElement("desired-attributes")
    api.child_add(xi)

    xi1 = NaElement("lun-info")
    xi.child_add(xi1)

    xi1.child_add_string("path", "<path>")
    xi1.child_add_string("volume", "<volume>")
    xi1.child_add_string("multiprotocol-type", "<multiprotocol-type>")
    xi1.child_add_string("mapped", "<mapped>")
    
    xi2 = NaElement("query")
    api.child_add(xi2)

    xi3 = NaElement("lun-info")
    xi2.child_add(xi3)

    xi3.child_add_string("multiprotocol-type", "linux")
    xi3.child_add_string("mapped", "false")

    api.child_add_string("max-records", "2000")
    xo = s.invoke_elem(api)
    if (xo.results_status() == "failed"):
        print ("Error:\n")
        print (xo.sprintf())
        sys.exit(1)
    else:
        luns = xo.child_get("attributes-list").children_get()
        csv_columns = ['path', 'volume', 'multiprotocol-type', 'mapped']
        with open("D4_unmapped.csv", 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
            writer.writeheader()
            for lun in luns:
                mydict = xmltodict.parse(lun.sprintf())
                dicty = mydict['lun-info'].copy()
                del dicty['qtree']
                del dicty['vserver']
                writer.writerow(dicty)
except Exception, err:
    print(Exception + err)