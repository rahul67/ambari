/**
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
package org.apache.ambari.server.controller.internal;

import com.google.inject.Guice;
import com.google.inject.Injector;
import com.google.inject.persist.PersistService;
import org.apache.ambari.server.api.services.AmbariMetaInfo;
import org.apache.ambari.server.controller.AmbariManagementController;
import org.apache.ambari.server.controller.spi.Predicate;
import org.apache.ambari.server.controller.spi.Request;
import org.apache.ambari.server.controller.spi.Resource;
import org.apache.ambari.server.controller.utilities.PredicateBuilder;
import org.apache.ambari.server.controller.utilities.PropertyHelper;
import org.apache.ambari.server.orm.GuiceJpaInitializer;
import org.apache.ambari.server.orm.InMemoryDefaultTestModule;
import org.apache.ambari.server.state.stack.MetricDefinition;
import org.junit.After;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import static org.apache.ambari.server.controller.internal.StackArtifactResourceProvider.ARTIFACT_DATA_PROPERTY_ID;
import static org.apache.ambari.server.controller.internal.StackArtifactResourceProvider.ARTIFACT_NAME_PROPERTY_ID;
import static org.apache.ambari.server.controller.internal.StackArtifactResourceProvider.STACK_NAME_PROPERTY_ID;
import static org.apache.ambari.server.controller.internal.StackArtifactResourceProvider.STACK_SERVICE_NAME_PROPERTY_ID;
import static org.apache.ambari.server.controller.internal.StackArtifactResourceProvider.STACK_VERSION_PROPERTY_ID;
import static org.easymock.EasyMock.createNiceMock;
import static org.easymock.EasyMock.expect;
import static org.easymock.EasyMock.replay;
import static org.easymock.EasyMock.verify;

public class StackArtifactResourceProviderTest {
  private AmbariMetaInfo metaInfo;
  private Injector injector;

  @Before
  public void setup() throws Exception {
    // Unfortunately metainfo is tied to in-memory db instance through
    // looking for updated repo url in StackContext
    InMemoryDefaultTestModule module = new InMemoryDefaultTestModule();
    injector = Guice.createInjector(module);
    injector.getInstance(GuiceJpaInitializer.class);
    metaInfo = injector.getInstance(AmbariMetaInfo.class);
    metaInfo.init();
  }

  @After
  public void tearDown() {
    injector.getInstance(PersistService.class).stop();
  }

  private StackArtifactResourceProvider getStackArtifactResourceProvider(
      AmbariManagementController managementController) {

    Resource.Type type = Resource.Type.StackArtifact;

    return (StackArtifactResourceProvider) AbstractControllerResourceProvider.getResourceProvider(
      type,
      PropertyHelper.getPropertyIds(type),
      PropertyHelper.getKeyPropertyIds(type),
      managementController);
  }

  @Test
  public void testGetMetricsDescriptorForService() throws Exception {
    AmbariManagementController managementController = createNiceMock(AmbariManagementController.class);

    expect(managementController.getAmbariMetaInfo()).andReturn(metaInfo).anyTimes();

    replay(managementController);

    StackArtifactResourceProvider resourceProvider = getStackArtifactResourceProvider(managementController);

    Set<String> propertyIds = new HashSet<String>();
    propertyIds.add(ARTIFACT_NAME_PROPERTY_ID);
    propertyIds.add(STACK_NAME_PROPERTY_ID);
    propertyIds.add(STACK_VERSION_PROPERTY_ID);
    propertyIds.add(STACK_SERVICE_NAME_PROPERTY_ID);
    propertyIds.add(ARTIFACT_DATA_PROPERTY_ID);

    Request request = PropertyHelper.getReadRequest(propertyIds);

    Predicate predicate = new PredicateBuilder().property
      (ARTIFACT_NAME_PROPERTY_ID).equals("metrics_descriptor").and().property
      (STACK_NAME_PROPERTY_ID).equals("OTHER").and().property
      (STACK_VERSION_PROPERTY_ID).equals("1.0").and().property
      (STACK_SERVICE_NAME_PROPERTY_ID).equals("HDFS").toPredicate();

    Set<Resource> resources = resourceProvider.getResources(request, predicate);

    Assert.assertEquals(1, resources.size());
    Resource resource = resources.iterator().next();
    Map<String, Map<String, Object>> propertyMap = resource.getPropertiesMap();
    Map<String, Object> descriptor = propertyMap.get(ARTIFACT_DATA_PROPERTY_ID + "/HDFS/DATANODE");
    Assert.assertNotNull(descriptor);
    Assert.assertEquals(1, ((ArrayList) descriptor.get("Component")).size());
    MetricDefinition md = (MetricDefinition) ((ArrayList) descriptor.get
      ("Component")).iterator().next();
    Assert.assertEquals(326, md.getMetrics().size());
    verify(managementController);
  }


}
