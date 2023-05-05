'use strict';
(function() {
  // ----------
  var State = function(data) {
    this.data = data;
  };

  // ----------
  _.extend(
    State.prototype,
    {
      // ----------
      get: function() {
        return this.data;
      },

      // ----------
      set: function(data) {
        this.data = data;
        this.emitEvent('change');
      }
    },
    EventEmitter.prototype
  );

  // ----------
  window.App = _.extend(window.App || {}, {
    // ----------
    init: function() {
      var self = this;

      this.$topNav = $('.top-nav');

      this.state = new State({
        opacity: 0.5
      });

      this.state.on('change', function() {
        if (self.canvasOverlay) {
          self.canvasOverlay.setOpacity(self.state.get().opacity);
        }
      });

      this.addSlider({
        container: this.$topNav,
        label: 'Derived Overlay Opacity',
        min: 0,
        max: 1,
        step: 0.01,
        value: 0.5,
        onChange: function(value) {
          self.state.set({
            opacity: value
          });
        }
      });

      this.viewer = OpenSeadragon({
        element: document.querySelector('.viewer-container'),
        prefixUrl: '/lib/openseadragon/images/',
        maxZoomPixelRatio: 5,
        crossOriginPolicy: 'Anonymous',
        tileSources: [App.dsaItems[0].tileSource]
      });

      this.canvasOverlay = new DSA.CanvasOverlay({
        osdViewer: this.viewer,
        opacity: this.state.get().opacity,
        sizeFactor: 0.5,
        onUpdate: function(context) {
          var sCanvas = self.viewer.drawer.canvas;
          var sContext = self.viewer.drawer.context;
          var dContext = context;
          var dCanvas = dContext.canvas;

          dContext.clearRect(0, 0, dCanvas.width, dCanvas.height);
          dContext.drawImage(
            sCanvas,
            0,
            0,
            sCanvas.width,
            sCanvas.height,
            0,
            0,
            dCanvas.width,
            dCanvas.height
          );

          self.process(dCanvas, dContext);
        }
      });
    },

    // ----------
    process: function(canvas, context) {
      var imageData = context.getImageData(0, 0, canvas.width, canvas.height);

      var gridSize = 100;
      var gridColumnCount = Math.ceil(imageData.width / gridSize);
      var gridRowCount = Math.ceil(imageData.height / gridSize);
      var gridCellCount = gridColumnCount * gridRowCount;
      var rGrid = new Int32Array(gridCellCount);
      var gGrid = new Int32Array(gridCellCount);
      var bGrid = new Int32Array(gridCellCount);
      var countGrid = new Int32Array(gridCellCount);
      var x = 0;
      var y = 0;
      var i, key, cell, column, row, index;
      for (i = 0; i < imageData.data.length; i += 4) {
        column = Math.floor(x / gridSize);
        row = Math.floor(y / gridSize);
        index = row * gridColumnCount + column;

        if (imageData.data[i + 3] >= 128) {
          rGrid[index] += imageData.data[i];
          gGrid[index] += imageData.data[i + 1];
          bGrid[index] += imageData.data[i + 2];
          countGrid[index]++;
        }

        x++;
        if (x >= imageData.width) {
          x = 0;
          y++;
        }
      }

      var count;
      for (i = 0; i < gridCellCount; i++) {
        count = countGrid[i];
        rGrid[i] = Math.round(rGrid[i] / count);
        gGrid[i] = Math.round(gGrid[i] / count);
        bGrid[i] = Math.round(bGrid[i] / count);
      }

      x = 0;
      y = 0;
      for (i = 0; i < imageData.data.length; i += 4) {
        column = Math.floor(x / gridSize);
        row = Math.floor(y / gridSize);
        index = row * gridColumnCount + column;

        imageData.data[i] = rGrid[index];
        imageData.data[i + 1] = gGrid[index];
        imageData.data[i + 2] = bGrid[index];
        imageData.data[i + 3] = Math.min(imageData.data[i + 3], 255);

        x++;
        if (x >= imageData.width) {
          x = 0;
          y++;
        }
      }

      context.putImageData(imageData, 0, 0);
    }
  });

  // ----------
  setTimeout(function() {
    App.init();
  }, 1);
})();
