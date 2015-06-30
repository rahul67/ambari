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
from ambari_commons import OSConst
from ambari_commons.os_family_impl import OsFamilyFuncImpl, OsFamilyImpl

@OsFamilyFuncImpl(os_family=OsFamilyImpl.DEFAULT)
def cosmos(name=None):
  import params

  File(os.path.join(params.cosmos_jmx_conf_dir, 'namenode.jmx'),
       owner=params.cosmos_user,
       group=params.cosmos_user,
       mode=0644,
       content=Template("namenode.jmx.j2")
  )

  File(os.path.join(params.cosmos_jmx_conf_dir, 'yarn.jmx'),
       owner=params.cosmos_user,
       group=params.cosmos_user,
       mode=0644,
       content=Template("yarn.jmx.j2")
  )

  File(os.path.join(params.cosmos_jmx_conf_dir, 'datanode.jmx'),
       owner=params.cosmos_user,
       group=params.cosmos_user,
       mode=0644,
       content=Template("datanode.jmx.j2")
  )

  File(os.path.join(params.cosmos_jmx_conf_dir, 'zookeeper.jmx'),
       owner=params.cosmos_user,
       group=params.cosmos_user,
       mode=0644,
       content=Template("zookeeper.jmx.j2")
  )

  pass
