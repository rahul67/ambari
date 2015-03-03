#!/usr/bin/env python

'''
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
'''
from mock.mock import MagicMock, call, patch
from stacks.utils.RMFTestCase import *

@patch("os.path.exists", new = MagicMock(return_value=True))
class TestHBaseClient(RMFTestCase):
  COMMON_SERVICES_PACKAGE_DIR = "HBASE/0.96.0.2.0/package"
  STACK_VERSION = "2.0.6"

  def test_configure_secured(self):
    self.executeScript(self.COMMON_SERVICES_PACKAGE_DIR + "/scripts/hbase_client.py",
                   classname = "HbaseClient",
                   command = "configure",
                   config_file="secured.json",
                   hdp_stack_version = self.STACK_VERSION,
                   target = RMFTestCase.TARGET_COMMON_SERVICES
    )

    self.assertResourceCalled('Directory', '/etc/hbase',
      mode = 0755
    )
    self.assertResourceCalled('Directory', '/etc/hbase/conf',
      owner = 'hbase',
      group = 'hadoop',
      recursive = True,
    )
    self.assertResourceCalled('Directory', '/hadoop/hbase',
      owner = 'hbase',
      mode=0775,
      recursive = True,
      cd_access='a'
    )
    self.assertResourceCalled('Directory', '/hadoop/hbase/local',
      owner = 'hbase',
      group = 'hadoop',
      mode=0775,
      recursive = True,
    )
    self.assertResourceCalled('Directory', '/hadoop/hbase/local/jars',
      owner = 'hbase',
      group = 'hadoop',
      mode=0775,
      recursive = True,
    )
    self.assertResourceCalled('XmlConfig', 'hbase-site.xml',
      owner = 'hbase',
      group = 'hadoop',
      conf_dir = '/etc/hbase/conf',
      configurations = self.getConfig()['configurations']['hbase-site'],
      configuration_attributes = self.getConfig()['configuration_attributes']['hbase-site']
    )
    self.assertResourceCalled('XmlConfig', 'core-site.xml',
      owner = 'hbase',
      group = 'hadoop',
      conf_dir = '/etc/hbase/conf',
      configurations = self.getConfig()['configurations']['core-site'],
      configuration_attributes = self.getConfig()['configuration_attributes']['core-site']
    )
    self.assertResourceCalled('XmlConfig', 'hdfs-site.xml',
      owner = 'hbase',
      group = 'hadoop',
      conf_dir = '/etc/hbase/conf',
      configurations = self.getConfig()['configurations']['hdfs-site'],
      configuration_attributes = self.getConfig()['configuration_attributes']['hdfs-site']
    )
    self.assertResourceCalled('XmlConfig', 'hdfs-site.xml',
      owner = 'hdfs',
      group = 'hadoop',
      conf_dir = '/etc/hadoop/conf',
      configurations = self.getConfig()['configurations']['hdfs-site'],
      configuration_attributes = self.getConfig()['configuration_attributes']['hdfs-site']
    )
    self.assertResourceCalled('File', '/etc/hbase/conf/hbase-policy.xml',
      owner = 'hbase',
      group = 'hadoop',
    )
    self.assertResourceCalled('File', '/etc/hbase/conf/hbase-env.sh',
        content = InlineTemplate(self.getConfig()['configurations']['hbase-env']['content']),
        owner = 'hbase',
    )
    self.assertResourceCalled('TemplateConfig', '/etc/hbase/conf/hadoop-metrics2-hbase.properties',
      owner = 'hbase',
      template_tag = 'GANGLIA-RS',
    )
    self.assertResourceCalled('TemplateConfig', '/etc/hbase/conf/regionservers',
      owner = 'hbase',
      template_tag = None,
    )
    self.assertResourceCalled('TemplateConfig', '/etc/hbase/conf/hbase_client_jaas.conf',
      owner = 'hbase',
      template_tag = None,
    )
    self.assertResourceCalled('File',
                              '/etc/hbase/conf/log4j.properties',
                              mode=0644,
                              group='hadoop',
                              owner='hbase',
                              content='log4jproperties\nline2'
    )
    self.assertNoMoreResources()
    
  def test_configure_default(self):
    self.executeScript(self.COMMON_SERVICES_PACKAGE_DIR + "/scripts/hbase_client.py",
                   classname = "HbaseClient",
                   command = "configure",
                   config_file="default.json",
                   hdp_stack_version = self.STACK_VERSION,
                   target = RMFTestCase.TARGET_COMMON_SERVICES
    )
    self.assertResourceCalled('Directory', '/etc/hbase',
      mode = 0755
    )
    self.assertResourceCalled('Directory', '/etc/hbase/conf',
      owner = 'hbase',
      group = 'hadoop',
      recursive = True,
    )
    self.assertResourceCalled('Directory', '/hadoop/hbase',
      owner = 'hbase',
      mode=0775,
      recursive = True,
      cd_access='a'
    )
    self.assertResourceCalled('Directory', '/hadoop/hbase/local',
      owner = 'hbase',
      group = 'hadoop',
      mode=0775,
      recursive = True,
    )
    self.assertResourceCalled('Directory', '/hadoop/hbase/local/jars',
      owner = 'hbase',
      group = 'hadoop',
      mode=0775,
      recursive = True,
    )
    self.assertResourceCalled('XmlConfig', 'hbase-site.xml',
      owner = 'hbase',
      group = 'hadoop',
      conf_dir = '/etc/hbase/conf',
      configurations = self.getConfig()['configurations']['hbase-site'],
      configuration_attributes = self.getConfig()['configuration_attributes']['hbase-site']
    )
    self.assertResourceCalled('XmlConfig', 'core-site.xml',
      owner = 'hbase',
      group = 'hadoop',
      conf_dir = '/etc/hbase/conf',
      configurations = self.getConfig()['configurations']['core-site'],
      configuration_attributes = self.getConfig()['configuration_attributes']['core-site']
    )
    self.assertResourceCalled('XmlConfig', 'hdfs-site.xml',
      owner = 'hbase',
      group = 'hadoop',
      conf_dir = '/etc/hbase/conf',
      configurations = self.getConfig()['configurations']['hdfs-site'],
      configuration_attributes = self.getConfig()['configuration_attributes']['hdfs-site']
    )
    self.assertResourceCalled('XmlConfig', 'hdfs-site.xml',
      owner = 'hdfs',
      group = 'hadoop',
      conf_dir = '/etc/hadoop/conf',
      configurations = self.getConfig()['configurations']['hdfs-site'],
      configuration_attributes = self.getConfig()['configuration_attributes']['hdfs-site']
    )
    self.assertResourceCalled('File', '/etc/hbase/conf/hbase-policy.xml',
      owner = 'hbase',
      group = 'hadoop',
    )
    self.assertResourceCalled('File', '/etc/hbase/conf/hbase-env.sh',
        content = InlineTemplate(self.getConfig()['configurations']['hbase-env']['content']),
        owner = 'hbase',
    )
    self.assertResourceCalled('TemplateConfig', '/etc/hbase/conf/hadoop-metrics2-hbase.properties',
      owner = 'hbase',
      template_tag = 'GANGLIA-RS',
    )
    self.assertResourceCalled('TemplateConfig', '/etc/hbase/conf/regionservers',
      owner = 'hbase',
      template_tag = None,
    )
    self.assertResourceCalled('File',
                              '/etc/hbase/conf/log4j.properties',
                              mode=0644,
                              group='hadoop',
                              owner='hbase',
                              content='log4jproperties\nline2'
    )
    self.assertNoMoreResources()


  def test_upgrade(self):
    self.executeScript(self.COMMON_SERVICES_PACKAGE_DIR + "/scripts/hbase_client.py",
                   classname = "HbaseClient",
                   command = "restart",
                   config_file="client-upgrade.json",
                   hdp_stack_version = self.STACK_VERSION,
                   target = RMFTestCase.TARGET_COMMON_SERVICES)

    self.assertResourceCalled("Execute", "hdp-select set hbase-client 2.2.1.0-2067")
    self.assertResourceCalled("Execute", "hdp-select set hadoop-client 2.2.1.0-2067")

    # for now, it's enough that hdp-select is confirmed
