'use strict';
(function() {
  window.DSA = window.DSA || {};

  DSA.dataSetManager = {
    dataSetRecords: {},

    // ----------
    get: function(key, success, failure) {
      var self = this;

      var successOutput, failureOutput, successMeta;
      var record = this.dataSetRecords[key];
      if (!record) {
        failureOutput = 'unknown dataSet: ' + key;
      } else if (record.failure) {
        failureOutput = key + ' has invalid data';
      } else if (record.dataSet) {
        successOutput = record.dataSet;
        successMeta = record.meta;
      } else if (!record.loader) {
        failureOutput = 'dataSet with no loader: ' + key;
      }

      if (successOutput || failureOutput) {
        // Keeping it async
        setTimeout(function() {
          if (successOutput) {
            success(successOutput, successMeta);
          } else {
            console.error(failureOutput);
            failure(failureOutput);
          }
        }, 1);

        return;
      }

      record.loader(function(dataSet, meta) {
        if (self.validate(key, dataSet)) {
          record.dataSet = dataSet;
          record.meta = meta;
          success(record.dataSet, record.meta);
        } else {
          record.failed = true;
          failure(key + ' has invalid data');
        }
      });
    },

    // ----------
    register: function(key, dataSetOrFunction) {
      console.assert(!this.dataSetRecords[key], 'should only register a dataSet once');

      if (_.isFunction(dataSetOrFunction)) {
        this.dataSetRecords[key] = {
          loader: dataSetOrFunction
        };
      } else {
        if (this.validate(key, dataSetOrFunction)) {
          this.dataSetRecords[key] = {
            dataSet: dataSetOrFunction
          };
        } else {
          this.dataSetRecords[key] = {
            failed: true
          };
        }
      }
    },

    // ----------
    validate: function(key, dataSet) {
      if (!dataSet || !dataSet.length) {
        console.error('empty dataSet:', key);
        return false;
      }

      var ok = true;
      _.each(dataSet, function(layer) {
        ok = DSA.validateLayer(layer, key) && ok;
      });

      return ok;
    }
  };
})();
