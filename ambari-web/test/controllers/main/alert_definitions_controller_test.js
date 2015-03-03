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

require('controllers/main/alert_definitions_controller');
require('models/alert_definition');

var controller;
describe('App.MainAlertDefinitionsController', function() {

  beforeEach(function() {

    controller = App.MainAlertDefinitionsController.create();

  });

  describe('#toggleDefinitionState', function() {

    beforeEach(function() {
      sinon.stub(App.ajax, 'send', Em.K);
      controller.reopen({
        content: [
          App.AlertDefinition.createRecord({id: 1, enabled: true})
        ]
      });
    });

    afterEach(function() {
      App.ajax.send.restore();
    });

    it('should do ajax-request', function() {
      var alertDefinition = controller.get('content')[0];
      controller.toggleDefinitionState(alertDefinition);
      expect(App.ajax.send.calledOnce).to.be.true;
    });

  });

  describe('#showPopup', function () {

    describe('#bodyClass', function () {

      var bodyView;

      beforeEach(function () {
        controller.reopen({unhealthyAlertInstances: [
          App.AlertInstance.createRecord({state: 'CRITICAL'}),
          App.AlertInstance.createRecord({state: 'WARNING'}),
          App.AlertInstance.createRecord({state: 'WARNING'}),
          App.AlertInstance.createRecord({state: 'CRITICAL'})
        ]});
        bodyView = controller.showPopup().get('bodyClass').create();
      });

      it('#content', function () {
        expect(bodyView.get('content.length')).to.equal(4);
      });

      it('#isLoaded', function () {
        expect(bodyView.get('isLoaded')).to.be.true;
      });

      it('#isAlertEmptyList', function () {
        expect(bodyView.get('isAlertEmptyList')).to.be.false;
      });

    });

  });

});
