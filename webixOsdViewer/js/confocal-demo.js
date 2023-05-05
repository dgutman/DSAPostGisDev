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
      this.viewerStateIndex = -1;

      this.viewerStates = [
        this.makeViewerState('VivaStack #1'),
        this.makeViewerState('VivaStack #3')
      ];

      var macroTS = {
        sliceNum: 0,
        tileHeight: 256,
        tileWidth: 256,
        minLevel: 0,
        height: 13000,
        width: 13000,
        imageName: 'v0000050.bmp',
        girderId: '5b81f79b92ca9a0019f017b1',
        getTileUrl: function(level, x, y) {
          return (
            'http://dermannotator.org:8080/api/v1/item/5b81f79b92ca9a0019f017b1/tiles/zxy/' +
            level +
            '/' +
            x +
            '/' +
            y +
            '?edge=crop'
          );
        },
        maxLevel: 7
      };

      this.overview = OpenSeadragon({
        element: document.querySelector('.overview-container'),
        tileSources: macroTS,
        prefixUrl: '/lib/openseadragon/images/',
        maxZoomPixelRatio: 6,
        crossOriginPolicy: 'Anonymous',
        zoomPerClick: 1
      });

      var overlay = this.overview.svgOverlay();

      var rect1 = DSA.createSVGElement('rect', overlay.node(), {
        x: 0.31,
        y: 0.16,
        width: 0.15,
        height: 0.15,
        stroke: 'red',
        fill: 'none',
        'stroke-width': 0.005 ,
        'pointer-events': 'all'
      });

      rect1.addEventListener('click', function() {
        self.startViewer(0);
      });

      var rect2 = DSA.createSVGElement('rect', overlay.node(), {
        x: 0.62,
        y: 0.46,
        width: 0.15,
        height: 0.15,
        stroke: 'blue',
        fill: 'none',
        'stroke-width': 0.005,
        'pointer-events': 'all'
      });

      rect2.addEventListener('click', function() {
        self.startViewer(1);
      });

      this.$layerSlider.on('input', function() {
        self.updateLayer();
      });

      this.startViewer(0);
    },

    // ----------
    makeViewerState: function(key) {
      var tileSources = App.confocalZStack[key];

      var layers = _.map(tileSources, function(tileSource) {
        return DSA.makeLayer({
          tileSource: tileSource
        });
      });

      return {
        layers: layers,
        layerIndex: layers.length - 1
      };
    },

    // ----------
    startViewer: function(index) {
      var self = this;
      if (index === this.viewerStateIndex) {
        return;
      }

      var state = this.viewerStates[index];
      if (!state) {
        console.error('bad index', index);
        return;
      }

      this.viewerStateIndex = index;
      this.viewerState = state;

      if (this.viewer) {
        this.viewer.destroy();
      }

      this.viewer = new DSA.OverlaidViewer({
        container: document.querySelector('.viewer-container'),
        state: state,
        options: {
          prefixUrl: '/lib/openseadragon/images/',
          maxZoomPixelRatio: 5
        },
        onOpen: function() {
          self.updateLayer();
        }
      });

      this.$layerSlider.attr({
        min: 0,
        max: this.viewerState.layers.length - 1
      });

      this.$layerSlider.val(this.viewerState.layers.length - 1 - this.viewerState.layerIndex);
    },

    // ----------
    updateLayer: function() {
      var self = this;

      var index = this.viewerState.layers.length - 1 - parseInt(this.$layerSlider.val(), 10);
      var i, visible;
      for (i = 0; i < this.viewerState.layers.length; i++) {
        visible = i === index || i === index - 1;
        this.viewerState.layers[i].opacity = visible ? 1 : 0;
      }

      this.update();

      this.viewerState.layerIndex = index;

      var tileSource = this.viewerState.layers[index].tileSource;
      this.$layerName.text(tileSource.imageName);

      this.$layers.empty();

      this.addSlider({
        container: this.$layers,
        label: 'Opacity',
        min: 0,
        max: 1,
        step: 0.01,
        value: this.viewerState.layers[index].opacity,
        onChange: function(value) {
          self.viewerState.layers[index].opacity = value;
          self.update();
        }
      });

      this.addSlider({
        container: this.$layers,
        label: 'Colorize',
        min: 0,
        max: 1,
        step: 0.01,
        value: this.viewerState.layers[index].colorize,
        onChange: function(value) {
          self.viewerState.layers[index].colorize = value;
          self.update();
        }
      });

      this.addSlider({
        container: this.$layers,
        label: 'imgProcess',
        min: 1,
        max: 9,
        step: 2,
        value: this.viewerState.layers[index].imgProcess,
        onChange: function(value) {
          self.viewerState.layers[index].imgProcess = value;
          self.update();
        }
      });

      this.addSlider({
        container: this.$layers,
        label: 'Hue',
        min: 0,
        max: 360,
        step: 1,
        value: this.viewerState.layers[index].hue,
        onChange: function(value) {
          self.viewerState.layers[index].hue = value;
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
      checkbox.checked = true;
      label.appendChild(checkbox);

      var labelText = document.createTextNode(' Layer ' + (index + 1));
      label.appendChild(labelText);

      label.addEventListener('click', function() {
        self.viewerState.layers[index].shown = !!checkbox.checked;
        self.update();
      });
    },

    // ----------
    addShim: function(index) {
      var self = this;
      var layers = document.querySelector('.layers');

      var pixelWidth = this.viewer.getLayerPixelWidth(index);
      var pixelHeight = this.viewer.getLayerPixelWidth(index);
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
      this.viewer.setState(this.viewerState);
    }
  });

  // ----------
  setTimeout(function() {
    App.init();
  }, 1);
})();
