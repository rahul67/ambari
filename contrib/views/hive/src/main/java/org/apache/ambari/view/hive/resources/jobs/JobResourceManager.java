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

package org.apache.ambari.view.hive.resources.jobs;

import org.apache.ambari.view.ViewContext;
import org.apache.ambari.view.hive.client.*;
import org.apache.ambari.view.hive.persistence.utils.FilteringStrategy;
import org.apache.ambari.view.hive.persistence.utils.ItemNotFound;
import org.apache.ambari.view.hive.resources.PersonalCRUDResourceManager;
import org.apache.ambari.view.hive.utils.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/**
 * Object that provides CRUD operations for query objects
 */
public class JobResourceManager extends PersonalCRUDResourceManager<Job> {
  private final static Logger LOG =
      LoggerFactory.getLogger(JobResourceManager.class);

  private JobControllerFactory jobControllerFactory;

  /**
   * Constructor
   * @param context View Context instance
   */
  public JobResourceManager(ViewContext context) {
    super(JobImpl.class, context);
    jobControllerFactory = JobControllerFactory.getInstance(context);
  }

  @Override
  public Job create(Job object) {
    super.create(object);
    JobController jobController = jobControllerFactory.createControllerForJob(object);

    try {

      jobController.afterCreation();
      saveIfModified(jobController);

    } catch (ServiceFormattedException e) {
      cleanupAfterErrorAndThrowAgain(object, e);
    }

    return object;
  }

  private void saveIfModified(JobController jobController) {
    if (jobController.isModified()) {
      save(jobController.getJobPOJO());
      jobController.clearModified();
    }
  }


  @Override
  public Job read(Integer id) throws ItemNotFound {
    Job job = super.read(id);
    JobController jobController =  jobControllerFactory.createControllerForJob(job);
    jobController.onRead();
    saveIfModified(jobController);
    return job;
  }

  @Override
  public List<Job> readAll(FilteringStrategy filteringStrategy) {
    return super.readAll(filteringStrategy);
  }

  @Override
  public void delete(Integer resourceId) throws ItemNotFound {
    super.delete(resourceId);
  }

  public JobController readController(Integer id) throws ItemNotFound {
    Job job = read(id);
    return jobControllerFactory.createControllerForJob(job);
  }

  public Cursor getJobResultsCursor(Job job) {
    try {
      JobController jobController = jobControllerFactory.createControllerForJob(job);
      return jobController.getResults();
    } catch (ItemNotFound itemNotFound) {
      throw new NotFoundFormattedException("Job results are expired", null);
    }
  }
}
