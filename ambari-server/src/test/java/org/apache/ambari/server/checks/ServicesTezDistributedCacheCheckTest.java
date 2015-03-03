/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.ambari.server.checks;

import java.util.HashMap;
import java.util.Map;

import org.apache.ambari.server.ServiceNotFoundException;
import org.apache.ambari.server.controller.PrereqCheckRequest;
import org.apache.ambari.server.state.Cluster;
import org.apache.ambari.server.state.Clusters;
import org.apache.ambari.server.state.Config;
import org.apache.ambari.server.state.DesiredConfig;
import org.apache.ambari.server.state.Service;
import org.apache.ambari.server.state.stack.PrereqCheckStatus;
import org.apache.ambari.server.state.stack.PrerequisiteCheck;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.mockito.Mockito;

import com.google.inject.Provider;

/**
 * Unit tests for ServicesTezDistributedCacheCheck
 *
 */
public class ServicesTezDistributedCacheCheckTest {
  private final Clusters clusters = Mockito.mock(Clusters.class);

  private final ServicesTezDistributedCacheCheck servicesTezDistributedCacheCheck = new ServicesTezDistributedCacheCheck();

  @Before
  public void setup() {
    servicesTezDistributedCacheCheck.clustersProvider = new Provider<Clusters>() {

      @Override
      public Clusters get() {
        return clusters;
      }
    };
  }

  @Test
  public void testIsApplicable() throws Exception {
    final Cluster cluster = Mockito.mock(Cluster.class);
    Mockito.when(cluster.getClusterId()).thenReturn(1L);
    Mockito.when(clusters.getCluster("cluster")).thenReturn(cluster);

    final Service service = Mockito.mock(Service.class);
    Mockito.when(cluster.getService("TEZ")).thenReturn(service);
    Assert.assertTrue(servicesTezDistributedCacheCheck.isApplicable(new PrereqCheckRequest("cluster")));

    PrereqCheckRequest req = new PrereqCheckRequest("cluster");
    req.addResult(CheckDescription.SERVICES_NAMENODE_HA, PrereqCheckStatus.FAIL);
    Mockito.when(cluster.getService("TEZ")).thenReturn(service);
    Assert.assertFalse(servicesTezDistributedCacheCheck.isApplicable(req));

    req.addResult(CheckDescription.SERVICES_NAMENODE_HA, PrereqCheckStatus.PASS);
    Mockito.when(cluster.getService("TEZ")).thenReturn(service);
    Assert.assertTrue(servicesTezDistributedCacheCheck.isApplicable(req));


    Mockito.when(cluster.getService("TEZ")).thenThrow(new ServiceNotFoundException("no", "service"));
    Assert.assertFalse(servicesTezDistributedCacheCheck.isApplicable(new PrereqCheckRequest("cluster")));


  }

  @Test
  public void testPerform() throws Exception {
    final Cluster cluster = Mockito.mock(Cluster.class);
    Mockito.when(cluster.getClusterId()).thenReturn(1L);
    Mockito.when(clusters.getCluster("cluster")).thenReturn(cluster);

    final DesiredConfig desiredConfig = Mockito.mock(DesiredConfig.class);
    Mockito.when(desiredConfig.getTag()).thenReturn("tag");
    Map<String, DesiredConfig> configMap = new HashMap<String, DesiredConfig>();
    configMap.put("tez-site", desiredConfig);
    configMap.put("core-site", desiredConfig);
    Mockito.when(cluster.getDesiredConfigs()).thenReturn(configMap);
    final Config config = Mockito.mock(Config.class);
    Mockito.when(cluster.getConfig(Mockito.anyString(), Mockito.anyString())).thenReturn(config);
    final Map<String, String> properties = new HashMap<String, String>();
    Mockito.when(config.getProperties()).thenReturn(properties);

    PrerequisiteCheck check = new PrerequisiteCheck(null, null);
    servicesTezDistributedCacheCheck.perform(check, new PrereqCheckRequest("cluster"));
    Assert.assertEquals(PrereqCheckStatus.FAIL, check.getStatus());

    properties.put("fs.defaultFS", "anything");
    properties.put("tez.lib.uris", "hdfs://some/path/to/archive.tar.gz");
    properties.put("tez.use.cluster.hadoop-libs", "false");
    check = new PrerequisiteCheck(null, null);
    servicesTezDistributedCacheCheck.perform(check, new PrereqCheckRequest("cluster"));
    Assert.assertEquals(PrereqCheckStatus.PASS, check.getStatus());

    properties.put("fs.defaultFS", "anything");
    properties.put("tez.lib.uris", "dfs://some/path/to/archive.tar.gz");
    properties.put("tez.use.cluster.hadoop-libs", "false");
    check = new PrerequisiteCheck(null, null);
    servicesTezDistributedCacheCheck.perform(check, new PrereqCheckRequest("cluster"));
    Assert.assertEquals(PrereqCheckStatus.PASS, check.getStatus());

    properties.put("fs.defaultFS", "dfs://ha");
    properties.put("tez.lib.uris", "/some/path/to/archive.tar.gz");
    properties.put("tez.use.cluster.hadoop-libs", "false");
    check = new PrerequisiteCheck(null, null);
    servicesTezDistributedCacheCheck.perform(check, new PrereqCheckRequest("cluster"));
    Assert.assertEquals(PrereqCheckStatus.PASS, check.getStatus());

    properties.put("fs.defaultFS", "hdfs://ha");
    properties.put("tez.lib.uris", "/some/path/to/archive.tar.gz");
    properties.put("tez.use.cluster.hadoop-libs", "false");
    check = new PrerequisiteCheck(null, null);
    servicesTezDistributedCacheCheck.perform(check, new PrereqCheckRequest("cluster"));
    Assert.assertEquals(PrereqCheckStatus.PASS, check.getStatus());

    // Fail due to no DFS
    properties.put("fs.defaultFS", "anything");
    properties.put("tez.lib.uris", "/some/path/to/archive.tar.gz");
    properties.put("tez.use.cluster.hadoop-libs", "false");
    check = new PrerequisiteCheck(null, null);
    servicesTezDistributedCacheCheck.perform(check, new PrereqCheckRequest("cluster"));
    Assert.assertEquals(PrereqCheckStatus.FAIL, check.getStatus());

    // Fail due to no tar.gz
    properties.put("fs.defaultFS", "hdfs://ha");
    properties.put("tez.lib.uris", "/some/path/to/archive.log");
    properties.put("tez.use.cluster.hadoop-libs", "false");
    check = new PrerequisiteCheck(null, null);
    servicesTezDistributedCacheCheck.perform(check, new PrereqCheckRequest("cluster"));
    Assert.assertEquals(PrereqCheckStatus.FAIL, check.getStatus());

    // Fail due to property set to true
    properties.put("fs.defaultFS", "hdfs://ha");
    properties.put("tez.lib.uris", "/some/path/to/archive.tar.gz");
    properties.put("tez.use.cluster.hadoop-libs", "true");
    check = new PrerequisiteCheck(null, null);
    servicesTezDistributedCacheCheck.perform(check, new PrereqCheckRequest("cluster"));
    Assert.assertEquals(PrereqCheckStatus.FAIL, check.getStatus());
  }
}
