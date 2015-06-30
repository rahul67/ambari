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

from resource_management.core.logger import Logger
from resource_management.core.base import Fail
from resource_management import Script
from resource_management import *

from ambari_commons import OSConst
from ambari_commons.os_family_impl import OsFamilyFuncImpl, OsFamilyImpl


class CosmosServiceCheck(Script):

  @OsFamilyFuncImpl(os_family=OsFamilyImpl.DEFAULT)
  def service_check(self, env):
    import params

    Logger.info("Cosmos service check was started.")
    env.set_params(params)

    collectd_check_cmd = format("{cosmos_collectd_script} status")
    jmx_check_cmd = format("{cosmos_jmx_script} status")
  
    Execute( collectd_check_cmd,
      tries     = 3,
      try_sleep = 5,
      user = params.cosmos_user,
      logoutput = True
    )
  
    Execute ( jmx_check_cmd,
      tries     = 3,
      try_sleep = 5,
      user = params.cosmos_user,
      logoutput = True
    )
    

    Logger.info("Cosmos service check is finished.")

if __name__ == "__main__":
  CosmosServiceCheck().execute()

