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

import os
import socket
import os.path

from resource_management.libraries.functions.check_process_status import check_process_status
from resource_management.core.exceptions import ComponentIsNotRunning
from ambari_commons import OSCheck, OSConst
from ambari_commons.os_family_impl import OsFamilyFuncImpl, OsFamilyImpl

RESULT_CODE_OK = 'OK'
RESULT_CODE_CRITICAL = 'CRITICAL'
RESULT_CODE_UNKNOWN = 'UNKNOWN'

COSMOS_JMX_PID_DIR = '/var/run'

def get_tokens():
  """
  Returns a tuple of tokens in the format {{site/property}} that will be used
  to build the dictionary passed into execute
  """
  return (COSMOS_JMX_PID_DIR,)

@OsFamilyFuncImpl(OsFamilyImpl.DEFAULT)
def is_jmx_process_live(lock_file):
  """
  Gets whether the Cosmos JMX represented by the specified file is running.
  :param lock_file: the lock file of the jmx process to check
  :return: True if the cosmos jmx process is running, False otherwise
  """
  live = False

  if os.path.exists(lock_file):
    live = True

  return live


def execute(parameters=None, host_name=None):
  """
  Returns a tuple containing the result code and a pre-formatted result label

  Keyword arguments:
  parameters (dictionary): a mapping of parameter key to value
  host_name (string): the name of this host where the alert is running
  """

  if parameters is None:
    return (RESULT_CODE_UNKNOWN, ['There were no parameters supplied to the script.'])

  if set([COSMOS_JMX_PID_DIR]).issubset(parameters):
    COSMOS_JMX_LOCK_PATH = os.path.join(parameters[COSMOS_JMX_PID_DIR], 'sv/cosmos-jmx/lock')
  else:
    return (RESULT_CODE_UNKNOWN, ['The cosmos_jmx_pid_dir is a required parameter.'])

  if host_name is None:
    host_name = socket.getfqdn()

  cosmos_jmx_process_running = is_jmx_process_live(COSMOS_JMX_LOCK_PATH)

  alert_state = RESULT_CODE_OK if cosmos_jmx_process_running else RESULT_CODE_CRITICAL

  alert_label = 'Cosmos JMX is running on {0}' if cosmos_jmx_process_running else 'Cosmos JMX is NOT running on {0}'
  alert_label = alert_label.format(host_name)

  return (alert_state, [alert_label])
