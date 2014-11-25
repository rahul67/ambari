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

Ambari Agent

"""

from resource_management import *
import status_params
import partition_tokenizer
import socket

# server configurations
config = Script.get_config()
tmp_dir = Script.get_tmp_dir()

cassandra_service_name = "cassandra"

#RPM versioning support
rpm_version = default("/configurations/hadoop-env/rpm_version", None)

#hadoop params
if rpm_version is not None:
  cassandra_bin = '/usr/hdp/current/cassandra/bin'
  smoke_script = '/usr/hdp/current/cassandra/bin/cassandraCli.sh'
else:
  cassandra_bin = '/usr/lib/cassandra/bin'
  smoke_script = "/usr/lib/cassandra/bin/cassandraCli.sh"

config_dir = "/etc/cassandra"
default_cassandra_dir = "/var/lib/cassandra"
cluster_name = config['configurations']['cassandra-env']['cluster_name']
cassandra_user =  config['configurations']['cassandra-env']['cassandra_user']
hostname = config['hostname']
cassandra_group = config['configurations']['cassandra-env']['cassandra_group']
cassandra_rackdc_template = config['configurations']['cassandra-env']['rackdc_content']

"""
cassandra_env_sh_template = config['configurations']['cassandra-env']['content']
"""
data_file_directories = config['configurations']['cassandra-env']['data_file_directories']
data_file_directories = data_file_directories.split(",")
commitlog_directory = config['configurations']['cassandra-env']['commitlog_directory']
saved_caches_directory = config['configurations']['cassandra-env']['saved_caches_directory']
cassandra_log_dir = config['configurations']['cassandra-env']['cassandra_log_dir']
cassandra_pid_dir = status_params.cassandra_pid_dir
cassandra_pid_file = status_params.cassandra_pid_file

"""
cassandra_server_heapsize = "-Xmx1024m"
"""

seed_provider = config['configurations']['cassandra-env']['seed_provider']
thrift_framed_transport_size_in_mb = config['configurations']['cassandra-env']['thrift_framed_transport_size_in_mb']
thrift_max_message_length_in_mb = config['configurations']['cassandra-env']['thrift_max_message_length_in_mb']
endpoint_snitch = config['configurations']['cassandra-env']['endpoint_snitch']
commitlog_sync = config['configurations']['cassandra-env']['commitlog_sync']
commitlog_sync_batch_window_in_ms = config['configurations']['cassandra-env']['commitlog_sync_batch_window_in_ms']
partitioner = config['configurations']['cassandra-env']['partitioner']
rpc_server_type = config['configurations']['cassandra-env']['rpc_server_type']

java64_home = config['hostLevelParams']['java_home']

cassandra_hosts = config['clusterHostInfo']['cassandra_hosts']
cassandra_hosts.sort()

currentHostIndex = sorted(cassandra_hosts).index(hostname)

"""
Dynamic variables for cassandra.yaml.
"""
initial_token = partition_tokenizer.getToken(partitioner, len(cassandra_hosts), currentHostIndex)
listen_address = socket.gethostbyname(hostname)
seeds = socket.gethostbyname(sorted(cassandra_hosts)[0])
rpc_address = listen_address

smokeuser = config['configurations']['cluster-env']['smokeuser']
