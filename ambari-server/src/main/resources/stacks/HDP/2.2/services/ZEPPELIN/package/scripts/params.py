#!/usr/bin/python
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

from resource_management.libraries.functions.version import format_hdp_stack_version, compare_versions
from resource_management.libraries.functions.default import default
from resource_management import *
from setup_zeppelin import *
import status_params
import re

config = Script.get_config()
tmp_dir = Script.get_tmp_dir()

stack_name = default("/hostLevelParams/stack_name", None)
stack_version_unformatted = str(config['hostLevelParams']['stack_version'])
hdp_stack_version = format_hdp_stack_version(stack_version_unformatted)

# Params from zeppelin-env
zeppelin_tarball_url = config['configurations']['zeppelin-env']['zeppelin_tarball_url']
zeppelin_install_location = "/usr/hdp/2.2.0.0-2041"
zeppelin_extracted_dir = re.sub('\.tgz$', '', zeppelin_tarball_url.split('/')[-1])
zeppelin_extracted_dir = re.sub('\.tar\.gz$', '', zeppelin_extracted_dir)
zeppelin_install_dir = zeppelin_install_location + os.sep + zeppelin_extracted_dir
backup_existing_installation = default("/configurations/zeppelin-env/backup_existing_installation", True)

zeppelin_yarn_queue = default("/configurations/zeppelin-env/zeppelin_yarn_queue", "default")
zeppelin_log_dir = config['configurations']['zeppelin-env']['zeppelin_log_dir']
zeppelin_pid_dir = config['configurations']['zeppelin-env']['zeppelin_pid_dir']
spark_master = config['configurations']['zeppelin-env']['spark_master']
backup_existing_installation = default("/configurations/zeppelin-env/backup_existing_installation", True)

spark_jobhistoryserver_hosts = default("/clusterHostInfo/spark_jobhistoryserver_hosts", [])

if len(spark_jobhistoryserver_hosts) > 0:
  spark_history_server_host = spark_jobhistoryserver_hosts[0]
else:
  spark_history_server_host = "localhost"

spark_history_ui_port = default("/configurations/spark-defaults/spark.history.ui.port", "18080")

zeppelin_java_opts = config['configurations']['zeppelin-env']['zeppelin_java_opts']
# Append Spark options from spark-defaults to zeppelin_java_opts to pass on to SparkContext
spark_defaults = config['configurations']['spark-defaults'].copy()
spark_defaults['spark.yarn.queue'] = zeppelin_yarn_queue
spark_defaults['spark.yarn.historyServer.address'] = spark_history_server_host + ':' + str(spark_history_ui_port)
spark_opts_for_zeppelin = ""
for key in spark_defaults:
    val = str(spark_defaults[key])
    val = val.strip()
    if val:
        spark_opts_for_zeppelin = spark_opts_for_zeppelin + " -D" + key + "=" + val

# Append explicit Zeppelin Java Options to the end so they take precedence
# overriding previous ones.
zeppelin_java_opts = spark_opts_for_zeppelin + " " + zeppelin_java_opts

zeppelin_intp_java_opts = config['configurations']['zeppelin-env']['zeppelin_intp_java_opts']
zeppelin_mem = config['configurations']['zeppelin-env']['zeppelin_mem']
zeppelin_intp_mem = config['configurations']['zeppelin-env']['zeppelin_intp_mem']
zeppelin_niceness = config['configurations']['zeppelin-env']['zeppelin_niceness']
zeppelin_server_port = config['configurations']['zeppelin-site']['zeppelin.server.port']
spark_yarn_jar = config['configurations']['zeppelin-env']['spark_yarn_jar']
spark_yarn_jar = spark_yarn_jar.strip()

hadoop_home = "/usr/hdp/current/hadoop-client"
hadoop_bin_dir = "/usr/hdp/current/hadoop-client/bin"
zeppelin_conf = '/etc/zeppelin/conf'
zeppelin_home = '/usr/hdp/current/zeppelin'

zeppelin_notebook_dir = default("/configurations/zeppelin-site/zeppelin.notebook.dir", format("{zeppelin_home}/notebooks"))
zeppelin_interpreter_dir = default("/configurations/zeppelin-site/zeppelin.interpreter.dir", format("{zeppelin_home}/interpreter"))
zeppelin_ssl_keystore_path = default("/configurations/zeppelin-site/zeppelin.ssl.keystore.path", format("{zeppelin_home}/keystore"))
zeppelin_ssl_truststore_path = default("/configurations/zeppelin-site/zeppelin.ssl.truststore.path", format("${zeppelin_home}/truststore"))

java_home = config['hostLevelParams']['java_home']
hadoop_conf_dir = "/etc/hadoop/conf"
hdfs_user = config['configurations']['hadoop-env']['hdfs_user']

zeppelin_user = status_params.zeppelin_user
zeppelin_group = status_params.zeppelin_group
user_group = status_params.user_group

zeppelin_hdfs_user_dir = format("/user/{zeppelin_user}")

zeppelin_server_start = format("{zeppelin_home}/bin/zeppelin-daemon.sh start")
zeppelin_server_stop = format("{zeppelin_home}/bin/zeppelin-daemon.sh stop")

zeppelin_server_hosts = default("/clusterHostInfo/zeppelin_server_hosts", [])

if len(zeppelin_server_hosts) > 0:
  zeppelin_server_host = zeppelin_server_hosts[0]
else:
  zeppelin_server_host = "localhost"

zeppelin_server_pid_file = format("{zeppelin_pid_dir}/zeppelin-{zeppelin_user}-{zeppelin_server_host}.pid")

zeppelin_env_sh = config['configurations']['zeppelin-env']['content']
zeppelin_log4j_properties = config['configurations']['zeppelin-log4j-properties']['content']

hive_server_host = default("/clusterHostInfo/hive_server_host", [])
is_hive_installed = not len(hive_server_host) == 0

security_enabled = config['configurations']['cluster-env']['security_enabled']
kinit_path_local = ""


import functools
#create partial functions with common arguments for every HdfsDirectory call
#to create hdfs directory we need to call params.HdfsDirectory in code
HdfsDirectory = functools.partial(
  HdfsDirectory,
  conf_dir=hadoop_conf_dir,
  hdfs_user=hdfs_user,
  security_enabled = security_enabled,
  keytab = '',
  kinit_path_local = kinit_path_local,
  bin_dir = hadoop_bin_dir
)

