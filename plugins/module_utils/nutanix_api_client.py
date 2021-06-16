# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Nutanix
# Copyright: (c) 2021, Balu George <balu.george@nutanix.com>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json

try:
    import requests
    import requests.exceptions
except Exception as e:
    raise Exception(f"Failed to import: {e}")


class NutanixApiError(Exception):
    pass

class NutanixApiClient(object):
    """Nutanix Rest API client"""
    def __init__(self, hostname, username, password, port, validate_certs, **kwargs):
        self.api_base = f"https://{hostname}:{port}/api/nutanix"
        self.auth = (username, password)
        self.validate_certs = validate_certs
        self.session = requests.Session()

    def request(self, api_endpoint, method, data, timeout=5):
        self.api_url = f"{self.api_base}/{api_endpoint}"
        headers = {'Content-Type': 'application/json',  'Accept':'application/json'}
        try:
            response = self.session.request(method=method, url=self.api_url, auth=self.auth, data=data, headers=headers, verify=self.validate_certs, timeout=timeout)
        except requests.exceptions.RequestException as cerr:
            raise NutanixApiError(f"Request failed {str(cerr)}")

        if response.ok:
            return response
        else:
            raise NutanixApiError(f"Request failed to complete, response code {response.status_code}, content {resp.content}")
