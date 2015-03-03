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
var stringUtils = require('utils/string_utils');

var configGroupsByTag = [];

App.config = Em.Object.create({

  CONFIG_GROUP_NAME_MAX_LENGTH: 18,

  /**
   * filename exceptions used to support substandard sitenames which don't have "xml" extension
   */
  filenameExceptions: [],

  preDefinedServiceConfigs: [],
  /**
   *
   * Returns file name version that stored on server.
   *
   * Example:
   *   App.config.getOriginalFileName('core-site') // returns core-site.xml
   *   App.config.getOriginalFileName('zoo.cfg') // returns zoo.cfg
   *
   * @param {String} fileName
   * @method getOriginalFileName
   **/
  getOriginalFileName: function (fileName) {
    if (/\.xml$/.test(fileName)) return fileName;
    return this.get('filenameExceptions').contains(fileName) ? fileName : fileName + '.xml';
  },

  /**
   * Check if Hive installation with new MySQL database created via Ambari is allowed
   * @param osFamily
   * @returns {boolean}
   */
  isManagedMySQLForHiveAllowed: function (osFamily) {
    var osList = ['redhat5', 'suse11'];
    return !osList.contains(osFamily);
  },

  /**
   *
   * Returns the configuration tagName from supplied filename
   *
   * Example:
   *   App.config.getConfigTagFromFileName('core-site.xml') // returns core-site
   *   App.config.getConfigTagFromFileName('zoo.cfg') // returns zoo.cfg
   *
   * @param {String} fileName
   * @method getConfigTagFromFileName
   **/
  getConfigTagFromFileName: function (fileName) {
    return fileName.endsWith('.xml') ? fileName.slice(0, -4) : fileName;
  },

  setPreDefinedServiceConfigs: function (isMiscTabToBeAdded) {
    var configs = this.get('preDefinedSiteProperties');
    var services = [];
    var stackServices = App.StackService.find().filterProperty('id');
    // Only include services that has configTypes related to them for service configuration page
    var servicesWithConfigTypes = stackServices.filter(function (service) {
      var configtypes = service.get('configTypes');
      return configtypes && !!Object.keys(configtypes).length;
    }, this);

    var allTabs;
    if (isMiscTabToBeAdded) {
      var nonServiceTab = require('data/service_configs');
      var miscService = nonServiceTab.findProperty('serviceName', 'MISC');
      var tagTypes = {};
      servicesWithConfigTypes.mapProperty('configTypes').forEach(function(configTypes) {
        for (var fileName in configTypes) {
          if (fileName.endsWith('-env') && !miscService.get('configTypes')[fileName]) {
            tagTypes[fileName] = configTypes[fileName];
          }
        }
      });
      miscService.set('configTypes', $.extend(miscService.get('configTypes'), tagTypes));
      allTabs = servicesWithConfigTypes.concat(nonServiceTab);
    } else {
      allTabs = servicesWithConfigTypes;
    }

    allTabs.forEach(function (service) {
      var serviceConfigs = configs.filterProperty('serviceName', service.get('serviceName'));
      service.set('configs', serviceConfigs);
      services.push(service);
    });
    this.set('preDefinedServiceConfigs', services);
  },

  configMapping: require('data/HDP2/config_mapping'),

  preDefinedSiteProperties: function () {
    var sitePropertiesForCurrentStack = this.preDefinedConfigFile('site_properties');
    if (sitePropertiesForCurrentStack) {
      return sitePropertiesForCurrentStack.configProperties;
    }

    if (App.get('isHadoop22Stack')) {
      return require('data/HDP2.2/site_properties').configProperties;
    }
    return require('data/HDP2/site_properties').configProperties;
  }.property('App.isHadoop22Stack', 'App.currentStackName'),

  preDefinedCustomConfigs: require('data/HDP2/custom_configs'),

  preDefinedConfigFile: function(file) {
    try {
      return require('data/{0}/{1}'.format(App.get('currentStackName'), file));
    } catch(err) {
      // the file doesn't exist, which might be expected.
    }
  },
  //categories which contain custom configs
  categoriesWithCustom: ['CapacityScheduler'],


  /**
   * Create array of service properties for Log4j files
   * @returns {Array}
   */
  createContentProperties: function (configs) {
    var services = App.StackService.find();
    var contentProperties = [];
    if (configs) {
      services.forEach(function (service) {
        if (service.get('configTypes')) {
          Object.keys(service.get('configTypes')).forEach(function (type) {
            var contentProperty = configs.filterProperty('filename', type + '.xml').someProperty('name', 'content');
            if (contentProperty && (type.endsWith('-log4j') || type.endsWith('-env'))) {
              var property = {
                "id": "site property",
                "name": "content",
                "displayName": type.endsWith('-env') ? type + ' template' : "content",
                "value": "",
                "defaultValue": "",
                "description": type + " properties",
                "displayType": "content",
                "isOverridable": true,
                "isRequired": false,
                "isVisible": true,
                "showLabel": type.endsWith('-env'),
                "serviceName": service.get('serviceName'),
                "filename": type + '.xml',
                "category": "Advanced " + type
              };
              contentProperties.pushObject(property);
            }
          }, this);
        }
      }, this);
    }
    return contentProperties;
  },

  //configs with these filenames go to appropriate category not in Advanced
  customFileNames: ['flume-conf.xml'],

  /**
   * Function should be used post-install as precondition check should not be done only after installer wizard
   * @param siteNames {String|Array}
   * @returns {Array}
   */
  getBySitename: function (siteNames) {
    var computedConfigs = this.get('configMapping').computed();
    var siteProperties = [];
    if (typeof siteNames === "string") {
      siteProperties = computedConfigs.filterProperty('filename', siteNames);
    } else if (siteNames instanceof Array) {
      siteNames.forEach(function (_siteName) {
        siteProperties = siteProperties.concat(computedConfigs.filterProperty('filename', _siteName));
      }, this);
    }
    return siteProperties;
  },

  /**
   * Cache of loaded configurations. This is useful in not loading
   * same configuration multiple times. It is populated in multiple
   * places.
   *
   * Example:
   * {
   *  'hdfs-site_version3': {...},
   * }
   */
  loadedConfigurationsCache: {},

  /**
   * identify category by filename of config
   * @param config
   * @return {object|null}
   */
  identifyCategory: function (config) {
    var category = null,
      serviceConfigMetaData = this.get('preDefinedServiceConfigs').findProperty('serviceName', config.serviceName),
      configCategories = (serviceConfigMetaData && serviceConfigMetaData.get('configCategories')) || [];

    if (config.filename.contains("env")) {
      if (config.category) {
        category = configCategories.findProperty("name", config.category);
      } else {
        configCategories.forEach(function (_category) {
          if (_category.name.contains(this.getConfigTagFromFileName(config.filename))) {
            category = _category;
          }
        }, this);
      }
    } else {
      configCategories.forEach(function (_category) {
        if (_category.siteFileNames && Array.isArray(_category.siteFileNames) && _category.siteFileNames.contains(config.filename)) {
          category = _category;
        }
      });
      category = Em.isNone(category) ? configCategories.findProperty('siteFileName', this.getOriginalFileName(config.filename)) : category;
    }
    return category;
  },
  /**
   * additional handling for special properties such as
   * checkbox and digital which values with 'm' at the end
   * @param config
   */
  handleSpecialProperties: function (config) {
    if (config.displayType === 'int' && /\d+m$/.test(config.value)) {
      config.value = config.value.slice(0, config.value.length - 1);
      config.defaultValue = config.value;
    }
  },
  /**
   * calculate config properties:
   * category, filename, isUserProperty, description
   * @param config
   * @param isAdvanced
   * @param advancedConfigs
   */
  calculateConfigProperties: function (config, isAdvanced, advancedConfigs) {
    if (!isAdvanced || this.get('customFileNames').contains(config.filename)) {
      var categoryMetaData = this.identifyCategory(config);
      if (categoryMetaData != null) {
        config.category = categoryMetaData.get('name');
        if (!isAdvanced) config.isUserProperty = true;
      }
      if (isAdvanced) {
        var advancedProperty = advancedConfigs.filterProperty('filename', config.filename).findProperty('name', config.name);
        if (advancedProperty) {
          config.description = advancedProperty.description;
        }
      }
    } else {
      var advancedProperty = null;
      var configType = this.getConfigTagFromFileName(config.filename);
      if (isAdvanced) {
        advancedProperty = advancedConfigs.filterProperty('filename', config.filename).findProperty('name', config.name);
      }
      config.category = config.category ? config.category : 'Advanced ' + configType;
      if (advancedProperty) {
        config.description = advancedProperty.description;
      }
    }
  },

  capacitySchedulerFilter: function () {
    var yarnRegex = /^yarn\.scheduler\.capacity\.root\.([a-z]([\_\-a-z0-9]{0,50}))\.(acl_administer_jobs|acl_submit_jobs|state|user-limit-factor|maximum-capacity|capacity)$/i;
    return function (_config) {
      return (yarnRegex.test(_config.name));
    }
  }.property(),
  /**
   * return:
   *   configs,
   *   mappingConfigs
   *
   * @param configCategories
   * @param advancedConfigs
   * @param tags
   * @param serviceName
   * @return {object}
   */
  mergePreDefinedWithLoaded: function (configCategories, advancedConfigs, tags, serviceName) {
    var configs = [];
    var contentProperties = this.createContentProperties(advancedConfigs);
    var preDefinedConfigs = this.get('preDefinedSiteProperties').concat(contentProperties);
    var mappingConfigs = [];
    var filenameExceptions = this.get('filenameExceptions');
    var selectedServiceNames = App.Service.find().mapProperty('serviceName');
    tags.forEach(function (_tag) {
      var isAdvanced = null;
      var filename = (filenameExceptions.contains(_tag.siteName)) ? _tag.siteName : _tag.siteName + ".xml";
      var siteConfig = configCategories.filter(function (serviceConfigProperties) {
        return _tag.tagName === serviceConfigProperties.tag && _tag.siteName === serviceConfigProperties.type;
      });
      siteConfig = siteConfig[0] || {};

      var attributes = siteConfig['properties_attributes'] || {};
      var finalAttributes = attributes.final || {};
      var properties = siteConfig.properties || {};
      for (var index in properties) {
        var configsPropertyDef = preDefinedConfigs.filterProperty('name', index).findProperty('filename', filename);
        if (!configsPropertyDef) {
          advancedConfigs.filterProperty('name', index).forEach(function (_advancedConfig) {
            var isServiceInstalled = selectedServiceNames.contains(_advancedConfig.serviceName);
            if (isServiceInstalled || _advancedConfig.serviceName == 'MISC') {
              configsPropertyDef = _advancedConfig;
            }
          }, this);
        }

        var serviceConfigObj = App.ServiceConfig.create({
          name: index,
          value: properties[index],
          defaultValue: properties[index],
          filename: filename,
          isUserProperty: false,
          isOverridable: true,
          isReconfigurable: true,
          isRequired: advancedConfigs.someProperty('name', index),
          isFinal: finalAttributes[index] === "true",
          defaultIsFinal: finalAttributes[index] === "true",
          showLabel: true,
          serviceName: serviceName,
          belongsToService: []
        });

        if (configsPropertyDef) {
          this.setServiceConfigUiAttributes(serviceConfigObj, configsPropertyDef);
          // check if defined UI config present in config list obtained from server.
          // in case when config is absent on server and defined UI config is required
          // by server, this config should be ignored
          var serverProperty = properties[serviceConfigObj.get('name')];
          if (Em.isNone(serverProperty) && serviceConfigObj.get('isRequiredByAgent')) {
            continue;
          }
        }

        if (!this.getBySitename(serviceConfigObj.get('filename')).someProperty('name', index)) {
          if (configsPropertyDef) {
            if (configsPropertyDef.isRequiredByAgent === false) {
              continue;
            }
            this.handleSpecialProperties(serviceConfigObj);
          } else {
            serviceConfigObj.displayType = stringUtils.isSingleLine(serviceConfigObj.value) ? 'advanced' : 'multiLine';
          }

          isAdvanced = advancedConfigs.filterProperty('name', index).someProperty('filename', filename);
          serviceConfigObj.id = 'site property';
          serviceConfigObj.displayName = configsPropertyDef && configsPropertyDef.displayName ? configsPropertyDef.displayName : index;
          serviceConfigObj.options = configsPropertyDef ? configsPropertyDef.options : null;
          serviceConfigObj.radioName = configsPropertyDef ? configsPropertyDef.radioName : null;
          serviceConfigObj.serviceName = configsPropertyDef && configsPropertyDef.serviceName ? configsPropertyDef.serviceName : serviceName;
          serviceConfigObj.belongsToService = configsPropertyDef && configsPropertyDef.belongsToService ? configsPropertyDef.belongsToService : [];
          this.calculateConfigProperties(serviceConfigObj, isAdvanced, advancedConfigs);
          this.setValueByDisplayType(serviceConfigObj);
          configs.push(serviceConfigObj);
        } else {
          mappingConfigs.push(serviceConfigObj);
        }
      }
    }, this);
    return {
      configs: configs,
      mappingConfigs: mappingConfigs
    }
  },

  setValueByDisplayType: function(serviceConfigObj) {
    if (serviceConfigObj.get('displayType') == 'directories' && (serviceConfigObj.get('category') == 'DataNode' || serviceConfigObj.get('category') == 'NameNode')) {
      var dirs = serviceConfigObj.get('value').split(',').sort();
      serviceConfigObj.set('value', dirs.join(','));
      serviceConfigObj.set('defaultValue', dirs.join(','));
    }

    if (serviceConfigObj.get('displayType') == 'directory' && serviceConfigObj.get('category') == 'SNameNode') {
      var dirs = serviceConfigObj.get('value').split(',').sort();
      serviceConfigObj.set('value', dirs[0]);
      serviceConfigObj.set('defaultValue', dirs[0]);
    }

    if (serviceConfigObj.get('displayType') == 'masterHosts') {
      if (typeof(serviceConfigObj.get('value')) == 'string') {
        var value = serviceConfigObj.get('value').replace(/\[|]|'|&apos;/g, "").split(',');
        serviceConfigObj.set('value', value);
      }
    }
  },

  /**
   * @param serviceConfigObj : Object
   * @param configsPropertyDef : Object
   */
  setServiceConfigUiAttributes: function (serviceConfigObj, configsPropertyDef) {
    serviceConfigObj.displayType = configsPropertyDef.displayType;
    serviceConfigObj.isRequired = (configsPropertyDef.isRequired !== undefined) ? configsPropertyDef.isRequired : true;
    serviceConfigObj.isRequiredByAgent = (configsPropertyDef.isRequiredByAgent !== undefined) ? configsPropertyDef.isRequiredByAgent : true;
    serviceConfigObj.isReconfigurable = (configsPropertyDef.isReconfigurable !== undefined) ? configsPropertyDef.isReconfigurable : true;
    serviceConfigObj.isVisible = (configsPropertyDef.isVisible !== undefined) ? configsPropertyDef.isVisible : true;
    serviceConfigObj.unit = (configsPropertyDef.unit !== undefined) ? configsPropertyDef.unit : undefined;
    serviceConfigObj.description = (configsPropertyDef.description !== undefined) ? configsPropertyDef.description : undefined;
    serviceConfigObj.isOverridable = configsPropertyDef.isOverridable === undefined ? true : configsPropertyDef.isOverridable;
    serviceConfigObj.serviceName = configsPropertyDef ? configsPropertyDef.serviceName : null;
    serviceConfigObj.index = configsPropertyDef.index;
    serviceConfigObj.isSecureConfig = configsPropertyDef.isSecureConfig === undefined ? false : configsPropertyDef.isSecureConfig;
    serviceConfigObj.belongsToService = configsPropertyDef.belongsToService;
    serviceConfigObj.category = configsPropertyDef.category;
    serviceConfigObj.showLabel = configsPropertyDef.showLabel !== false;
    serviceConfigObj.dependentConfigPattern = configsPropertyDef.dependentConfigPattern
  },

  /**
   * synchronize order of config properties with order, that on UI side
   *
   * @method syncOrderWithPredefined
   * @param configSet {object}
   * @return {Object}
   */
  syncOrderWithPredefined: function (configSet) {
    var siteConfigs = configSet.configs,
      siteStart = [];

    var preDefinedSiteProperties = this.get('preDefinedSiteProperties').mapProperty('name');
    var contentProperties = this.createContentProperties(siteConfigs).mapProperty('name');
    var siteProperties = preDefinedSiteProperties.concat(contentProperties);
    siteProperties.forEach(function (name) {
      var _site = siteConfigs.filterProperty('name', name);
      if (_site.length == 1) {
        siteStart.push(_site[0]);
        siteConfigs = siteConfigs.without(_site[0]);
      } else if (_site.length > 1) {
        _site.forEach(function (site) {
          siteStart.push(site);
          siteConfigs = siteConfigs.without(site);
        }, this);
      }
    }, this);

    return {
      configs: siteStart.concat(siteConfigs.sortProperty('name')),
      mappingConfigs: configSet.mappingConfigs
    }
  },

  /**
   * merge stored configs with pre-defined
   * @param storedConfigs
   * @param advancedConfigs
   * @param selectedServiceNames
   * @return {Array}
   */
  mergePreDefinedWithStored: function (storedConfigs, advancedConfigs, selectedServiceNames) {
    var mergedConfigs = [];
    var contentProperties = advancedConfigs ? this.createContentProperties(advancedConfigs) : [];
    var preDefinedConfigs = this.get('preDefinedSiteProperties').concat(contentProperties);

    storedConfigs = (storedConfigs) ? storedConfigs : [];

    var preDefinedNames = preDefinedConfigs.mapProperty('name');
    var storedNames = storedConfigs.mapProperty('name');
    var names = preDefinedNames.concat(storedNames).uniq();
    names.forEach(function (name) {
      var storedCfgs = storedConfigs.filterProperty('name', name);
      var preDefinedCfgs = [];
      var preDefinedConfig = preDefinedConfigs.filterProperty('name', name);
      preDefinedConfig.forEach(function (_preDefinedConfig) {
        if (selectedServiceNames.contains(_preDefinedConfig.serviceName) || _preDefinedConfig.serviceName === 'MISC') {
          preDefinedCfgs.push(_preDefinedConfig);
        }
      }, this);

      var configData = {};
      var isAdvanced = advancedConfigs && advancedConfigs.someProperty('name', name);
      if (storedCfgs.length <= 1 && preDefinedCfgs.length <= 1) {
        var stored = storedCfgs[0];
        var preDefined = preDefinedCfgs[0];

        if (preDefined && stored) {
          configData = preDefined;
          configData.value = stored.value;
          configData.defaultValue = stored.defaultValue;
          configData.overrides = stored.overrides;
          configData.filename = stored.filename;
          configData.description = stored.description;
          configData.isVisible = stored.isVisible;
          configData.isFinal = stored.isFinal;
          configData.supportsFinal = stored.supportsFinal;
          configData.isRequired = (configData.isRequired !== undefined) ? configData.isRequired : true;
          configData.isRequiredByAgent = (configData.isRequiredByAgent !== undefined) ? configData.isRequiredByAgent : true;
          configData.showLabel = !!stored.showLabel;
        }
        else if (!preDefined && stored) {
          configData = this.addUserProperty(stored, isAdvanced, advancedConfigs);
        }
        else if (preDefined && !stored) {
          configData = preDefined;
          configData.isRequiredByAgent = (configData.isRequiredByAgent !== undefined) ? configData.isRequiredByAgent : true;
          if (isAdvanced) {
            var advanced = advancedConfigs.filterProperty('filename', configData.filename).findProperty('name', configData.name);
            this.setPropertyFromStack(configData, advanced);
          }
        }

        mergedConfigs.push(configData);
      } else {
        preDefinedCfgs.forEach(function (cfg) {
          configData = cfg;
          configData.isRequiredByAgent = (configData.isRequiredByAgent !== undefined) ? configData.isRequiredByAgent : true;
          var storedCfg = storedCfgs.findProperty('filename', cfg.filename);
          if (storedCfg) {
            configData.value = storedCfg.value;
            configData.defaultValue = storedCfg.defaultValue;
            configData.overrides = storedCfg.overrides;
            configData.filename = storedCfg.filename;
            configData.description = storedCfg.description;
            configData.isFinal = storedCfg.isFinal;
            configData.supportsFinal = storedCfg.supportsFinal;
            configData.showLabel = !!storedCfg.showLabel;
          } else if (isAdvanced) {
            advanced = advancedConfigs.filterProperty('filename', configData.filename).findProperty('name', configData.name);
            this.setPropertyFromStack(configData, advanced);
          }
          mergedConfigs.push(configData);
        }, this);
      }
    }, this);
    return mergedConfigs;
  },

  /**
   *
   * @param configData {Object} Configs that will be binded to the view on step-7 of installer wizard
   * @param advanced {Object} Config property loaded from Server side stack definition
   */
  setPropertyFromStack: function (configData, advanced) {

    // Password fields should be made blank by default in installer wizard
    // irrespective of whatever value is sent from stack definition.
    // This forces the user to fill the password field.
    if (configData.displayType == 'password') {
      configData.value = '';
    } else {
      configData.value = advanced ? advanced.value : configData.value;
    }
    configData.defaultValue = configData.value;
    configData.filename = advanced ? advanced.filename : configData.filename;
    configData.description = advanced ? advanced.description : configData.description;
    configData.isFinal = !!(advanced && (advanced.isFinal === "true"));
    configData.supportsFinal = !!(advanced && advanced.supportsFinal);
  },


  /**
   * look over advanced configs and add missing configs to serviceConfigs
   * filter fetched configs by service if passed
   * @param serviceConfigs
   * @param advancedConfigs
   * @param serviceName
   */
  addAdvancedConfigs: function (serviceConfigs, advancedConfigs, serviceName) {
    var miscConfigs = serviceConfigs.filterProperty('serviceName', 'MISC');
    var configsToVerifying = (serviceName) ? serviceConfigs.filterProperty('serviceName', serviceName).concat(miscConfigs) : serviceConfigs.slice();
    var definedService = this.get('preDefinedServiceConfigs').findProperty('serviceName', serviceName);
    if (definedService) {
      var definedConfigs = (serviceName) ? definedService.get('configs') : [];

      if (definedConfigs.length) {
        advancedConfigs = advancedConfigs.filter(function(property) {
          return !(definedConfigs.someProperty('name', property.name) && !serviceConfigs.someProperty('name', property.name));
        }, this);
      }
    }
    if (advancedConfigs) {
      advancedConfigs.forEach(function (_config) {
        var configType = this.getConfigTagFromFileName(_config.filename);
        var configCategory = _config.category || 'Advanced ' + configType;
        var categoryMetaData = null;
        if (_config) {
          if (!(this.get('configMapping').computed().someProperty('name', _config.name) ||
            configsToVerifying.filterProperty('name', _config.name).someProperty('filename', _config.filename))) {
            if (this.get('customFileNames').contains(_config.filename)) {
              categoryMetaData = this.identifyCategory(_config);
              if (categoryMetaData != null) {
                configCategory = categoryMetaData.get('name');
              }
            }
            _config.id = "site property";
            _config.category = configCategory;
            _config.displayName = _config.displayName || _config.name;
            _config.defaultValue = _config.value;
            // make all advanced configs optional and populated by default
            /*
             * if (/\${.*}/.test(_config.value) || (service.serviceName !==
             * 'OOZIE' && service.serviceName !== 'HBASE')) { _config.isRequired =
             * false; _config.value = ''; } else if
             * (/^\s+$/.test(_config.value)) { _config.isRequired = false; }
             */
            _config.isRequired = true;
            _config.displayType = _config.displayType ? _config.displayType : stringUtils.isSingleLine(_config.value) ? 'advanced' : 'multiLine';
            serviceConfigs.push(_config);
          }
        }
      }, this);
    }
  },
  /**
   * Render a custom conf-site box for entering properties that will be written in *-site.xml files of the services
   */
  addCustomConfigs: function (configs) {
    var preDefinedCustomConfigs = $.extend(true, [], this.get('preDefinedCustomConfigs'));
    var stored = configs.filter(function (_config) {
      return this.get('categoriesWithCustom').contains(_config.category);
    }, this);
  },

  miscConfigVisibleProperty: function (configs, serviceToShow) {
    configs.forEach(function (item) {
      if (item.get('isVisible') && item.belongsToService && item.belongsToService.length) {
        if (item.get('belongsToService').contains('Cluster') && item.get('displayType') == 'user') {
          item.set('isVisible', true);
          return;
        }
        item.set("isVisible", item.belongsToService.some(function (cur) {
          return serviceToShow.contains(cur)
        }));
      }
    });
    return configs;
  },

  /**
   * render configs, distribute them by service
   * and wrap each in ServiceConfigProperty object
   * @param configs
   * @param storedConfigs
   * @param allSelectedServiceNames
   * @param installedServiceNames
   * @param localDB
   * @return {Array}
   */
  renderConfigs: function (configs, storedConfigs, allSelectedServiceNames, installedServiceNames, localDB, recommended) {
    var renderedServiceConfigs = [];
    var services = [];

    this.get('preDefinedServiceConfigs').forEach(function (serviceConfig) {
      var serviceName = serviceConfig.get('serviceName');
      if (allSelectedServiceNames.contains(serviceName) || serviceName === 'MISC') {
        console.log('pushing ' + serviceName, serviceConfig);
        if (!installedServiceNames.contains(serviceName) || serviceName === 'MISC') {
          serviceConfig.set('showConfig', true);
        }
        services.push(serviceConfig);
      }
    });
    services.forEach(function (service) {
      var configsByService = [];
      var serviceConfigs = configs.filterProperty('serviceName', service.get('serviceName'));
      serviceConfigs.forEach(function (_config) {
        _config.isOverridable = (_config.isOverridable === undefined) ? true : _config.isOverridable;
        var serviceConfigProperty = App.ServiceConfigProperty.create(_config);
        this.updateHostOverrides(serviceConfigProperty, _config);
        if (!storedConfigs && !serviceConfigProperty.get('hasInitialValue')) {
          var hiveMetastoreUrisConfig = configs.filterProperty('filename', 'hive-site.xml').findProperty('name', 'hive.metastore.uris');
          var clientPortConfig = configs.filterProperty('filename', 'zoo.cfg.xml').findProperty('name', 'clientPort');
          var dependencies = {
            'hive.metastore.uris': hiveMetastoreUrisConfig && hiveMetastoreUrisConfig.defaultValue,
            'clientPort': clientPortConfig && clientPortConfig.defaultValue
          };
          serviceConfigProperty.initialValue(localDB, dependencies);
        }
        if (storedConfigs && storedConfigs.filterProperty('name', _config.name).length && !!_config.filename) {
          var storedConfig = storedConfigs.filterProperty('name', _config.name).findProperty('filename', _config.filename);
          if (storedConfig) {
            serviceConfigProperty.set('defaultValue', storedConfig.defaultValue);
            serviceConfigProperty.set('value', storedConfig.value);
          }
        }
        this.tweakDynamicDefaults(localDB, serviceConfigProperty, _config);
        serviceConfigProperty.validate();
        configsByService.pushObject(serviceConfigProperty);
      }, this);
      var serviceConfig = this.createServiceConfig(service.get('serviceName'));
      serviceConfig.set('showConfig', service.get('showConfig'));

      // Use calculated default values for some configs
      var recommendedDefaults = {};
      if (!storedConfigs && service.get('configTypes')) {
        Object.keys(service.get('configTypes')).forEach(function (type) {
          if (!recommended || !recommended[type]) {
            return;
          }
          var defaults = recommended[type].properties;
          for (var name in defaults) {
            var config = configsByService.findProperty('name', name);
            if (!config) {
              continue;
            }
            recommendedDefaults[name] = defaults[name];
            config.set('value', defaults[name]);
            config.set('defaultValue', defaults[name]);
          }
        });
      }
      serviceConfig.set('configs', configsByService);
      renderedServiceConfigs.push(serviceConfig);
    }, this);
    return renderedServiceConfigs;
  },
  /**
   Takes care of the "dynamic defaults" for the GLUSTERFS configs.  Sets
   some of the config defaults to previously user-entered data.
   **/
  tweakDynamicDefaults: function (localDB, serviceConfigProperty, config) {
    var firstHost;
    for (var host in localDB.hosts) {
      firstHost = host;
      break;
    }
    try {
      if (typeof(config.defaultValue) == "string" && config.defaultValue.indexOf("{firstHost}") >= 0) {
        serviceConfigProperty.set('value', serviceConfigProperty.value.replace(new RegExp("{firstHost}"), firstHost));
        serviceConfigProperty.set('defaultValue', serviceConfigProperty.defaultValue.replace(new RegExp("{firstHost}"), firstHost));
      }
    } catch (err) {
      // Nothing to worry about here, most likely trying indexOf on a non-string
    }
  },

  /**
   * Mark descriptor properties in configuration object.
   *
   * @param {Object[]} configs - config properties to change
   * @param {App.ServiceConfigProperty[]} descriptor - parsed kerberos descriptor
   */
  addKerberosDescriptorConfigs: function(configs, descriptor) {
    descriptor.forEach(function(item) {
      var property = configs.findProperty('name', item.get('name'));
      if (property) {
        Em.set(property, 'isSecureConfig', true);
        Em.set(property, 'displayName', Em.get(item, 'name'));
        Em.set(property, 'isUserProperty', false);
        Em.set(property, 'isOverridable', false);
        Em.set(property, 'category', 'Advanced ' + Em.get(item, 'filename'));
      }
    });
  },
  /**
   * create new child configs from overrides, attach them to parent config
   * override - value of config, related to particular host(s)
   * @param configProperty
   * @param storedConfigProperty
   */
  updateHostOverrides: function (configProperty, storedConfigProperty) {
    if (storedConfigProperty.overrides != null && storedConfigProperty.overrides.length > 0) {
      var overrides = [];
      storedConfigProperty.overrides.forEach(function (overrideEntry) {
        // create new override with new value
        var newSCP = App.ServiceConfigProperty.create(configProperty);
        newSCP.set('value', overrideEntry.value);
        newSCP.set('isOriginalSCP', false); // indicated this is overridden value,
        newSCP.set('parentSCP', configProperty);
        var hostsArray = Ember.A([]);
        overrideEntry.hosts.forEach(function (host) {
          hostsArray.push(host);
        });
        newSCP.set('selectedHostOptions', hostsArray);
        overrides.pushObject(newSCP);
      });
      configProperty.set('overrides', overrides);
    }
  },
  /**
   * create new ServiceConfig object by service name
   * @param serviceName
   */
  createServiceConfig: function (serviceName) {
    var preDefinedServiceConfig = App.config.get('preDefinedServiceConfigs').findProperty('serviceName', serviceName);
    var serviceConfig = App.ServiceConfig.create({
      serviceName: preDefinedServiceConfig.get('serviceName'),
      displayName: preDefinedServiceConfig.get('displayName'),
      configCategories: preDefinedServiceConfig.get('configCategories'),
      configs: [],
      configGroups: []
    });
    return serviceConfig;
  },
  /**
   * GETs all cluster level sites in one call.
   *
   * @return {object}
   */
  loadConfigsByTags: function (tags) {
    var urlParams = [];
    tags.forEach(function (_tag) {
      urlParams.push('(type=' + _tag.siteName + '&tag=' + _tag.tagName + ')');
    });
    var params = urlParams.join('|');
    return App.ajax.send({
      name: 'config.on_site',
      sender: this,
      data: {
        params: params
      }
    });
  },

  /**
   * Fetch cluster configs from server
   *
   * @param callback
   * @return {object|null}
   */
  loadClusterConfig: function (callback) {
    return App.ajax.send({
      name: 'config.cluster',
      sender: this,
      data: {
        stackVersionUrl: App.get('stackVersionURL'),
        callback: callback
      },
      success: 'loadClusterConfigSuccess',
      error: 'loadClusterConfigError'
    });
  },

  loadClusterConfigSuccess: function (data, opt, params) {
    console.log("TRACE: In success function for the loadClusterConfigSuccess; url is ", opt.url);
    var properties = [];
    if (data.items.length) {
      data.items.forEach(function (item) {
        item.StackLevelConfigurations.property_type = item.StackLevelConfigurations.property_type || [];
        item.StackLevelConfigurations.service_name = 'MISC';
        var property = this.createAdvancedPropertyObject(item.StackLevelConfigurations);
        if (property) properties.push(property);
      }, this);
    }
    params.callback(properties);
  },

  loadClusterConfigError: function (request, ajaxOptions, error, opt, params) {
    console.log('ERROR: Failed to load cluster-env configs');
    params.callback([]);
  },


  /**
   * Generate serviceProperties save it to localDB
   * called from stepController step6WizardController
   *
   * @method loadAdvancedConfig
   * @param serviceName
   * @param callback
   * @return {object|null}
   */
  loadAdvancedConfig: function (serviceName, callback) {
    return App.ajax.send({
      name: 'config.advanced',
      sender: this,
      data: {
        serviceName: serviceName,
        stackVersionUrl: App.get('stackVersionURL'),
        stackVersion: App.get('currentStackVersionNumber'),
        callback: callback
      },
      success: 'loadAdvancedConfigSuccess',
      error: 'loadAdvancedConfigError'
    });
  },

  /**
   * Load advanced configs by service names etc.
   * Use this method when you need to get configs for
   * particular services by single request
   *
   * @method loadAdvancedConfigPartial
   * @param {String[]} serviceNames
   * @param {Object} opt
   * @param {Function} callback
   * @returns {jqXHR}
   */
  loadAdvancedConfigPartial: function(serviceNames, opt, callback) {
    var data = {
      serviceList: serviceNames.join(','),
      stackVersionUrl: App.get('stackVersionURL'),
      stackVersion: App.get('currentStackVersionNumber'),
      queryFilter: ('&' + opt.queryFilter) || '',
      callback: callback
    };
    return App.ajax.send({
      name: 'config.advanced.partial',
      sender: this,
      data: data,
      success: 'loadAdvancedConfigPartialSuccess',
      error: 'loadAdvancedConfigError'
    });
  },

  loadAdvancedConfigSuccess: function (data, opt, params, request) {
    console.log("TRACE: In success function for the loadAdvancedConfig; url is ", opt.url);
    var properties = [];
    if (data.items.length) {
      data.items.forEach(function (item) {
        var property = this.createAdvancedPropertyObject(item.StackConfigurations);
        if (property) properties.push(property);
      }, this);
    }
    params.callback(properties, request);
  },

  loadAdvancedConfigError: function (request, ajaxOptions, error, opt, params) {
    console.log('ERROR: failed to load stack configs for', params.serviceName);
    params.callback([], request);
  },

  loadAdvancedConfigPartialSuccess: function(data, opt, params, request) {
    var properties = [];
    if(data.items.length && data.items.mapProperty('configurations').length) {
      var configurations = data.items.mapProperty('configurations').reduce(function(p,c) { return p.concat(c); });
      configurations.forEach(function(item) {
        var property = this.createAdvancedPropertyObject(item.StackConfigurations);
        if (property) properties.push(property);
      }, this);
    }
    params.callback(properties, request);
  },

  /**
   * Bootstrap configuration property object according to
   * format that we using in our application.
   *
   * @method createAdvancedPropertyObject
   * @param {Object} item
   * @returns {Object|Boolean} 
   */
  createAdvancedPropertyObject: function(item) {
    var serviceName = item.service_name;
    var fileName = item.type;
    /**
     * Properties from mapred-queue-acls.xml are ignored
     * Properties from capacity-scheduler.xml are ignored unless HDP stack version is 2.x or
     * HDP stack version is 1.x
     */
    if (fileName == 'mapred-queue-acls.xml') return false;
    item.isVisible = fileName != 'cluster-env.xml';
    var property = {
      serviceName: serviceName,
      name: item.property_name,
      value: item.property_value,
      description: item.property_description,
      isVisible: item.isVisible,
      isFinal: item.final === "true",
      defaultIsFinal: item.final === "true",
      filename: item.filename || fileName
    };

    return $.extend(property, this.advancedConfigIdentityData(item));
  },
  
  /**
   * Add additional properties to advanced property config object.
   * Additional logic based on `property_type`.
   *
   * @method advancedConfigIdentityData
   * @param {Object} config
   * @return {Object}
   */
  advancedConfigIdentityData: function(config) {
    var propertyData = {};
    var proxyUserGroupServices = ['HIVE', 'OOZIE', 'FALCON'];
    var nameToDisplayNameMap = {
      'smokeuser': 'Smoke Test User',
      'user_group': 'Hadoop Group',
      'mapred_user': 'MapReduce User',
      'zk_user': 'ZooKeeper User',
      'ignore_groupsusers_create': 'Skip group modifications during install'
    };
    if (config.property_type.contains('USER') || config.property_type.contains('GROUP')) {
      propertyData.id = "puppet var";
      propertyData.category = 'Users and Groups';
      propertyData.isVisible = !App.get('isHadoopWindowsStack');
      propertyData.serviceName = 'MISC';
      propertyData.isOverridable = false;
      propertyData.isReconfigurable = false;
      propertyData.displayName = nameToDisplayNameMap[config.property_name] || App.format.normalizeName(config.property_name);
      propertyData.displayType = config.property_name == 'ignore_groupsusers_create' ? 'checkbox' : 'user';
      if (config.service_name) {
        var propertyIndex = config.service_name == 'MISC' ? 30 : App.StackService.find().mapProperty('serviceName').indexOf(config.service_name);
        propertyData.belongsToService = [config.service_name];
        propertyData.index = propertyIndex;
      } else {
        propertyData.index = 30;
      }
      if (config.property_name == 'proxyuser_group') propertyData.belongsToService = proxyUserGroupServices;
    }

    if (config.property_type.contains('PASSWORD')) {
      propertyData.displayType = "password";
    }

    return propertyData;
  },

  /**
   * Get config types and config type attributes from stack service
   *
   * @param service
   * @return {object}
   */
  getConfigTypesInfoFromService: function (service) {
    var configTypes = service.get('configTypes');
    var configTypesInfo = {
      items: [],
      supportsFinal: []
    };
    if (configTypes) {
      for (var key in configTypes) {
        if (configTypes.hasOwnProperty(key)) {
          configTypesInfo.items.push(key);
          if (configTypes[key].supports && configTypes[key].supports.final === "true") {
            configTypesInfo.supportsFinal.push(key);
          }
        }
      }
    }
    return configTypesInfo;
  },

  /**
   * Get properties from server by type and tag with properties, that belong to group
   * push them to common {serviceConfigs} and call callback function
   */
  loadServiceConfigGroupOverrides: function (serviceConfigs, loadedGroupToOverrideSiteToTagMap, configGroups, callback, sender) {
    var configKeyToConfigMap = {};
    serviceConfigs.forEach(function (item) {
      if (!configKeyToConfigMap[item.filename]) {
        configKeyToConfigMap[item.filename] = {};
      }
      configKeyToConfigMap[item.filename][item.name] = item;
    });
    var typeTagToGroupMap = {};
    var urlParams = [];
    for (var group in loadedGroupToOverrideSiteToTagMap) {
      var overrideTypeTags = loadedGroupToOverrideSiteToTagMap[group];
      for (var type in overrideTypeTags) {
        var tag = overrideTypeTags[type];
        typeTagToGroupMap[type + "///" + tag] = configGroups.findProperty('name', group);
        urlParams.push('(type=' + type + '&tag=' + tag + ')');
      }
    }
    var params = urlParams.join('|');
    if (urlParams.length) {
      App.ajax.send({
        name: 'config.host_overrides',
        sender: this,
        data: {
          params: params,
          configKeyToConfigMap: configKeyToConfigMap,
          typeTagToGroupMap: typeTagToGroupMap,
          callback: callback,
          sender: sender,
          serviceConfigs: serviceConfigs
        },
        success: 'loadServiceConfigGroupOverridesSuccess'
      });
    } else {
      callback.call(sender, serviceConfigs);
    }
  },
  loadServiceConfigGroupOverridesSuccess: function (data, opt, params) {
    data.items.forEach(function (config) {
      App.config.loadedConfigurationsCache[config.type + "_" + config.tag] = config.properties;
      var group = params.typeTagToGroupMap[config.type + "///" + config.tag];
      var properties = config.properties;
      for (var prop in properties) {
        var fileName = this.getOriginalFileName(config.type);
        var serviceConfig = !!params.configKeyToConfigMap[fileName] ? params.configKeyToConfigMap[fileName][prop] : false;
        var hostOverrideValue = this.formatOverrideValue(serviceConfig, properties[prop]);
        var hostOverrideIsFinal = !!(config.properties_attributes && config.properties_attributes.final && config.properties_attributes.final[prop]);
        if (serviceConfig) {
          // Value of this property is different for this host.
          if (!Em.get(serviceConfig, 'overrides')) Em.set(serviceConfig, 'overrides', []);
          console.log("loadServiceConfigGroupOverridesSuccess(): [" + group + "] OVERRODE(" + serviceConfig.name + "): " + serviceConfig.value + " -> " + hostOverrideValue);
          serviceConfig.overrides.pushObject({value: hostOverrideValue, group: group, isFinal: hostOverrideIsFinal});
        } else {
          params.serviceConfigs.push(this.createCustomGroupConfig(prop, config, group));
        }
      }
    }, this);
    params.callback.call(params.sender, params.serviceConfigs);
  },
  /**
   * Create config with non default config group. Some custom config properties
   * can be created and assigned to non-default config group.
   *
   * @param {String} propertyName - name of the property
   * @param {Object} config - config info
   * @param {Em.Object} group - config group to set
   * @return {Object}
   **/
  createCustomGroupConfig: function (propertyName, config, group) {
    var propertyValue = config.properties[propertyName];
    var propertyObject = {
      name: propertyName,
      displayName: propertyName,
      defaultValue: propertyValue,
      value: propertyValue,
      displayType: stringUtils.isSingleLine(propertyValue) ? 'advanced' : 'multiLine',
      isSecureConfig: false,
      group: group,
      id: 'site property',
      serviceName: group.get('service.serviceName'),
      filename: this.getOriginalFileName(config.type),
      isUserProperty: true,
      isVisible: true,
      isOverridable: false
    };
    propertyObject.category = this.identifyCategory(propertyObject).name;
    group.set('switchGroupTextShort', Em.I18n.t('services.service.config_groups.switchGroupTextShort').format(group.get('name')));
    group.set('switchGroupTextFull', Em.I18n.t('services.service.config_groups.switchGroupTextFull').format(group.get('name')));
    return App.ServiceConfigProperty.create(propertyObject);
  },
  /**
   * format value of override of config
   * @param serviceConfig
   * @param hostOverrideValue
   */
  formatOverrideValue: function (serviceConfig, hostOverrideValue) {
    if (serviceConfig && serviceConfig.displayType === 'int') {
      if (/\d+m$/.test(hostOverrideValue)) {
        return hostOverrideValue.slice(0, hostOverrideValue.length - 1);
      }
    }
    return hostOverrideValue;
  },

  /**
   * Set all site property that are derived from other site-properties
   */
  setConfigValue: function (mappedConfigs, allConfigs, config) {
    var globalValue;
    if (config.value == null) {
      return;
    }
    var fkValue = config.value.match(/<(foreignKey.*?)>/g);
    var fkName = config.name.match(/<(foreignKey.*?)>/g);
    var templateValue = config.value.match(/<(templateName.*?)>/g);
    if (fkValue) {
      fkValue.forEach(function (_fkValue) {
        var index = parseInt(_fkValue.match(/\[([\d]*)(?=\])/)[1]);
        if (mappedConfigs.someProperty('name', config.foreignKey[index])) {
          globalValue = mappedConfigs.findProperty('name', config.foreignKey[index]).value;
          config.value = config.value.replace(_fkValue, globalValue);
        } else if (allConfigs.someProperty('name', config.foreignKey[index])) {
          if (allConfigs.findProperty('name', config.foreignKey[index]).value === '') {
            globalValue = allConfigs.findProperty('name', config.foreignKey[index]).defaultValue;
          } else {
            globalValue = allConfigs.findProperty('name', config.foreignKey[index]).value;
          }
          config.value = config.value.replace(_fkValue, globalValue);
        }
      }, this);
    }

    // config._name - formatted name from original config name
    if (fkName) {
      fkName.forEach(function (_fkName) {
        var index = parseInt(_fkName.match(/\[([\d]*)(?=\])/)[1]);
        if (mappedConfigs.someProperty('name', config.foreignKey[index])) {
          globalValue = mappedConfigs.findProperty('name', config.foreignKey[index]).value;
          config._name = config.name.replace(_fkName, globalValue);
        } else if (allConfigs.someProperty('name', config.foreignKey[index])) {
          if (allConfigs.findProperty('name', config.foreignKey[index]).value === '') {
            globalValue = allConfigs.findProperty('name', config.foreignKey[index]).defaultValue;
          } else {
            globalValue = allConfigs.findProperty('name', config.foreignKey[index]).value;
          }
          config._name = config.name.replace(_fkName, globalValue);
        }else{
          config.noMatchSoSkipThisConfig = true;
        }
      }, this);
    }

    //For properties in the configMapping file having foreignKey and templateName properties.
    if (templateValue) {
      templateValue.forEach(function (_value) {
        var index = parseInt(_value.match(/\[([\d]*)(?=\])/)[1]);
        if (allConfigs.someProperty('name', config.templateName[index])) {
          var globalValue = allConfigs.findProperty('name', config.templateName[index]).value;
          config.value = config.value.replace(_value, globalValue);
        } else {
          config.value = null;
        }
      }, this);
    }
  },

  /**
   * identify service name of config by its config's type
   * @param type
   * @return {string|null}
   */
  getServiceNameByConfigType: function (type) {
    var preDefinedServiceConfigs = this.get('preDefinedServiceConfigs');
    var service = preDefinedServiceConfigs.find(function (serviceConfig) {
      return !!serviceConfig.get('configTypes')[type];
    }, this);
    return service && service.get('serviceName');
  },

  /**
   * add user property
   * @param stored
   * @param isAdvanced
   * @param advancedConfigs
   * @return {Object}
   */
  addUserProperty: function (stored, isAdvanced, advancedConfigs) {
    var
      skipChangeOfDisplayType = ['ignore_groupsusers_create'],
      originalDispType = advancedConfigs.findProperty('name', stored.name) ? advancedConfigs.findProperty('name', stored.name).displayType : stored.displayType;
      configData = {
        id: stored.id,
        name: stored.name,
        displayName: App.format.normalizeName(stored.name),
        serviceName: stored.serviceName,
        value: stored.value,
        defaultValue: stored.defaultValue,
        displayType: skipChangeOfDisplayType.contains(stored.name) ? originalDispType : (stringUtils.isSingleLine(stored.value) ? 'advanced' : 'multiLine'),
        filename: stored.filename,
        isUserProperty: stored.isUserProperty === true,
        hasInitialValue: !!stored.hasInitialValue,
        isOverridable: true,
        overrides: stored.overrides,
        isRequired: false,
        isVisible: stored.isVisible,
        isFinal: stored.isFinal,
        defaultIsFinal: stored.defaultIsFinal,
        supportsFinal: stored.supportsFinal,
        showLabel: stored.showLabel !== false,
        category: stored.category
      };

    App.get('config').calculateConfigProperties(configData, isAdvanced, advancedConfigs);
    return configData;
  },

  complexConfigsTemplate: [
    {
      "id": "site property",
      "name": "capacity-scheduler",
      "displayName": "Capacity Scheduler",
      "value": "",
      "defaultValue": "",
      "description": "Capacity Scheduler properties",
      "displayType": "custom",
      "isOverridable": true,
      "isRequired": true,
      "isVisible": true,
      "isReconfigurable": true,
      "supportsFinal": false,
      "serviceName": "YARN",
      "filename": "capacity-scheduler.xml",
      "category": "CapacityScheduler"
    }
  ],

  /**
   * transform set of configs from file
   * into one config with textarea content:
   * name=value
   * @param configs
   * @param filename
   * @return {*}
   */
  fileConfigsIntoTextarea: function (configs, filename) {
    var fileConfigs = configs.filterProperty('filename', filename);
    var value = '';
    var defaultValue = '';
    var template = this.get('complexConfigsTemplate').findProperty('filename', filename);
    var complexConfig = $.extend({}, template);
    if (complexConfig) {
      fileConfigs.forEach(function (_config) {
        value += _config.name + '=' + _config.value + '\n';
        defaultValue += _config.name + '=' + _config.defaultValue + '\n';
      }, this);
      var isFinal = fileConfigs.someProperty('isFinal', true);
      complexConfig.value = value;
      complexConfig.defaultValue = defaultValue;
      complexConfig.isFinal = isFinal;
      complexConfig.defaultIsFinal = isFinal;
      configs = configs.filter(function (_config) {
        return _config.filename !== filename;
      });
      configs.push(complexConfig);
    }
    return configs;
  },

  /**
   * transform one config with textarea content
   * into set of configs of file
   * @param configs
   * @param filename
   * @return {*}
   */
  textareaIntoFileConfigs: function (configs, filename) {
    var complexConfigName = this.get('complexConfigsTemplate').findProperty('filename', filename).name;
    var configsTextarea = configs.findProperty('name', complexConfigName);
    if (configsTextarea) {
      var properties = configsTextarea.get('value').split('\n');

      properties.forEach(function (_property) {
        var name, value;
        if (_property) {
          _property = _property.split('=');
          name = _property[0];
          value = (_property[1]) ? _property[1] : "";
          configs.push(Em.Object.create({
            id: configsTextarea.get('id'),
            name: name,
            value: value,
            defaultValue: value,
            serviceName: configsTextarea.get('serviceName'),
            filename: filename,
            isFinal: configsTextarea.get('isFinal'),
            isNotDefaultValue: configsTextarea.get('isNotDefaultValue'),
            group: null
          }));
        }
      });
      return configs.without(configsTextarea);
    }
    console.log('ERROR: textarea config - ' + complexConfigName + ' is missing');
    return configs;
  },

  /**
   * trim trailing spaces for all properties.
   * trim both trailing and leading spaces for host displayType and hive/oozie datebases url.
   * for directory or directories displayType format string for further using.
   * for password and values with spaces only do nothing.
   * @param {Object} property
   * @param {Boolean} isEmberObject
   * @returns {*}
   */
  trimProperty: function (property, isEmberObject) {
    var displayType = (isEmberObject) ? property.get('displayType') : property.displayType;
    var value = (isEmberObject) ? property.get('value') : property.value;
    var name = (isEmberObject) ? property.get('name') : property.name;
    var rez;
    switch (displayType) {
      case 'directories':
      case 'directory':
      case 'datanodedirs':
        rez = value.replace(/,/g,' ').trim().split(/\s+/g).join(',');
        break;
      case 'host':
        rez = value.trim();
        break;
      case 'password':
        break;
      case 'advanced':
        if (name == 'javax.jdo.option.ConnectionURL' || name == 'oozie.service.JPAService.jdbc.url') {
          rez = value.trim();
        }
      default:
        rez = (typeof value == 'string') ? value.replace(/(\s+$)/g, '') : value;
    }
    return ((rez == '') || (rez == undefined)) ? value : rez;
  },

  OnNnHAHideSnn: function (ServiceConfig) {
    var configCategories = ServiceConfig.get('configCategories');
    var snCategory = configCategories.findProperty('name', 'SNameNode');
    var isSnnPresent = !!App.HDFSService.find('HDFS').get('snameNode');
    if (snCategory && !isSnnPresent) {
      configCategories.removeObject(snCategory);
    }
  },

  /**
   * Launches a dialog where an existing config-group can be selected, or a new
   * one can be created. This is different than the config-group management
   * dialog where host membership can be managed.
   *
   * The callback will be passed the created/selected config-group in the form
   * of {id:2, name:'New hardware group'}. In the case of dialog being cancelled,
   * the callback is provided <code>null</code>
   *
   * @param {String} groupName
   *  is closed, cancelled or OK is pressed.
   */

  saveGroupConfirmationPopup: function (groupName) {
    App.ModalPopup.show({
      header: Em.I18n.t('config.group.save.confirmation.header'),
      secondary: Em.I18n.t('config.group.save.confirmation.manage.button'),
      groupName: groupName,
      bodyClass: Ember.View.extend({
        templateName: require('templates/common/configs/saveConfigGroup')
      }),
      onSecondary: function () {
        App.router.get('mainServiceInfoConfigsController').manageConfigurationGroups();
        this.hide();
      }
    });
  },

  //Persist config groups created in step7 wizard controller
  persistWizardStep7ConfigGroups: function () {
    var installerController = App.router.get('installerController');
    var step7Controller = App.router.get('wizardStep7Controller');
      installerController.saveServiceConfigGroups(step7Controller, step7Controller.get('content.controllerName') == 'addServiceController');
      App.clusterStatus.setClusterStatus({
        localdb: App.db.data
      });
  },
  /**
   * exclude configs that depends on services which are uninstalled
   * if config doesn't have serviceName or dependent service is installed then
   * config not excluded
   */
  excludeUnsupportedConfigs: function (configs, installedServices) {
    return configs.filter(function (config) {
      return !(config.serviceName && !installedServices.contains(config.serviceName));
    });
  },

  launchConfigGroupSelectionCreationDialog: function (serviceId, configGroups, configProperty, callback, isInstaller) {
    var self = this;
    var availableConfigGroups = configGroups.slice();
    // delete Config Groups, that already have selected property overridden
    var alreadyOverriddenGroups = [];
    if (configProperty.get('overrides')) {
      alreadyOverriddenGroups = configProperty.get('overrides').mapProperty('group.name');
    }
    var result = [];
    availableConfigGroups.forEach(function (group) {
      if (!group.get('isDefault') && (!alreadyOverriddenGroups.length || !alreadyOverriddenGroups.contains(group.name))) {
        result.push(group);
      }
    }, this);
    availableConfigGroups = result;
    var selectedConfigGroup = availableConfigGroups && availableConfigGroups.length > 0 ?
      availableConfigGroups[0] : null;
    var serviceName = App.format.role(serviceId);
    App.ModalPopup.show({
      classNames: [ 'sixty-percent-width-modal' ],
      header: Em.I18n.t('config.group.selection.dialog.title').format(serviceName),
      subTitle: Em.I18n.t('config.group.selection.dialog.subtitle').format(serviceName),
      selectExistingGroupLabel: Em.I18n.t('config.group.selection.dialog.option.select').format(serviceName),
      noGroups: Em.I18n.t('config.group.selection.dialog.no.groups').format(serviceName),
      createNewGroupLabel: Em.I18n.t('config.group.selection.dialog.option.create').format(serviceName),
      createNewGroupDescription: Em.I18n.t('config.group.selection.dialog.option.create.msg').format(serviceName),
      warningMessage: '&nbsp;',
      isWarning: false,
      optionSelectConfigGroup: true,
      optionCreateConfigGroup: function () {
        return !this.get('optionSelectConfigGroup');
      }.property('optionSelectConfigGroup'),
      hasExistedGroups: function () {
        return !!this.get('availableConfigGroups').length;
      }.property('availableConfigGroups'),
      availableConfigGroups: availableConfigGroups,
      selectedConfigGroup: selectedConfigGroup,
      newConfigGroupName: '',
      disablePrimary: function () {
        return !(this.get('optionSelectConfigGroup') || (this.get('newConfigGroupName').trim().length > 0 && !this.get('isWarning')));
      }.property('newConfigGroupName', 'optionSelectConfigGroup', 'warningMessage'),
      onPrimary: function () {
        if (this.get('optionSelectConfigGroup')) {
          var selectedConfigGroup = this.get('selectedConfigGroup');
          this.hide();
          callback(selectedConfigGroup);
        } else {
          var newConfigGroupName = this.get('newConfigGroupName').trim();
          var newConfigGroup = App.ConfigGroup.create({
            id: null,
            name: newConfigGroupName,
            description: Em.I18n.t('config.group.description.default').format(new Date().toDateString()),
            isDefault: false,
            parentConfigGroup: null,
            service: (isInstaller) ? Em.Object.create({id: serviceId}) : App.Service.find().findProperty('serviceName', serviceId),
            hosts: [],
            configSiteTags: [],
            properties: []
          });
          if (!isInstaller) {
            self.postNewConfigurationGroup(newConfigGroup);
          }
          if (newConfigGroup) {
            newConfigGroup.set('parentConfigGroup', configGroups.findProperty('isDefault'));
            configGroups.pushObject(newConfigGroup);
            if (isInstaller) {
              self.persistWizardStep7ConfigGroups();
            } else {
              self.saveGroupConfirmationPopup(newConfigGroupName);
            }
            this.hide();
            callback(newConfigGroup);
          }
        }
      },
      onSecondary: function () {
        this.hide();
        callback(null);
      },
      doSelectConfigGroup: function (event) {
        var configGroup = event.context;
        console.log(configGroup);
        this.set('selectedConfigGroup', configGroup);
      },
      validate: function () {
        var msg = '&nbsp;';
        var isWarning = false;
        var optionSelect = this.get('optionSelectConfigGroup');
        if (!optionSelect) {
          var nn = this.get('newConfigGroupName');
          if (nn && configGroups.mapProperty('name').contains(nn.trim())) {
            msg = Em.I18n.t("config.group.selection.dialog.err.name.exists");
            isWarning = true;
          }
        }
        this.set('warningMessage', msg);
        this.set('isWarning', isWarning);
      }.observes('newConfigGroupName', 'optionSelectConfigGroup'),
      bodyClass: Ember.View.extend({
        templateName: require('templates/common/configs/selectCreateConfigGroup'),
        controllerBinding: 'App.router.mainServiceInfoConfigsController',
        selectConfigGroupRadioButton: Ember.Checkbox.extend({
          tagName: 'input',
          attributeBindings: ['type', 'checked', 'disabled'],
          checked: function () {
            return this.get('parentView.parentView.optionSelectConfigGroup');
          }.property('parentView.parentView.optionSelectConfigGroup'),
          type: 'radio',
          disabled: false,
          click: function () {
            this.set('parentView.parentView.optionSelectConfigGroup', true);
          },
          didInsertElement: function () {
            if (!this.get('parentView.parentView.hasExistedGroups')) {
              this.set('disabled', true);
              this.set('parentView.parentView.optionSelectConfigGroup', false);
            }
          }
        }),
        createConfigGroupRadioButton: Ember.Checkbox.extend({
          tagName: 'input',
          attributeBindings: ['type', 'checked'],
          checked: function () {
            return !this.get('parentView.parentView.optionSelectConfigGroup');
          }.property('parentView.parentView.optionSelectConfigGroup'),
          type: 'radio',
          click: function () {
            this.set('parentView.parentView.optionSelectConfigGroup', false);
          }
        })
      })
    });
  },
  /**
   * launch dialog where can be assigned another group to host
   * @param selectedGroup
   * @param configGroups
   * @param hostName
   * @param callback
   */
  launchSwitchConfigGroupOfHostDialog: function (selectedGroup, configGroups, hostName, callback) {
    var self = this;
    App.ModalPopup.show({
      header: Em.I18n.t('config.group.host.switch.dialog.title'),
      configGroups: configGroups,
      selectedConfigGroup: selectedGroup,
      disablePrimary: function () {
        return !(this.get('selectedConfigGroup.name') !== selectedGroup.get('name'));
      }.property('selectedConfigGroup'),
      onPrimary: function () {
        var newGroup = this.get('selectedConfigGroup');
        if (selectedGroup.get('isDefault')) {
          selectedGroup.set('hosts.length', selectedGroup.get('hosts.length') - 1)
        } else {
          selectedGroup.get('hosts').removeObject(hostName);
        }
        if (!selectedGroup.get('isDefault')) {
          self.updateConfigurationGroup(selectedGroup, function () {
          }, Em.K);
        }

        if (newGroup.get('isDefault')) {
          newGroup.set('hosts.length', newGroup.get('hosts.length') + 1)
        } else {
          newGroup.get('hosts').pushObject(hostName);
        }
        callback(newGroup);
        if (!newGroup.get('isDefault')) {
          self.updateConfigurationGroup(newGroup, function () {
          }, Em.K);
        }
        this.hide();
      },
      bodyClass: Ember.View.extend({
        templateName: require('templates/utils/config_launch_switch_config_group_of_host')
      })
    });
  },
  /**
   * Create a new config-group for a service.
   *
   * @param newConfigGroupData   config group to post to server
   * @param callback    Callback function for Success or Error handling
   * @return  Returns the created config-group
   */
  postNewConfigurationGroup: function (newConfigGroupData, callback) {
    var dataHosts = [];
    newConfigGroupData.get('hosts').forEach(function (_host) {
      dataHosts.push({
        host_name: _host
      });
    }, this);
    var sendData = {
      name: 'config_groups.create',
      data: {
        'group_name': newConfigGroupData.get('name'),
        'service_id': newConfigGroupData.get('service.id'),
        'description': newConfigGroupData.get('description'),
        'hosts': dataHosts
      },
      success: 'successFunction',
      error: 'errorFunction',
      successFunction: function (response) {
        newConfigGroupData.set('id', response.resources[0].ConfigGroup.id);
        if (callback) {
          callback();
        }
      },
      errorFunction: function (xhr, text, errorThrown) {
        if (callback) {
          callback(xhr, text, errorThrown);
        }
        console.error('Error in creating new Config Group');
      }
    };
    sendData.sender = sendData;
    App.ajax.send(sendData);
    return newConfigGroupData;
  },

  /**
   * PUTs the new configuration-group on the server.
   * Changes possible here are the name, description and
   * host memberships of the configuration-group.
   *
   * @param {App.ConfigGroup} configGroup Configuration group to update
   * @param {Function} successCallback
   * @param {Function} errorCallback
   */
  updateConfigurationGroup: function (configGroup, successCallback, errorCallback) {
    var putConfigGroup = {
      ConfigGroup: {
        group_name: configGroup.get('name'),
        description: configGroup.get('description'),
        tag: configGroup.get('service.id'),
        hosts: [],
        desired_configs: []
      }
    };
    configGroup.get('hosts').forEach(function (h) {
      putConfigGroup.ConfigGroup.hosts.push({
        host_name: h
      });
    });
    configGroup.get('configSiteTags').forEach(function (cst) {
      putConfigGroup.ConfigGroup.desired_configs.push({
        type: cst.get('site'),
        tag: cst.get('tag')
      });
    });

    var sendData = {
      name: 'config_groups.update',
      data: {
        id: configGroup.get('id'),
        data: putConfigGroup
      },
      success: 'successFunction',
      error: 'errorFunction',
      successFunction: function () {
        if (successCallback) {
          successCallback();
        }
      },
      errorFunction: function (xhr, text, errorThrown) {
        if (errorCallback) {
          errorCallback(xhr, text, errorThrown);
        }
      }
    };
    sendData.sender = sendData;
    App.ajax.send(sendData);
  },

  clearConfigurationGroupHosts: function (configGroup, successCallback, errorCallback) {
    configGroup = jQuery.extend({}, configGroup);
    configGroup.set('hosts', []);
    this.updateConfigurationGroup(configGroup, successCallback, errorCallback);
  },

  deleteConfigGroup: function (configGroup, successCallback, errorCallback) {
    var sendData = {
      name: 'common.delete.config_group',
      sender: this,
      data: {
        id: configGroup.get('id')
      },
      success: 'successFunction',
      error: 'errorFunction',
      successFunction: function () {
        if (successCallback) {
          successCallback();
        }
      },
      errorFunction: function (xhr, text, errorThrown) {
        if (errorCallback) {
          errorCallback(xhr, text, errorThrown);
        }
      }
    };
    sendData.sender = sendData;
    App.ajax.send(sendData);
  },

  /**
   * Gets all the configuration-groups for the given service.
   *
   * @param serviceId
   *          (string) ID of the service. Ex: HDFS
   */
  getConfigGroupsForService: function (serviceId) {

  },

  /**
   * Gets all the configuration-groups for a host.
   *
   * @param hostName
   *          (string) host name used to register
   */
   getConfigGroupsForHost: function (hostName) {

  },

  /**
   * Generate minimal config property object used in *_properties.js files.
   * Example:
   * <code>
   *   var someProperties = App.config.generateConfigPropertiesByName([
   *    'property_1', 'property_2', 'property_3'], { category: 'General', filename: 'myFileName'});
   *   // someProperties contains Object[]
   *   [
   *    {
   *      name: 'property_1',
   *      displayName: 'property_1',
   *      isVisible: true,
   *      isReconfigurable: true,
   *      category: 'General',
   *      filename: 'myFileName'
   *    },
   *    .......
   *   ]
   * </code>
   * @param {Array} names
   * @param {Object} properties - additional properties which will merge with base object definition
   * @returns {*}
   */
  generateConfigPropertiesByName: function(names, properties) {
    return names.map(function (item) {
      var baseObj = {
        name: item,
        displayName: item,
        isVisible: true,
        isReconfigurable: true
      };
      if (properties) return $.extend(baseObj, properties);
      else return baseObj;
    });
  },

  /**
   * replace some values in config property
   * @param {string} name
   * @param {string} express
   * @param {string} value
   * @param {string} globValue
   * @return {string}
   * @private
   * @method replaceConfigValues
   */
  replaceConfigValues: function (name, express, value, globValue) {
    if (name == 'templeton.hive.properties') {
      globValue = globValue.replace(/,/g, '\\,');
    }
    return value.replace(express, globValue);
  }
});
