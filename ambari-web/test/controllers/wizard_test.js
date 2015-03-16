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

var App = require('app');
require('models/cluster');
require('controllers/wizard');

var c;

describe('App.WizardController', function () {

  var wizardController = App.WizardController.create({});

  var totalSteps = 11;
  var ruller = [];
  for(var i = 0; i < totalSteps; i++) {
    ruller.push(i);
  }

  beforeEach(function () {
    c = App.WizardController.create({});
  });

  describe('#setLowerStepsDisable', function() {
    for(var i = 1; i < totalSteps; i++) {
      var indx = i;
      var steps = [];
      for(var j = 1; j <= indx; j++) {
        steps.push(Em.Object.create({step:j,value:false}));
      }
      wizardController.set('isStepDisabled', steps);
      for(j = 1; j <= indx; j++) {
        it('Steps: ' + i + ' | Disabled: ' + (j-1), function() {
          wizardController.setLowerStepsDisable(j);
          expect(wizardController.get('isStepDisabled').filterProperty('value', true).length).to.equal(j-1);
        });
      }
    }
  });

  // isStep0 ... isStep10 tests
  App.WizardController1 = App.WizardController.extend({currentStep:''});
  var tests = [];
  for(var i = 0; i < totalSteps; i++) {
    var n = ruller.slice(0);
    n.splice(i,1);
    tests.push({i:i,n:n});
  }
  tests.forEach(function(test) {
    describe('isStep'+test.i, function() {
      var w = App.WizardController1.create();
      w.set('currentStep', test.i);
      it('Current Step is ' + test.i + ', so isStep' + test.i + ' is TRUE', function() {
        expect(w.get('isStep'+ test.i)).to.equal(true);
      });
      test.n.forEach(function(indx) {
        it('Current Step is ' + test.i + ', so isStep' + indx + ' is FALSE', function() {
          expect(w.get('isStep'+ indx)).to.equal(false);
        });
      });
    });
  });
  // isStep0 ... isStep10 tests end

  describe('#gotoStep', function() {
    var w = App.WizardController1.create();
    var steps = [];
    for(var j = 0; j < totalSteps; j++) {
      steps.push(Em.Object.create({step:j,value:false}));
    }
    steps.forEach(function(step, index) {
      step.set('value', true);
      w.set('isStepDisabled', steps);
      it('step ' + index + ' is disabled, so gotoStep('+index+') is not possible', function() {
        expect(w.gotoStep(index)).to.equal(false);
      });
    });
  });

  describe('#launchBootstrapSuccessCallback', function() {
    it('Save bootstrapRequestId', function() {
      var data = {requestId: 123};
      var params = {popup: {finishLoading: function(){}}};
      sinon.spy(params.popup, "finishLoading");
      wizardController.launchBootstrapSuccessCallback(data, {}, params);
      expect(params.popup.finishLoading.calledWith(123)).to.be.true;
      params.popup.finishLoading.restore();
    });
  });

  describe('#getInstallOptions', function () {

    var cases = [
        {
          isHadoopWindowsStack: true,
          expected: {
            useSsh: false
          }
        },
        {
          isHadoopWindowsStack: false,
          expected: {
            useSsh: true
          }
        }
      ],
      title = 'should return {0}';

    beforeEach(function () {
      sinon.stub(wizardController, 'get')
        .withArgs('installOptionsTemplate').returns({useSsh: true})
        .withArgs('installWindowsOptionsTemplate').returns({useSsh: false});
    });

    afterEach(function () {
      App.get.restore();
      wizardController.get.restore();
    });

    cases.forEach(function (item) {
      it(title.format(item.expected), function () {
        sinon.stub(App, 'get').withArgs('isHadoopWindowsStack').returns(item.isHadoopWindowsStack);
        expect(wizardController.getInstallOptions()).to.eql(item.expected);
      });
    });

  });

  describe('#clearInstallOptions', function () {

    wizardController.setProperties({
      content: {},
      name: 'wizard'
    });

    beforeEach(function () {
      sinon.stub(App, 'get').withArgs('isHadoopWindowsStack').returns(false);
    });

    afterEach(function () {
      App.get.restore();
    });

    it('should clear install options', function () {
      wizardController.clearInstallOptions();
      expect(wizardController.get('content.installOptions')).to.eql(wizardController.get('installOptionsTemplate'));
      expect(wizardController.get('content.hosts')).to.eql({});
      expect(wizardController.getDBProperty('installOptions')).to.eql(wizardController.get('installOptionsTemplate'))
      expect(wizardController.getDBProperty('hosts')).to.eql({});
    });
  });

  describe('#saveServiceConfigProperties', function () {

    beforeEach(function () {
      c.set('content', {});
      sinon.stub(c, 'setDBProperty', Em.K);
    });

    afterEach(function () {
      c.setDBProperty.restore();
    });

    var stepController = Em.Object.create({
      installedServiceNames: [],
      stepConfigs: [
      Em.Object.create({
        serviceName: 'HDFS',
        configs: [
          Em.Object.create({
            id: 'id',
            name: 'name',
            value: 'value',
            defaultValue: 'defaultValue',
            description: 'description',
            serviceName: 'serviceName',
            domain: 'domain',
            isVisible: true,
            isFinal: true,
            defaultIsFinal: true,
            supportsFinal: true,
            filename: 'filename',
            displayType: 'string',
            isRequiredByAgent: true,
            hasInitialValue: true,
            isRequired: true,
            group: {name: 'group'},
            showLabel: true,
            category: 'some_category'
          })
        ]
      })
    ]});

    it('should save configs to content.serviceConfigProperties', function () {
      c.saveServiceConfigProperties(stepController);
      var saved = c.get('content.serviceConfigProperties');
      expect(saved.length).to.equal(1);
      expect(saved[0].category).to.equal('some_category');
    });

  });

  describe('#enableStep', function () {

    it('should update appropriate value in isStepDisabled', function () {

      c.set('isStepDisabled', [
        Em.Object.create({step: 1, value: true}),
        Em.Object.create({step: 2, value: true}),
        Em.Object.create({step: 3, value: true}),
        Em.Object.create({step: 4, value: true}),
        Em.Object.create({step: 5, value: true}),
        Em.Object.create({step: 6, value: true}),
        Em.Object.create({step: 7, value: true})
      ]);

      c.enableStep(1);
      expect(c.get('isStepDisabled')[0].get('value')).to.be.false;

      c.enableStep(7);
      expect(c.get('isStepDisabled')[6].get('value')).to.be.false;
    });

  });

  describe('#setSkipSlavesStep', function () {

    var step = 6,
      cases = [
        {
          services: [
            {
              hasSlave: true,
              hasNonMastersWithCustomAssignment: true
            }
          ],
          skipSlavesStep: false,
          title: 'service with customizable slave selected'
        },
        {
          services: [
            {
              hasClient: true,
              hasNonMastersWithCustomAssignment: true
            }
          ],
          skipSlavesStep: false,
          title: 'service with customizable client selected'
        },
        {
          services: [
            {
              hasSlave: true,
              hasNonMastersWithCustomAssignment: false
            },
            {
              hasClient: true,
              hasNonMastersWithCustomAssignment: false
            }
          ],
          skipSlavesStep: true,
          title: 'no service with customizable slaves or clients selected'
        },
        {
          services: [
            {
              hasSlave: false,
              hasClient: false
            }
          ],
          skipSlavesStep: true,
          title: 'no service with slaves or clients selected'
        }
      ];

    beforeEach(function () {
      c.reopen({
        isStepDisabled: [
          Em.Object.create({
            step: 6
          })
        ],
        content: {}
      });
    });

    cases.forEach(function (item) {
      it(item.title, function () {
        c.setSkipSlavesStep(item.services, step);
        expect(Boolean(c.get('isStepDisabled').findProperty('step', step).get('value'))).to.equal(item.skipSlavesStep);
      });
    });

  });
});
