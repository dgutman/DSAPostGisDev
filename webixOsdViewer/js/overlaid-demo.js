'use strict';
(function() {
  // ----------
  window.App = _.extend(window.App || {}, {
    // ----------
    init: function() {
      var self = this;

      this.$layerSlider = $('.layer-slider');
      this.$layerName = $('.layer-name');
      this.$layers = $('.layers');

      var urlParams = DSA.getUrlParams();
      if (urlParams.data === 'thrive') {
        this.layers = _.map(App.demoTileSources.ThriveExampleSet, function(tileSource) {
          return DSA.makeLayer({
            tileSource: tileSource,
            name: tileSource.url
          });
        });
      } else if (urlParams.data === 'smm') {
        var items = _.filter(App.dsaItems, function(item) {
          return item.groupName === 'SMM204_POST_F';
        });

        this.layers = _.map(items, function(item) {
          return DSA.makeLayer({
            tileSource: item.tileSource,
            name: item.name
          });
        });
      } else {
        this.layers = _.map(App.demoTileSources.exampleSet1, function(tileSource) {
          return DSA.makeLayer({
            tileSource: tileSource,
            name: tileSource.url
          });
        });
      }

      this.viewer = new DSA.OverlaidViewer({
        container: document.querySelector('.viewer-container'),
        state: {
          layers: this.layers
        },
        options: {
          prefixUrl: '/lib/openseadragon/images/',
          maxZoomPixelRatio: 5
        },
        onOpen: function() {
          self.updateLayer();
        }
      });

      var overlay = this.viewer.svgOverlay(); // TODO: Use this

      this.$layerSlider.attr({
        min: 0,
        max: this.layers.length - 1
      });

      this.$layerSlider.val(0);

      this.$layerSlider.on('input', function() {
        self.updateLayer();
      });
    },

    // ----------
    updateLayer: function() {
      var self = this;

      var index = this.layers.length - 1 - parseInt(this.$layerSlider.val(), 10);
      var i, visible;
      for (i = 0; i < this.layers.length; i++) {
        visible = i === index || i === index - 1;
        this.layers[i].opacity = visible ? 1 : 0;
      }

      this.update();

      var layer = this.layers[index];
      this.$layerName.text(layer.name);

      this.$layers.empty();

      this.addSlider({
        container: this.$layers,
        label: 'Opacity',
        min: 0,
        max: 1,
        step: 0.01,
        value: this.layers[index].opacity,
        onChange: function(value) {
          self.layers[index].opacity = value;
          self.update();
        }
      });

      this.addSlider({
        container: this.$layers,
        label: 'Colorize',
        min: 0,
        max: 1,
        step: 0.01,
        value: this.layers[index].colorize,
        onChange: function(value) {
          self.layers[index].colorize = value;
          self.update();
        }
      });

      this.addSlider({
        container: this.$layers,
        label: 'Hue',
        min: 0,
        max: 360,
        step: 1,
        value: this.layers[index].hue,
        onChange: function(value) {
          self.layers[index].hue = value;
          self.update();
        }
      });

      this.addMenu({
        container: this.$layers,
        label: 'Erosion',
        labels: ['None', '3x3 Kernel', '5x5 Kernel', '7x7 Kernel', '9x9 Kernel'],
        values: [1, 3, 5, 7, 9],
        value: this.layers[index].erosionKernel,
        onChange: function(value) {
          self.layers[index].erosionKernel = value;
          self.update();
        }
      });

      this.addShim(index);
    },

    // ----------
    addCheckbox: function(index) {
      var self = this;
      var layers = document.querySelector('.layers');

      var div = document.createElement('div');
      layers.appendChild(div);

      var label = document.createElement('label');
      div.appendChild(label);

      var checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.checked = this.layers[index].shown;
      label.appendChild(checkbox);

      var labelText = document.createTextNode(' Layer ' + (index + 1));
      label.appendChild(labelText);

      label.addEventListener('click', function() {
        self.layers[index].shown = !!checkbox.checked;
        self.update();
      });
    },

    // ----------
    addShim: function(index) {
      var self = this;
      var layers = document.querySelector('.layers');

      var shimFactor = 0.2;
      var pixelWidth = Math.round(this.viewer.getLayerPixelWidth(index) * shimFactor);
      var pixelHeight = Math.round(this.viewer.getLayerPixelWidth(index) * shimFactor);
      var offset = this.viewer.getLayerPixelOffset(index);

      var div = document.createElement('div');
      layers.appendChild(div);

      var shimText = document.createTextNode(' Shim X: ');
      div.appendChild(shimText);

      var xSlider = document.createElement('input');
      xSlider.type = 'range';
      xSlider.min = -pixelWidth;
      xSlider.max = pixelWidth;
      xSlider.step = 1;
      xSlider.value = offset.x;
      div.appendChild(xSlider);

      var xLabel = document.createTextNode(' ' + xSlider.value);
      div.appendChild(xLabel);

      div = document.createElement('div');
      layers.appendChild(div);

      shimText = document.createTextNode(' Shim Y: ');
      div.appendChild(shimText);

      var ySlider = document.createElement('input');
      ySlider.type = 'range';
      ySlider.min = -pixelHeight;
      ySlider.max = pixelHeight;
      ySlider.step = 1;
      ySlider.value = offset.y;
      div.appendChild(ySlider);

      var yLabel = document.createTextNode(' ' + ySlider.value);
      div.appendChild(yLabel);

      var update = function() {
        self.viewer.setLayerPixelOffset(index, xSlider.value, ySlider.value);
        xLabel.textContent = ' ' + xSlider.value;
        yLabel.textContent = ' ' + ySlider.value;
      };

      xSlider.addEventListener('input', update);
      ySlider.addEventListener('input', update);
    },

    // ----------
    update: function() {
      this.viewer.setState({
        layers: this.layers
      });
    }
  });

  // ----------
  setTimeout(function() {
    App.init();
  }, 1);
})();
