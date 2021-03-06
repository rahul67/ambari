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

import sys
import fileinput
import shutil
import os
import tempfile
import urllib2
from time import gmtime, strftime
from resource_management import *
from resource_management.core.exceptions import ComponentIsNotRunning
from resource_management.core.logger import Logger
from resource_management.core import shell
from resource_management.libraries.resources.copy_from_local import CopyFromLocal

def setup_spark(env, type, action = None):
  import params

  env.set_params(params)

  _setup_spark_user_group()
  
  Directory([params.spark_pid_dir, params.spark_log_dir, params.spark_conf],
            owner=params.spark_user,
            group=params.user_group,
            recursive=True
  )
  if type == 'server':
    if action == 'start' or action == 'config':
      params.HdfsDirectory(params.spark_hdfs_user_dir,
                         action="create",
                         owner=params.spark_user,
                         mode=0775
      )

  file_path = params.spark_conf + '/spark-defaults.conf'
  create_file(file_path)

  write_properties_to_file(file_path, spark_properties(params))

  # create spark-env.sh in etc/conf dir
  File(os.path.join(params.spark_conf, 'spark-env.sh'),
       owner=params.spark_user,
       group=params.spark_group,
       content=InlineTemplate(params.spark_env_sh)
  )

  #create log4j.properties in etc/conf dir
  File(os.path.join(params.spark_conf, 'log4j.properties'),
       owner=params.spark_user,
       group=params.spark_group,
       content=params.spark_log4j_properties
  )

  #create metrics.properties in etc/conf dir
  File(os.path.join(params.spark_conf, 'metrics.properties'),
       owner=params.spark_user,
       group=params.spark_group,
       content=InlineTemplate(params.spark_metrics_properties)
  )

  File(os.path.join(params.spark_conf, 'java-opts'),
       owner=params.spark_user,
       group=params.spark_group,
       content=params.spark_javaopts_properties
  )

  if params.is_hive_installed:
    hive_config = get_hive_config()
    XmlConfig("hive-site.xml",
              conf_dir=params.spark_conf,
              configurations=hive_config,
              owner=params.spark_user,
              group=params.spark_group,
              mode=0644)

def get_hive_config():
  import params
  hive_conf_dict = dict()
  hive_conf_dict['hive.metastore.uris'] = params.config['configurations']['hive-site']['hive.metastore.uris']
  if params.security_enabled:
    hive_conf_dict['hive.metastore.sasl.enabled'] =  str(params.config['configurations']['hive-site']['hive.metastore.sasl.enabled']).lower()
    hive_conf_dict['hive.metastore.kerberos.keytab.file'] = params.config['configurations']['hive-site']['hive.metastore.kerberos.keytab.file']
    hive_conf_dict['hive.server2.authentication.spnego.principal'] =  params.config['configurations']['hive-site']['hive.server2.authentication.spnego.principal']
    hive_conf_dict['hive.server2.authentication.spnego.keytab'] = params.config['configurations']['hive-site']['hive.server2.authentication.spnego.keytab']
    hive_conf_dict['hive.metastore.kerberos.principal'] = params.config['configurations']['hive-site']['hive.metastore.kerberos.principal']
    hive_conf_dict['hive.server2.authentication.kerberos.principal'] = params.config['configurations']['hive-site']['hive.server2.authentication.kerberos.principal']
    hive_conf_dict['hive.server2.authentication.kerberos.keytab'] =  params.config['configurations']['hive-site']['hive.server2.authentication.kerberos.keytab']
    hive_conf_dict['hive.security.authorization.enabled'] = params.spark_hive_sec_authorization_enabled
    hive_conf_dict['hive.server2.enable.doAs'] =  str(params.config['configurations']['hive-site']['hive.server2.enable.doAs']).lower()

  return hive_conf_dict


def spark_properties(params):
  spark_dict = dict()

  all_spark_config  = params.config['configurations']['spark-defaults']
  #Add all configs unfiltered first to handle Custom case.
  spark_dict = all_spark_config.copy()

  spark_dict['spark.yarn.executor.memoryOverhead'] = params.spark_yarn_executor_memoryOverhead
  spark_dict['spark.yarn.driver.memoryOverhead'] = params.spark_yarn_driver_memoryOverhead
  spark_dict['spark.yarn.applicationMaster.waitTries'] = params.spark_yarn_applicationMaster_waitTries
  spark_dict['spark.yarn.scheduler.heartbeat.interval-ms'] = params.spark_yarn_scheduler_heartbeat_interval
  spark_dict['spark.yarn.max_executor.failures'] = params.spark_yarn_max_executor_failures
  spark_dict['spark.yarn.queue'] = params.spark_yarn_queue
  spark_dict['spark.yarn.containerLauncherMaxThreads'] = params.spark_yarn_containerLauncherMaxThreads
  spark_dict['spark.yarn.submit.file.replication'] = params.spark_yarn_submit_file_replication
  spark_dict['spark.yarn.preserve.staging.files'] = params.spark_yarn_preserve_staging_files

  # Hardcoded paramaters to be added to spark-defaults.conf
  spark_dict['spark.yarn.historyServer.address'] = params.spark_history_server_host + ':' + str(
    params.spark_history_ui_port)
  spark_dict['spark.yarn.services'] = params.spark_yarn_services
  spark_dict['spark.history.provider'] = params.spark_history_provider
  spark_dict['spark.history.ui.port'] = params.spark_history_ui_port

  spark_dict['spark.driver.extraJavaOptions'] = params.spark_driver_extraJavaOptions
  spark_dict['spark.yarn.am.extraJavaOptions'] = params.spark_yarn_am_extraJavaOptions
  if params.spark_yarn_jar.strip():
      spark_dict['spark.yarn.jar'] = params.namenode_address + params.spark_yarn_jar.strip()

  return spark_dict


def write_properties_to_file(file_path, value):
  for key in value:
    modify_config(file_path, key, value[key])


def modify_config(filepath, variable, setting):
  var_found = False
  already_set = False
  V = str(variable)
  S = str(setting)

  if ' ' in S:
    S = '%s' % S

  for line in fileinput.input(filepath, inplace=1):
    if not line.lstrip(' ').startswith('#') and '=' in line:
      _infile_var = str(line.split('=')[0].rstrip(' '))
      _infile_set = str(line.split('=')[1].lstrip(' ').rstrip())
      if var_found == False and _infile_var.rstrip(' ') == V:
        var_found = True
        if _infile_set.lstrip(' ') == S:
          already_set = True
        else:
          line = "%s %s\n" % (V, S)

    sys.stdout.write(line)

  if not var_found:
    with open(filepath, "a") as f:
      f.write("%s \t %s\n" % (V, S))
  elif already_set == True:
    pass
  else:
    pass

  return


def create_file(file_path):
  try:
    file = open(file_path, 'w')
    file.close()
  except:
    print('Unable to create file: ' + file_path)
    sys.exit(0)

def setup_tarball():
    import params
    
    _setup_spark_user_group()
    
    tempdir = tempfile.mkdtemp()
    tarball_name = tempdir + os.sep + "spark.tgz"
    u = urllib2.urlopen(params.spark_tarball_url)
    f = open(tarball_name, 'wb')
    meta = u.info()
    tar_size = meta.getheaders("Content-Length")[0]
    Logger.info("Downloading: %s Bytes: %s" % (tarball_name, tar_size))
    chunk_size = 16*1024
    while True:
        buffer = u.read(chunk_size)
        if not buffer:
            break
        f.write(buffer)
    f.close()
    os.chdir(params.spark_install_location)
    if (os.path.exists(params.spark_install_dir)):
        if params.backup_existing_installation:
            backup_time = strftime("%Y%m%d-%H%M%S")
            backup_dir = params.spark_install_dir + "." + backup_time
            Logger.info("Backing up existing installation at: %s" % (backup_dir))
            shutil.move(params.spark_install_dir, backup_dir)
        else:
            Logger.info("Removing existing installation from: %s" % (params.spark_install_dir))
            shutil.rmtree(params.spark_install_dir)

    Execute(format("tar -xzf {tarball_name}"))
    if (os.path.islink(params.spark_home)):
        Logger.info("Overriding Spark Installation at: %s" % (params.spark_home))
        os.unlink(params.spark_home)
    if (os.path.isdir(params.spark_home)):
        raise Fail("ERROR: Spark Installation Already Exists At: %s" % (params.spark_home))
    os.chdir(os.path.abspath(os.path.join(params.spark_home, os.pardir)))
    os.symlink(params.spark_install_dir, os.path.basename(params.spark_home))
    conf_dir = os.path.join(params.spark_install_dir, "conf")
    if (os.path.isdir(conf_dir)):
        backup_conf = conf_dir + ".orig"
        shutil.move(conf_dir, backup_conf)
    os.chdir(params.spark_install_dir)
    os.symlink(params.spark_conf, "conf")
    
    Execute (format("chown -R root:root {params.spark_install_dir}"))
    
    shutil.rmtree(tempdir)

def _setup_spark_user_group():
    import params

    if params.spark_group:
        Group(params.spark_group, 
              ignore_failures = False
        )
    if params.spark_user:
        User(params.spark_user,
             gid = params.spark_group,
             groups = [params.spark_group, params.user_group],
             ignore_failures = False
        )

def copy_spark_jars_to_hdfs():
    import params
    
    if params.spark_yarn_jar_path_hdfs:
        params.HdfsDirectory(params.spark_yarn_jar_path_hdfs,
                             action="create",
                             owner=params.hdfs_user,
                             group=params.user_group,
                             mode=0755,
                             recursive_chown=True,
                             recursive_chmod=False
                             )
        files = [ f for f in os.listdir(os.path.join(params.spark_install_dir, "lib"))]
        for file in files:
            spark_lib_path = os.path.join(params.spark_install_dir, "lib", file)
            CopyFromLocal(spark_lib_path,
                          dest_dir=params.spark_yarn_jar_path_hdfs,
                          dest_file=file,
                          owner=params.hdfs_user,
                          mode=0644)

