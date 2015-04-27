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


def setup_zeppelin(env, type, action = None):
  import params

  env.set_params(params)

  _setup_zeppelin_user_group()
  
  Directory([params.zeppelin_pid_dir, params.zeppelin_log_dir, params.zeppelin_conf,
             params.zeppelin_notebook_dir, params.zeppelin_ssl_keystore_path,
             params.zeppelin_ssl_truststore_path],
            owner=params.zeppelin_user,
            group=params.user_group,
            recursive=True
  )
  if type == 'server':
    if action == 'start' or action == 'config':
      params.HdfsDirectory(params.zeppelin_hdfs_user_dir,
                         action="create",
                         owner=params.zeppelin_user,
                         mode=0775
      )
    if action == 'config':
      interpreter = os.path.join(params.zeppelin_conf, "interpreter.json")
      if os.path.exists(interpreter):
          os.remove(interpreter)

  XmlConfig( "zeppelin-site.xml",
            conf_dir = params.zeppelin_conf,
            configurations = params.config['configurations']['zeppelin-site'],
            configuration_attributes=params.config['configuration_attributes']['zeppelin-site'],
            owner = params.zeppelin_user,
            group = params.zeppelin_group
  )

  # create zeppelin-env.sh in etc/conf dir
  File(os.path.join(params.zeppelin_conf, 'zeppelin-env.sh'),
       owner=params.zeppelin_user,
       group=params.zeppelin_group,
       content=InlineTemplate(params.zeppelin_env_sh)
  )

  #create log4j.properties in etc/conf dir
  File(os.path.join(params.zeppelin_conf, 'log4j.properties'),
       owner=params.zeppelin_user,
       group=params.zeppelin_group,
       content=params.zeppelin_log4j_properties
  )

  if params.is_hive_installed:
    hive_config = get_hive_config()
    XmlConfig("hive-site.xml",
              conf_dir=params.zeppelin_conf,
              configurations=hive_config,
              owner=params.zeppelin_user,
              group=params.zeppelin_group,
              mode=0644)

def get_hive_config():
  import params
  hive_conf_dict = dict()
  hive_conf_dict['hive.metastore.uris'] = params.config['configurations']['hive-site']['hive.metastore.uris']

  # These Params don't matter much here as setup is not kerberos compatible.
  """
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
  """

  return hive_conf_dict


def setup_tarball():
    import params
    
    _setup_zeppelin_user_group()
    
    tempdir = tempfile.mkdtemp()
    tarball_name = tempdir + os.sep + "zeppelin.tgz"
    u = urllib2.urlopen(params.zeppelin_tarball_url)
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
    os.chdir(params.zeppelin_install_location)
    if (os.path.exists(params.zeppelin_install_dir)):
        if params.backup_existing_installation:
            backup_time = strftime("%Y%m%d-%H%M%S")
            backup_dir = params.zeppelin_install_dir + "." + backup_time
            Logger.info("Backing up existing installation at: %s" % (backup_dir))
            shutil.move(params.zeppelin_install_dir, backup_dir)
        else:
            Logger.info("Removing existing installation from: %s" % (params.zeppelin_install_dir))
            shutil.rmtree(params.zeppelin_install_dir)

    Execute(format("tar -xzf {tarball_name}"))
    if (os.path.islink(params.zeppelin_home)):
        Logger.info("Overriding Zeppelin Installation at: %s" % (params.zeppelin_home))
        os.unlink(params.zeppelin_home)
    if (os.path.isdir(params.zeppelin_home)):
        raise Fail("ERROR: Zeppelin Installation Already Exists At: %s" % (params.zeppelin_home))
    os.chdir(os.path.abspath(os.path.join(params.zeppelin_home, os.pardir)))
    os.symlink(params.zeppelin_install_dir, os.path.basename(params.zeppelin_home))
    conf_dir = os.path.join(params.zeppelin_install_dir, "conf")
    if (os.path.isdir(conf_dir)):
        backup_conf = conf_dir + ".orig"
        shutil.move(conf_dir, backup_conf)
    os.chdir(params.zeppelin_install_dir)
    os.symlink(params.zeppelin_conf, "conf")
    
    Execute (format("chown -R root:root {params.zeppelin_install_dir}"))
    
    shutil.rmtree(tempdir)

def _setup_zeppelin_user_group():
    import params

    if params.zeppelin_group:
        Group(params.zeppelin_group, 
              ignore_failures = False
        )
    if params.zeppelin_user:
        User(params.zeppelin_user,
             gid = params.zeppelin_group,
             groups = [params.zeppelin_group, params.user_group],
             ignore_failures = False
        )
