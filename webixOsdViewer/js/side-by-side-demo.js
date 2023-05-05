'use strict';
(function () {
  // ----------
  window.App = _.extend(window.App || {}, {
    // ----------
    init: function () {
      var self = this;

      this.$top = $('.top');
      this.$bottom = $('.bottom');
      this.$sideBySideControls = $('.side-by-side-controls');

      var urlParams = DSA.getUrlParams();

      this.noneRadio = document.querySelector('.none-radio');
      this.addRadio = document.querySelector('.add-radio');
      this.removeRadio = document.querySelector('.remove-radio');
      this.syncCheckbox = document.querySelector('.sync-checkbox');
      var combineCheckbox = document.querySelector('.combine-checkbox');

      this.noneRadio.addEventListener('click', function () {
        self.viewer.setClickMode('none');
      });

      this.addRadio.addEventListener('click', function () {
        self.viewer.setClickMode('add');
      });

      this.removeRadio.addEventListener('click', function () {
        self.viewer.setClickMode('remove');
      });

      this.syncCheckbox.addEventListener('click', function () {
        self.viewer.setSyncMode(self.syncCheckbox.checked);
      });

      combineCheckbox.addEventListener('click', function () {
        if (combineCheckbox.checked) {
          self.startCombined();
        } else {
          self.startSeparate();
        }
      });

      var dataSetKey = 'exampleSet1With2';
      if (urlParams.data === 'derm') {
        dataSetKey = 'dsaItemsWith2';
      }
      if (urlParams.data === 'llmpp') {
        dataSetKey = 'llmpp';
      }

      if (urlParams.data === 'dermviva') {
        dataSetKey = 'dermviva';
      }

      console.log('loading' + dataSetKey);

      DSA.dataSetManager.get(
        dataSetKey,
        function (dataSet) {
          self.originalLayers = _.map(dataSet, function (layer) {
            return _.extend({}, layer, {
              rotation: 0
            });
          });

          self.startSeparate();
        },
        function (error) {
          alert(error);
        }
      );
    },

    // ----------
    startSeparate: function () {
      var self = this;

      if (this.viewer) {
        this.viewer.destroy();
      }

      this.$sideBySideControls.show();

      this.layers = this.originalLayers.slice().reverse();

      var tileSources = _.pluck(this.layers, 'tileSource');

      this.viewer = new DSA.SideBySideViewer({
        container: document.querySelector('.viewer-container'),
        state: {
          layers: this.layers
        },
        options: {
          prefixUrl: '/lib/openseadragon/images/',
          maxZoomPixelRatio: 5,
          crossOriginPolicy: true
        },
        onOpen: function () {
          self.addColorizeSliders();
          self.updateShims(true);
        },
        onAddMarker: function (layerIndex, marker) {
          self.layers[layerIndex].markers.push(marker);
          self.viewer.setState({
            layers: self.layers
          });
        },
        onRemoveMarker: function (layerIndex, markerIndex) {
          self.layers[layerIndex].markers.splice(markerIndex, 1);
          self.viewer.setState({
            layers: self.layers
          });
        }
      });

      if (this.addRadio.checked) {
        this.viewer.setClickMode('add');
      } else if (this.removeRadio.checked) {
        this.viewer.setClickMode('remove');
      }

      this.viewer.setSyncMode(this.syncCheckbox.checked);

      this.$top.empty();
      this.$bottom.empty();
    },

    // ----------
    startCombined: function () {
      var self = this;

      if (this.viewer) {
        this.viewer.destroy();
      }

      this.$sideBySideControls.hide();

      this.layers = this.originalLayers.slice();

      this.viewer = new DSA.OverlaidViewer({
        container: document.querySelector('.viewer-container'),
        state: {
          layers: this.layers
        },
        options: {
          prefixUrl: '/lib/openseadragon/images/',
          maxZoomPixelRatio: 5,
          crossOriginPolicy: true
        },
        onOpen: function () {
          self.addColorizeSliders(true);
          self.updateShims(true);
        }
      });

      this.$top.empty();
      this.$bottom.empty();

      this.addSlider({
        container: this.$top,
        label: 'Opacity',
        min: 0,
        max: 1,
        step: 0.01,
        value: this.layers[1].opacity,
        onChange: function (value) {
          self.layers[1].opacity = value;
          self.update();
        }
      });

      this.addSlider({
        container: this.$bottom,
        label: 'Opacity',
        min: 0,
        max: 1,
        step: 0.01,
        value: this.layers[0].opacity,
        onChange: function (value) {
          self.layers[0].opacity = value;
          self.update();
        }
      });
    },

    // ----------
    addColorizeSliders: function (flip) {
      var self = this;

      var topIndex, bottomIndex;
      if (flip) {
        topIndex = 1;
        bottomIndex = 0;
      } else {
        topIndex = 0;
        bottomIndex = 1;
      }

      this.addSliderSet({
        container: this.$top,
        layerIndex: topIndex
      });

      this.addSliderSet({
        container: this.$bottom,
        layerIndex: bottomIndex
      });
    },

    // ----------
    addSliderSet: function (args) {
      var self = this;

      var colorizeSlider = this.addSlider({
        container: args.container,
        label: 'Colorize',
        min: 0,
        max: 1,
        step: 0.01,
        value: this.layers[args.layerIndex].colorize,
        onChange: function (value) {
          self.layers[args.layerIndex].colorize = value;
          self.update();
        }
      });

      var hueSlider = this.addSlider({
        container: args.container,
        label: 'Hue',
        min: 0,
        max: 360,
        step: 1,
        value: this.layers[args.layerIndex].hue,
        onChange: function (value) {
          self.layers[args.layerIndex].hue = value;
          self.update();
        }
      });

      this.addSlider({
        container: args.container,
        label: 'Brightness',
        min: -1,
        max: 1,
        step: 0.01,
        value: this.layers[args.layerIndex].brightness,
        onChange: function (value) {
          self.layers[args.layerIndex].brightness = value;
          self.update();
        }
      });

      this.addSlider({
        container: args.container,
        label: 'Contrast',
        min: -1,
        max: 1,
        step: 0.01,
        value: this.layers[args.layerIndex].contrast,
        onChange: function (value) {
          self.layers[args.layerIndex].contrast = value;
          self.update();
        }
      });

      var shimFactor = 1;
      var pixelWidth = Math.round(this.viewer.getLayerPixelWidth(args.layerIndex) * shimFactor);
      var pixelHeight = Math.round(this.viewer.getLayerPixelWidth(args.layerIndex) * shimFactor);

      this.addSlider({
        container: args.container,
        label: 'Shim X',
        min: -pixelWidth,
        max: pixelWidth,
        step: 1,
        value: this.layers[args.layerIndex].shimX,
        onChange: function (value) {
          self.layers[args.layerIndex].shimX = value;
          self.update();
        }
      });

      this.addSlider({
        container: args.container,
        label: 'Shim Y',
        min: -pixelHeight,
        max: pixelHeight,
        step: 1,
        value: this.layers[args.layerIndex].shimY,
        onChange: function (value) {
          self.layers[args.layerIndex].shimY = value;
          self.update();
        }
      });

      this.addSlider({
        container: args.container,
        label: 'Rotation',
        min: -180,
        max: 180,
        step: 0.1,
        value: this.layers[args.layerIndex].rotation,
        onChange: function (value) {
          self.layers[args.layerIndex].rotation = value;
          self.update();
        }
      });

      this.addColorPalette({
        container: args.container,
        onClick: function (hue) {
          self.layers[args.layerIndex].colorize = 1;
          colorizeSlider.setValue(1);
          self.layers[args.layerIndex].hue = hue;
          hueSlider.setValue(hue);
          self.update();
        }
      });
    },

    // ----------
    update: function () {
      this.viewer.setState({
        layers: this.layers
      });

      this.updateShims();
    },

    // ----------
    updateShims: function (immediately) {
      var self = this;
      _.each(this.layers, function (layer, layerIndex) {
        self.viewer.setLayerPixelOffset(layerIndex, layer.shimX, layer.shimY, immediately);
      });
    }
  });

  // ----------
  setTimeout(function () {
    App.init();
  }, 1);
})();
