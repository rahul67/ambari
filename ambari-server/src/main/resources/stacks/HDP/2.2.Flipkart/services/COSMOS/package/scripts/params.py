#!/usr/bin/env python
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

from resource_management import *
import status_params
from ambari_commons import OSCheck

# server configurations
config = Script.get_config()
exec_tmp_dir = Script.get_tmp_dir()

#Cosmos data
cosmos_pid_dir = status_params.cosmos_pid_dir
cosmos_collectd_pid_file = status_params.cosmos_collectd_pid_file
cosmos_jmx_lock_file = status_params.cosmos_jmx_lock_file

cosmos_user = config['configurations']['cosmos-env']['cosmos_user']
cosmos_jmx_conf_dir = config['configurations']['cosmos-env']['cosmos_jmx_conf_dir']

cosmos_jmx_script = "/etc/init.d/cosmos-jmx"
cosmos_collectd_script = "/etc/init.d/cosmos-collectd"

cosmos_service_name = default("/configurations/cosmos-env/cosmos_service_name", "test")

# JMX configuration
namenode_jmx_port = int(default("/configurations/core-site/namenode_jmx_port", 0))
yarn_jmx_port = int(default("/configurations/core-site/yarn_jmx_port", 0))
datanode_jmx_port = int(default("/configurations/core-site/datanode_jmx_port", 0))
zookeeper_jmx_port = int(default("/configurations/zoo.cfg/zookeeper_jmx_port", 0))

# JMX Templates
namenode_json_template = config['configurations']['cosmos-env']['jmx-namenode-content']
datanode_json_template = config['configurations']['cosmos-env']['jmx-datanode-content']
yarn_json_template = config['configurations']['cosmos-env']['jmx-yarn-content']
zookeeper_json_template = config['configurations']['cosmos-env']['jmx-zookeeper-content']

hostname = status_params.hostname

