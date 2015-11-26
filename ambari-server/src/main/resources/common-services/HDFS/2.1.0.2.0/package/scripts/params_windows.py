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

import os

#Used in subsequent imports from params
from install_params import exclude_packages
from status_params import *

config = Script.get_config()
hadoop_conf_dir = None
hbase_conf_dir = None
hadoop_home = None
try:
  hadoop_conf_dir = os.environ["HADOOP_CONF_DIR"]
  hbase_conf_dir = os.environ["HBASE_CONF_DIR"]
  hadoop_home = os.environ["HADOOP_HOME"]
except:
  pass
#directories & files
dfs_name_dir = config['configurations']['hdfs-site']['dfs.namenode.name.dir']
fs_checkpoint_dir = config['configurations']['hdfs-site']['dfs.namenode.checkpoint.dir']
dfs_data_dir = config['configurations']['hdfs-site']['dfs.datanode.data.dir']
#decomission
hdfs_exclude_file = default("/clusterHostInfo/decom_dn_hosts", [])
exclude_file_path = config['configurations']['hdfs-site']['dfs.hosts.exclude']

hadoop_user = config["configurations"]["cluster-env"]["hadoop.user.name"]
hdfs_user = hadoop_user

grep_exe = "findstr"

name_node_params = default("/commandParams/namenode", None)

service_map = {
  "datanode" : datanode_win_service_name,
  "journalnode" : journalnode_win_service_name,
  "namenode" : namenode_win_service_name,
  "secondarynamenode" : snamenode_win_service_name,
  "zkfc_slave": zkfc_win_service_name
}
