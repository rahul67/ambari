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
import os

from resource_management import *
import sys
from ambari_commons import OSConst
from ambari_commons.os_family_impl import OsFamilyFuncImpl, OsFamilyImpl

@OsFamilyFuncImpl(os_family=OsFamilyImpl.DEFAULT)
def zookeeper(type = None):
  import params

  Directory(params.config_dir,
            owner=params.zk_user,
            recursive=True,
            group=params.user_group
  )

  File(os.path.join(params.config_dir, "zookeeper-env.sh"),
       content=InlineTemplate(params.zk_env_sh_template),
       owner=params.zk_user,
       group=params.user_group
  )
  

  configFile("zoo.cfg", template_name="zoo.cfg.j2")
  configFile("configuration.xsl", template_name="configuration.xsl.j2")

  Directory(params.zk_pid_dir,
            owner=params.zk_user,
            recursive=True,
            group=params.user_group
  )

  Directory(params.zk_log_dir,
            owner=params.zk_user,
            recursive=True,
            group=params.user_group
  )

  Directory(params.zk_data_dir,
            owner=params.zk_user,
            recursive=True,
            cd_access="a",
            group=params.user_group
  )

  if type == 'server':
    myid = str(sorted(params.zookeeper_hosts).index(params.hostname) + 1)

    File(os.path.join(params.zk_data_dir, "myid"),
         mode = 0644,
         content = myid
    )

  if (params.log4j_props != None):
    File(os.path.join(params.config_dir, "log4j.properties"),
         mode=0644,
         group=params.user_group,
         owner=params.zk_user,
         content=params.log4j_props
    )
  elif (os.path.exists(os.path.join(params.config_dir, "log4j.properties"))):
    File(os.path.join(params.config_dir, "log4j.properties"),
         mode=0644,
         group=params.user_group,
         owner=params.zk_user
    )

  if params.security_enabled:
    if type == "server":
      configFile("zookeeper_jaas.conf", template_name="zookeeper_jaas.conf.j2")
      configFile("zookeeper_client_jaas.conf", template_name="zookeeper_client_jaas.conf.j2")
    else:
      configFile("zookeeper_client_jaas.conf", template_name="zookeeper_client_jaas.conf.j2")

  File(os.path.join(params.config_dir, "zoo_sample.cfg"),
       owner=params.zk_user,
       group=params.user_group
  )

@OsFamilyFuncImpl(os_family=OSConst.WINSRV_FAMILY)
def zookeeper(type = None):
  import params
  configFile("zoo.cfg", template_name="zoo.cfg.j2", mode="f")
  configFile("configuration.xsl", template_name="configuration.xsl.j2", mode="f")

  Directory(params.zk_data_dir,
            owner=params.zk_user,
            mode="(OI)(CI)F",
            recursive=True
  )
  if (params.log4j_props != None):
    File(os.path.join(params.config_dir, "log4j.properties"),
         mode="f",
         owner=params.zk_user,
         content=params.log4j_props
    )
  elif (os.path.exists(os.path.join(params.config_dir, "log4j.properties"))):
    File(os.path.join(params.config_dir, "log4j.properties"),
         mode="f",
         owner=params.zk_user
    )
  if type == 'server':
    myid = str(sorted(params.zookeeper_hosts).index(params.hostname) + 1)
    File(os.path.join(params.zk_data_dir, "myid"),
         owner=params.zk_user,
         mode = "f",
         content = myid
    )

def configFile(name, template_name=None, mode=None):
  import params

  File(os.path.join(params.config_dir, name),
       content=Template(template_name),
       owner=params.zk_user,
       group=params.user_group,
       mode=mode
  )



