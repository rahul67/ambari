# !/usr/bin/env python
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
def cosmos_service(name, action):
  import params

  if name == 'collectd':
    cmd = format("{cosmos_collectd_script}")
    #no_op_test should be much more complex to work with cumulative status of collectd
    #removing as startup script handle it also
    #no_op_test = format("ls {pid_file} >/dev/null 2>&1 && ps `cat {pid_file}` >/dev/null 2>&1")

    if action == 'start':
      daemon_cmd = format("{cmd} start")
      Execute(daemon_cmd,
              user=params.cosmos_user
      )

      pass
    elif action == 'stop':
      daemon_cmd = format("{cmd} stop")
      Execute(daemon_cmd,
              user=params.cosmos_user
      )

      pass
    pass
  elif name == 'jmx':
    cmd = format("{cosmos_jmx_script}")

    if action == 'start':
      daemon_cmd = format("{cmd} start")
      Execute(daemon_cmd,
              user=params.cosmos_user
      )

      pass
    elif action == 'stop':

      daemon_cmd = format("{cmd} stop")
      Execute(daemon_cmd,
              user=params.cosmos_user
      )

      pass
    pass
  pass
