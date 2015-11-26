"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

from resource_management.core import shell
from resource_management.core.logger import Logger
from resource_management.libraries.functions.default import default
from resource_management.libraries.functions.jmx import get_value_from_jmx


class NAMENODE_STATE:
  ACTIVE = "active"
  STANDBY = "standby"
  UNKNOWN = "unknown"


class NamenodeHAState:
  """
  Represents the current state of the Namenode Hosts in High Availability Mode
  """

  def __init__(self):
    """
    Initializes all fields by querying the Namenode state.
    Raises a ValueError if unable to construct the object.
    """
    import params

    self.name_services = params.dfs_ha_nameservices
    if len(self.name_services) == 0:
      raise ValueError("Could not retrieve property dfs.nameservices")

#     self.name_service = default("/configurations/hdfs-site/dfs.nameservices", None)
#     if not self.name_service:
#       raise ValueError("Could not retrieve property dfs.nameservices")

    self.nn_unique_ids = params.dfs_ha_namenode_ids
    
    for nsid in self.name_services:
      if not self.nn_unique_ids[nsid]:
        raise ValueError("Could not retrieve property "+join("dfs.ha.namenodes.", str(nsid)))

#     nn_unique_ids_key = "dfs.ha.namenodes." + str(self.name_service)
#     # List of the nn unique ids
#     self.nn_unique_ids = default("/configurations/hdfs-site/" + nn_unique_ids_key, None)
#     if not self.nn_unique_ids:
#       raise ValueError("Could not retrieve property " + nn_unique_ids_key)

#     self.nn_unique_ids = self.nn_unique_ids.split(",")
#     self.nn_unique_ids = [x.strip() for x in self.nn_unique_ids]

    policy = default("/configurations/hdfs-site/dfs.http.policy", "HTTP_ONLY")
    self.encrypted = policy.upper() == "HTTPS_ONLY"

    jmx_uri_fragment = ("https" if self.encrypted else "http") + "://{0}/jmx?qry=Hadoop:service=NameNode,name=FSNamesystem"
    namenode_http_fragment = "dfs.namenode.http-address.{0}.{1}"
    namenode_https_fragment = "dfs.namenode.https-address.{0}.{1}"

    # Dictionary where the key is the Namenode State (e.g., ACTIVE), and the value is a set of hostnames
    self.namenode_state_to_hostnames = {}

    # Dictionary from nn unique id name to a tuple of (http address, https address)
    self.nn_unique_id_to_addresses = {}
    for nsid in self.name_services:
      for nn_unique_id in self.nn_unique_ids[nsid]:
        http_key = namenode_http_fragment.format(nsid, nn_unique_id)
        https_key = namenode_https_fragment.format(nsid, nn_unique_id)

        http_value = default("/configurations/hdfs-site/" + http_key, None)
        https_value = default("/configurations/hdfs-site/" + https_key, None)
        actual_value = https_value if self.encrypted else http_value
        hostname = actual_value.split(":")[0].strip() if actual_value and ":" in actual_value else None

        self.nn_unique_id_to_addresses[nn_unique_id] = (http_value, https_value)
        try:
          if not hostname:
            raise Exception("Could not retrieve hostname from address " + actual_value)

          jmx_uri = jmx_uri_fragment.format(actual_value)
          state = get_value_from_jmx(jmx_uri, "tag.HAState", params.security_enabled, params.hdfs_user, params.is_https_enabled)

          # If JMX parsing failed
          if not state:
            run_user = default("/configurations/hadoop-env/hdfs_user", "hdfs")
            check_service_cmd = "hdfs haadmin -getServiceState {0}".format(nn_unique_id)
            code, out = shell.call(check_service_cmd, logoutput=True, user=run_user)
            if code == 0 and out:
              if NAMENODE_STATE.STANDBY in out:
                state = NAMENODE_STATE.STANDBY
              elif NAMENODE_STATE.ACTIVE in out:
                state = NAMENODE_STATE.ACTIVE

          if not state:
            raise Exception("Could not retrieve Namenode state from URL " + jmx_uri)

          state = state.lower()

          if state not in [NAMENODE_STATE.ACTIVE, NAMENODE_STATE.STANDBY]:
            state = NAMENODE_STATE.UNKNOWN

          if state in self.namenode_state_to_hostnames:
            self.namenode_state_to_hostnames[state].add(hostname)
          else:
            hostnames = set([hostname, ])
            self.namenode_state_to_hostnames[state] = hostnames
        except:
          Logger.error("Could not get namenode state for " + nn_unique_id)

  def __str__(self):
    return "Namenode HA State: {\n" + \
           ("IDs: %s\n"       % ", ".join(self.nn_unique_ids[x] for x in self.nn_unique_ids)) + \
           ("Addresses: %s\n" % str(self.nn_unique_id_to_addresses)) + \
           ("States: %s\n"    % str(self.namenode_state_to_hostnames)) + \
           ("Encrypted: %s\n" % str(self.encrypted)) + \
           ("Healthy: %s\n"   % str(self.is_healthy())) + \
           "}"

  def is_encrypted(self):
    """
    :return: Returns a bool indicating if HTTPS is enabled
    """
    return self.encrypted

  def get_nn_unique_ids(self):
    """
    :return Returns a dict of nameservices containing list of the nn unique ids
    """
    return self.nn_unique_ids

  def get_nn_unique_id_to_addresses(self):
    """
    :return Returns a dictionary where the key is the nn unique id, and the value is a tuple of (http address, https address)
    Each address is of the form, hostname:port
    """
    return self.nn_unique_id_to_addresses

  def get_address_for_nn_id(self, id):
    """
    :param id: Namenode ID
    :return: Returns the appropriate address (HTTP if no encryption, HTTPS otherwise) for the given namenode id.
    """
    if id in self.nn_unique_id_to_addresses:
      addresses = self.nn_unique_id_to_addresses[id]
      if addresses and len(addresses) == 2:
        return addresses[1] if self.encrypted else addresses[0]
    return None

  def get_address_for_host(self, hostname):
    """
    :param hostname: Host name
    :return: Returns the appropriate address (HTTP if no encryption, HTTPS otherwise) for the given host.
    """
    for id, addresses in self.nn_unique_id_to_addresses.iteritems():
      if addresses and len(addresses) == 2:
        if ":" in addresses[0]:
          nn_hostname = addresses[0].split(":")[0].strip()
          if nn_hostname == hostname:
            # Found the host
            return addresses[1] if self.encrypted else addresses[0]
    return None

  def get_namenode_state_to_hostnames(self):
    """
    :return Return a dictionary where the key is a member of NAMENODE_STATE, and the value is a set of hostnames.
    """
    return self.namenode_state_to_hostnames

  def get_address(self, namenode_state):
    """
    @param namenode_state: Member of NAMENODE_STATE
    :return Get the set of addresss that correspond to the hosts with the given state
    """
    hosts = self.namenode_state_to_hostnames[namenode_state] if namenode_state in self.namenode_state_to_hostnames else []
    if hosts and len(hosts) > 0:
      addresses = set()
      for host in hosts:
        addresses.add(self.get_address_for_host(host))
      return addresses
    return None

  def is_healthy(self):
    """
    :return: Returns a bool indicating if no. of ACTIVE and no. of STANDBY hosts are equal to no. of nameservices.
    """
    active_hosts = self.namenode_state_to_hostnames[NAMENODE_STATE.ACTIVE] if NAMENODE_STATE.ACTIVE in self.namenode_state_to_hostnames else []
    standby_hosts = self.namenode_state_to_hostnames[NAMENODE_STATE.STANDBY] if NAMENODE_STATE.STANDBY in self.namenode_state_to_hostnames else []
    return len(active_hosts) == len(standby_hosts) == len(self.name_services)
