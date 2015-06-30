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
from cosmos import cosmos
from cosmos_service import cosmos_service
from status import check_service_status

class CosmosJMX(Script):
  def install(self, env):
    self.install_packages(env)
    self.configure(env)

  def configure(self, env):
    import params
    env.set_params(params)
    cosmos(name='jmx')

  def start(self, env):
    self.configure(env)

    cosmos_service( 'jmx',
                 action = 'start'
    )

  def stop(self, env):
    import params
    env.set_params(params)

    cosmos_service( 'jmx',
                 action = 'stop'
    )

  def status(self, env):
    import status_params
    env.set_params(status_params)
    check_service_status(name='jmx')


if __name__ == "__main__":
  CosmosJMX().execute()

