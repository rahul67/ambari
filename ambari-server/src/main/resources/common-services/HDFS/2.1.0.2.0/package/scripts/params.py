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
from ambari_commons import OSCheck
from resource_management.libraries.functions.default import default
from resource_management.libraries.functions.version import compare_versions, format_hdp_stack_version

if OSCheck.is_windows_family():
  from params_windows import *
else:
  from params_linux import *

host_sys_prepped = default("/hostLevelParams/host_sys_prepped", False)

cluster_id = default("/configurations/cluster-env/cluster-id", None)
if cluster_id:
  fmt_cmd = format("namenode -format -clusterid {cluster_id}")
else:
  fmt_cmd = "namenode -format"

# Use the namenode RPC address if configured, otherwise, fallback to the default file system
namenode_address = None
if 'dfs.namenode.rpc-address' in config['configurations']['hdfs-site']:
  namenode_rpcaddress = config['configurations']['hdfs-site']['dfs.namenode.rpc-address']
  namenode_address = [format("hdfs://{namenode_rpcaddress}")]
else:
  namenode_address = [config['configurations']['core-site']['fs.defaultFS']]

# User NameServices for NN addresses if configured. Overrides fs.defaultFS and rpc-address URIs
dfs_ha_nameservices = []
if 'dfs.nameservices' in config['configurations']['hdfs-site']:
  nameservices = config['configurations']['hdfs-site']['dfs.nameservices']
  dfs_ha_nameservices = [ns.strip() for ns in nameservices.split(",")]
  namenode_address = ["hdfs://%s" % ns for ns in dfs_ha_nameservices]

# HDFS High Availability properties
dfs_ha_namenode_ids = {}
for ns in dfs_ha_nameservices:
  dfs_ha_namenode_ids[ns] = default(format("/configurations/hdfs-site/dfs.ha.namenodes.{ns}"), None)
dfs_ha_automatic_failover_enabled = default("/configurations/hdfs-site/dfs.ha.automatic-failover.enabled", False)

dfs_ha_namenode_active = []
dfs_ha_namenode_standby = []
# hostname of the active HDFS HA Namenode (only used when HA is enabled)
init_active = default("/configurations/hadoop-env/dfs_ha_initial_namenode_active", None)
if init_active:
  dfs_ha_namenode_active = [nn.strip() for nn in init_active.split(",")]
# hostname of the standby HDFS HA Namenode (only used when HA is enabled)
init_standby = default("/configurations/hadoop-env/dfs_ha_initial_namenode_standby", None)
if init_standby:
  dfs_ha_namenode_standby = [nn.strip() for nn in init_standby.split(",")]

# Values for the current Host
namenode_id = None
namenode_rpc = None
other_namenode_id = None
current_nn_nsid = None

dfs_ha_namenodes_ids_list = {}
dfs_ha_namenode_ids_array_len = {}
dfs_ha_enabled = {}
hostname_nsid_map = {}

for nsid in dfs_ha_nameservices:
  if dfs_ha_namenode_ids[nsid]:
    dfs_ha_namenodes_ids_list[nsid] = [nnid.strip() for nnid in dfs_ha_namenode_ids[nsid].split(",")]
    if len(dfs_ha_namenodes_ids_list[nsid]) > 1:
      dfs_ha_enabled[nsid] = True
    else:
      dfs_ha_enabled[nsid] = False
  if dfs_ha_enabled[nsid]:
    for nn_id in dfs_ha_namenodes_ids_list[nsid]:
      nn_host = config['configurations']['hdfs-site'][format('dfs.namenode.rpc-address.{nsid}.{nn_id}')]
      hostname_nsid_map[nn_host.split(":")[0].strip()] = nsid
      if hostname in nn_host:
        namenode_id = nn_id
        namenode_rpc = nn_host
        current_nn_nsid = nsid

  if current_nn_nsid:
    # With HA enabled namenode_address is recomputed
    namenode_address = format('hdfs://{current_nn_nsid}')

  # Calculate the namenode id of the other namenode. This is needed during RU to initiate an HA failover using ZKFC.
  if namenode_id is not None and current_nn_nsid is not None and len(dfs_ha_namenodes_ids_list[current_nn_nsid]) == 2:
    other_namenode_id = list(set(dfs_ha_namenodes_ids_list[current_nn_nsid]) - set([namenode_id]))[0]
    
if dfs_http_policy is not None and dfs_http_policy.upper() == "HTTPS_ONLY":
  https_only = True
  journalnode_address = default('/configurations/hdfs-site/dfs.journalnode.https-address', None)
else:
  https_only = False
  journalnode_address = default('/configurations/hdfs-site/dfs.journalnode.http-address', None)

if journalnode_address:
  journalnode_port = journalnode_address.split(":")[1]
  
  
if security_enabled:
  _dn_principal_name = config['configurations']['hdfs-site']['dfs.datanode.kerberos.principal']
  _dn_keytab = config['configurations']['hdfs-site']['dfs.datanode.keytab.file']
  _dn_principal_name = _dn_principal_name.replace('_HOST',hostname.lower())
  
  dn_kinit_cmd = format("{kinit_path_local} -kt {_dn_keytab} {_dn_principal_name};")
  
  _nn_principal_name = config['configurations']['hdfs-site']['dfs.namenode.kerberos.principal']
  _nn_keytab = config['configurations']['hdfs-site']['dfs.namenode.keytab.file']
  _nn_principal_name = _nn_principal_name.replace('_HOST',hostname.lower())
  
  nn_kinit_cmd = format("{kinit_path_local} -kt {_nn_keytab} {_nn_principal_name};")

  _jn_principal_name = default("/configurations/hdfs-site/dfs.journalnode.kerberos.principal", None)
  if _jn_principal_name:
    _jn_principal_name = _jn_principal_name.replace('_HOST', hostname.lower())
  _jn_keytab = default("/configurations/hdfs-site/dfs.journalnode.keytab.file", None)
  jn_kinit_cmd = format("{kinit_path_local} -kt {_jn_keytab} {_jn_principal_name};")
else:
  dn_kinit_cmd = ""
  nn_kinit_cmd = ""
  jn_kinit_cmd = ""

import functools
#create partial functions with common arguments for every HdfsDirectory call
#to create hdfs directory we need to call params.HdfsDirectory in code
# HdfsDirectory = functools.partial(
#   HdfsDirectory,
#   conf_dir=hadoop_conf_dir,
#   hdfs_user=hdfs_user,
#   security_enabled = security_enabled,
#   keytab = hdfs_user_keytab,
#   kinit_path_local = kinit_path_local,
#   bin_dir = hadoop_bin_dir
# )

# The logic for LZO also exists in OOZIE's params.py
io_compression_codecs = default("/configurations/core-site/io.compression.codecs", None)
lzo_enabled = io_compression_codecs is not None and "com.hadoop.compression.lzo" in io_compression_codecs.lower()
lzo_packages = get_lzo_packages(hdp_stack_version)

exclude_packages = []
if not lzo_enabled:
  exclude_packages += lzo_packages
  
name_node_params = default("/commandParams/namenode", None)

#hadoop params
hadoop_env_sh_template = config['configurations']['hadoop-env']['content']

#hadoop-env.sh
java_home = config['hostLevelParams']['java_home']
java_version = int(config['hostLevelParams']['java_version'])

# JMX configuration
namenode_jmx_port = int(default("/configurations/core-site/namenode_jmx_port", 0))
yarn_jmx_port = int(default("/configurations/core-site/yarn_jmx_port", 0))
datanode_jmx_port = int(default("/configurations/core-site/datanode_jmx_port", 0))

if hdp_stack_version != "" and compare_versions(hdp_stack_version, '2.0') >= 0 and compare_versions(hdp_stack_version, '2.1') < 0 and not OSCheck.is_suse_family():
  # deprecated rhel jsvc_path
  jsvc_path = "/usr/libexec/bigtop-utils"
else:
  jsvc_path = "/usr/lib/bigtop-utils"

hadoop_heapsize = config['configurations']['hadoop-env']['hadoop_heapsize']
namenode_heapsize = config['configurations']['hadoop-env']['namenode_heapsize']
namenode_opt_newsize = config['configurations']['hadoop-env']['namenode_opt_newsize']
namenode_opt_maxnewsize = config['configurations']['hadoop-env']['namenode_opt_maxnewsize']
namenode_opt_permsize = format_jvm_option("/configurations/hadoop-env/namenode_opt_permsize","128m")
namenode_opt_maxpermsize = format_jvm_option("/configurations/hadoop-env/namenode_opt_maxpermsize","256m")

jtnode_opt_newsize = "200m"
jtnode_opt_maxnewsize = "200m"
jtnode_heapsize =  "1024m"
ttnode_heapsize = "1024m"

dtnode_heapsize = config['configurations']['hadoop-env']['dtnode_heapsize']
nfsgateway_heapsize = config['configurations']['hadoop-env']['nfsgateway_heapsize']
