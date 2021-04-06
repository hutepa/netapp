#!/usr/bin/env python

import sys
import ssl
import xmltodict
#import json
import csv
import os.path
from collections import OrderedDict
import time

sys.path.append("../NetApp")
from NaServer import *

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

try:
    s = NaServer("IP_HERE", 1, 110)
    s.set_server_type("FILER")
    s.set_transport_type("HTTPS")
    s.set_port(443)
    s.set_style("LOGIN")
    s.set_admin_user("USER_HERE", "PASS_HERE")
    #s.set_vserver("VSERVER_HERE")
    s.set_server_cert_verification("False")
    s.set_hostname_verification("False")

    api = NaElement("lun-map-get-iter")

    xi = NaElement("desired-attributes")
    api.child_add(xi)

    xi1 = NaElement("lun-map-info")
    xi.child_add(xi1)

    xi1.child_add_string("initiator-group", "<initiator-group>")
    xi1.child_add_string("path", "<path>")

    api.child_add_string("max-records", "20000")
    xo = s.invoke_elem(api)
    mapy = {}

    if (xo.results_status() == "failed"):
        print ("Error:\n")
        print (xo.sprintf())
        sys.exit(1)
    else:
        maps = xo.child_get("attributes-list").children_get()
        for child in maps:
            map_dict = xmltodict.parse(child.sprintf())
            map_info = map_dict['lun-map-info']
            mapy[str(map_info['path'])] = str(map_info['initiator-group'])

    time.sleep(10)
    api2 = NaElement("lun-get-iter")

    xii = NaElement("desired-attributes")
    api2.child_add(xii)

    xi2 = NaElement("lun-info")
    xii.child_add(xi2)

    xi2.child_add_string("path", "<path>")

    xi2.child_add_string("size", "<size>")
    xi2.child_add_string("size-used", "<size-used>")
    xi2.child_add_string("volume", "<volume>")
    xi2.child_add_string("multiprotocol-type", "<multiprotocol-type>")

    xi3 = NaElement("query")
    api2.child_add(xi3)

    xi4 = NaElement("lun-info")
    xi3.child_add(xi4)
    
    xi4.child_add_string("multiprotocol-type","linux")

    api2.child_add_string("max-records", "2000")

    xoo = s.invoke_elem(api2)

    if (xoo.results_status() == "failed"):
        print ("Error:\n")
        print (xoo.sprintf())
        sys.exit(1)

    else:
        print (xoo.sprintf())
        luns = xoo.child_get("attributes-list").children_get()
        csv_columns = ['path', 'size', 'size-used', 'volume', 'multiprotocol-type', 'igroup']

        with open("linux_map.csv", 'w') as linux_map:
            writer = csv.DictWriter(linux_map, fieldnames=csv_columns)
            writer.writeheader()
            for lun in luns:
                lun_dict = xmltodict.parse(lun.sprintf())
                luny = lun_dict['lun-info'].copy()
                luny['size'] = ('%.0f' % (float(int(luny['size'].strip())) / 1024 / 1024 / 1024))
                luny['size-used'] = ('%.0f' % (float(int(luny['size-used'].strip())) / 1024 / 1024 / 1024))
                del luny['qtree']
                del luny['vserver']
                if luny['path'] in mapy.iterkeys():
                    luny['igroup'] = mapy[luny['path']]
                else:
                    continue
                writer.writerow(luny)

except Exception, err:
    print Exception, err
