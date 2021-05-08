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
    s = NaServer(config['filer'], 1, 30)
    s.set_server_type("FILER")
    s.set_transport_type("HTTPS")
    s.set_port(443)
    s.set_style("LOGIN")
    s.set_admin_user(config['username'], config['password'])
    s.set_vserver(config['vserver'])
    s.set_server_cert_verification("False")
    s.set_hostname_verification("False")

    api = NaElement("volume-get-iter")

    xi = NaElement("desired-attributes")
    api.child_add(xi)

    xi1 = NaElement("volume-attributes")
    xi.child_add(xi1)

    xi11 = NaElement("volume-id-attributes")
    xi1.child_add(xi11)
    xi11.child_add_string("name", "name")

    xi27 = NaElement("volume-space-attributes")
    xi1.child_add(xi27)
    xi27.child_add_string("size-total", "<size-total>")
    xi27.child_add_string("percentage-size-used", "<percentage-size-used>")
    api.child_add_string("max-records", "1000")
    xo = s.invoke_elem(api)
    if (xo.results_status() == "failed"):
        print ("Error:\n")
        print (xo.sprintf())
        sys.exit(1)
    else:
        vols = xo.child_get("attributes-list").children_get()
        data = []
        csv_columns = ['name', 'percentage-size-used', 'size-total']
        with open("vol_min.csv", 'w') as volumes:
            writer = csv.DictWriter(volumes, fieldnames=csv_columns)
            writer.writeheader()
            for vol in vols:
                mydict = xmltodict.parse(vol.sprintf())
                if 'volume-space-attributes' not in mydict['volume-attributes']:
                    continue

                dicty = mydict['volume-attributes']['volume-id-attributes'].copy()
                dicty.update(mydict['volume-attributes']['volume-space-attributes'])
                dicty['size-total'] = ('%.0f' % (float(int(dicty['size-total'].strip())) / 1024 / 1024 / 1024))
                dicty['percentage-size-used'] = ('%.0f' % (float(int(dicty['percentage-size-used'].strip())) / 1024 / 1024 / 1024))
                del dicty['owning-vserver-name']
                writer.writerow(dicty)
except Exception, err:
    print Exception, err