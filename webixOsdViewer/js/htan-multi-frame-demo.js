'use strict';

var viewer = {};

(function () {
  // ----------
  var dataSetKeys = ['jcADRC', 'multiFrameSet', 'MERFISH_Frame'];

  // ----------
  window.App = _.extend(window.App || {}, {
    // ----------
    init: function () {
      var self = this;

      this.$sideNav = $('.side-nav');
      this.$gridCheckbox = $('.grid-checkbox');
      this.$info = $('.info');
      this.$pixelColor = $('.pixel-color');
      this.$dataMenu = $('.data-menu');
      this.$exportButton = $('.export-button');
      this.$shareButton = $('.share-button');
      this.$fileInput = $('#import-file-input');
      this.$copyAlert = $('.copy-alert');
      this.gridShown = false;
      this.$gridCheckbox[0].checked = true;
      this.showGrid = this.$gridCheckbox[0].checked;
      this.dataSetKey = '';
      this.controlSets = [];
      this.extraViewers = [];
      this.extraViewersFollow = true;

      var colorStack = ['blue', 'green', 'red', 'yellow', 'orange'];

      this.throttledUpdateGridValue = _.throttle(this.updateGridValue, 250);

      function handleMouseOver(d, i, nodes) {
        var node = nodes[i];
        d3.select(node).attr('stroke', 'white');
      }

      function handleMouseOut(d, i, nodes) {
        var node = nodes[i];
        d3.select(node).attr('stroke', 'transparent');
      }

      //Working on adding the SVG rendering code
      var combineCheckbox = document.querySelector('.combine-checkbox');

      combineCheckbox.addEventListener('click', function () {
        var svgOverlay = self.viewer.getOsdViewer().svgOverlay();
        var rootNode = d3.select(svgOverlay.node());

        /* Adding in a new mask file based on the merFish sample */
        $.ajax('js/merFishCellMask.json').then(function (data, idx) {
          var scale = self.viewer.getOsdViewer().world.getHomeBounds().width / 4096;

          viewer = self.viewer.getOsdViewer();

          var xOffset = 8000; //This is to be determined--- as well as the scaling factor...
		var yOffset = 23000;

          data.forEach(function (pgn, idx) {
            if (Math.random() < 0.2) {
              // Sample Ratio
              var fillColor = colorStack[idx % 5];

              // Scale the values down so they appear inside the bounds of the viewer
              var points = pgn.spxBoundaries
                .split(' ')
                .map(function (pair) {
				   var x = parseFloat( pair.split(",")[0] - xOffset) * scale;
				   var y = parseFloat( pair.split(",")[1] - yOffset) * scale;

		//Changed logic to allow the x and y offset to be changed individually... need to figure out global coords
 			var pair = x+","+y;
                  return pair
              //      .split(',')
              //      .map(function (value) {
              //        return parseFloat(value - xOffset) * scale;
              //      })
              //      .join(',');
                })
                .join(' ');

                rootNode
                .append('polygon')
                .style('fill', fillColor)
                .attr('points', points)
                .attr('class', 'boundaryClass')
                .attr('stroke-width', 10 * scale)
                .on('mouseover', handleMouseOver)
                .on('mouseout', handleMouseOut);
            }
          });
        });
      });

      var urlParams = DSA.getUrlParams();

      _.each(dataSetKeys, function (key) {
        $('<option>').text(key).val(key).appendTo(self.$dataMenu);
      });

      this.$dataMenu.on('change', function () {
        var key = self.$dataMenu.val();
        self.loadDataSet(key);
      });

      this.$gridCheckbox.on('change', function () {
        self.showGrid = self.$gridCheckbox[0].checked;
        self.$info.text('');
        self.viewer.getOsdViewer().forceRedraw();
      });

      this.$exportButton.on('click', function () {
        self.export();
      });

      this.$fileInput.on('change', function (event) {
        self.import(event.target.files[0]);
      });

      this.$shareButton.on('click', function () {
        self.share();
      });

      this.histogramViewer = new DSA.HistogramViewer({
        $el: $('.main-histogram'),
      });

      DSA.makeServerDataSet(
        'TONSIL-1_40X',
        'https://imaging.htan.dev/girder/api/v1',
        '5f80b02f1720fd517a5bd0d7'
      );

      // Load in URL params
      if (urlParams.grid) {
        if (urlParams.grid === '1') {
          this.showGrid = true;
        } else if (urlParams.grid === '0') {
          this.showGrid = false;
        }

        this.$gridCheckbox[0].checked = this.showGrid;
      }

      var layers;
      if (urlParams.layers) {
        // Add the quotes back in so it's valid JSON
        var layersString = urlParams.layers.replace(/([{,]+)([^}]*?):/g, '$1"$2":');

        try {
          layers = JSON.parse(layersString);
        } catch (e) {
          console.error(e);
        }

        if (layers) {
          layers = _.map(layers, function (layer) {
            // Turn the "shown" back into a boolean, assuming that a missing value is equal to false.
            layer.shown = layer.shown === 1;

            // Reconstitue with default values as needed
            return DSA.makeLayer(layer);
          });
        }
      }

      this.loadDataSet(urlParams.data, layers);
    },

    // ----------
    loadDataSet: function (key, fromLayers) {
      var self = this;

      if (!_.includes(dataSetKeys, key)) {
        if (fromLayers) {
          alert('Unknown dataset: ' + key);
          return;
        }

        key = 'multiFrameSet';
      }

      if (key === this.dataSetKey) {
        if (fromLayers) {
          this.copyLayers(fromLayers);
          this.update();
        }

        return;
      }

      DSA.dataSetManager.get(
        key,
        function (dataSet, meta) {
          console.log('dataset meta', meta);
          self.metadata = meta;
          self.dataSetKey = key;
          self.$dataMenu.val(key);
          self.layers = DSA.deepCopy(dataSet);

          if (fromLayers) {
            self.copyLayers(fromLayers);
          } else {
            if (self.layers[4]) {
              self.layers[4].colorize = 1;
              self.layers[4].hue = self.getHueFromPaletteIndex(0);
              // self.layers[4].opacity = 0.0;
              self.layers[4].shimX = 0; //was 30; will need to read this from the spec
              self.layers[4].shimY = 0; //was -50
              self.layers[4].lowThreshold = 5;
            }

            if (self.layers[2]) {
              self.layers[2].colorize = 1;
              self.layers[2].hue = self.getHueFromPaletteIndex(8);
              // self.layers[2].opacity = 0.0;
            }

            if (self.layers[3]) {
              self.layers[3].colorize = 1;
              self.layers[3].hue = self.getHueFromPaletteIndex(4);
              // self.layers[3].opacity = 0.0;
            }

            var i, layer;
            var shownCount = 0;
            for (i = self.layers.length - 1; i >= 0; i--) {
              layer = self.layers[i];
              if (layer.shown) {
                if (shownCount >= 5) {
                  /*By default only show the first 4 layers...?*/
                  layer.shown = false;
                } else {
                  shownCount++;
                }
              }
            }
          }

          self.startCombined();
        },
        function (error) {
          alert(error);
        }
      );
    },

    // ----------
    startCombined: function () {
      var self = this;

      if (this.viewer) {
        this.viewer.destroy();
      }

      this.$stats = $('.stats');

      this.viewer = new DSA.OverlaidViewer({
        container: document.querySelector('.viewer-container'),
        state: {
          layers: this.layers,
        },
        options: {
          prefixUrl: '/lib/openseadragon/images/',
          maxZoomPixelRatio: 10,
          crossOriginPolicy: true,
        },
        onOpen: function () {
          self.addSliders();
          self.addGrid();
          self.addSVG();
          self.updateShims(true);
        },
        onZoom: function () {
          self.updateExtraViewerZoomPan();
          self.updateStats();
        },
        onPan: function () {
          self.updateExtraViewerZoomPan();
        },
      });
    },
    updateStats: function () {
      var stats = '';
      var zoom = this.viewer.getZoom();

      //	var imagePos = this.viewer.getOsdViewer().viewport.viewerElementToViewportCoordinates();
      //	console.log(imagePos);
	//      console.log(this.mouse);

      stats += 'Zoom: ' + zoom;
      if (this.mouse) {
        stats += ', Mouse: ' + Math.round(this.mouse.x) + ',' + Math.round(this.mouse.y);
      }

      this.$stats.text(stats);
    },

    // ----------
    addSliders: function (flip) {
      this.closeAllExtraViewers();
      this.$sideNav.empty();
      this.controlSets = [];

      var i;
      for (i = this.layers.length - 1; i >= 0; i--) {
        this.controlSets.push(
          this.addSliderSet({
            container: this.$sideNav,
            layerIndex: i,
          })
        );
      }

      this.updateThumbnails();
    },

    // ----------
    addSliderSet: function (args) {
      // console.log('addsliderset');
      var self = this;
      var layer = this.layers[args.layerIndex];
      var colorPalette;

      var $layer = $('<div>').addClass('layer-controls').appendTo(args.container);

      var $thumbnailArea = $('<div>').addClass('thumbnail-area').appendTo($layer);

      var $thumbnail = $('<div>').addClass('thumbnail').appendTo($thumbnailArea);

      var tileSource = layer.tileSource;
      if (layer.thumbnail) {
        tileSource = {
          type: 'image',
          url: layer.thumbnail,
        };
      }

      var viewer = OpenSeadragon({
        prefixUrl: '/lib/openseadragon/images/',
        element: $thumbnail[0],
        crossOriginPolicy: true,
        tileSources: tileSource,
        mouseNavEnabled: false,
        showNavigationControl: false,
      });

      viewer.addHandler('open', function () {
        var bounds = viewer.world.getItemAt(0).getBounds();
        var width = $thumbnail.width();
        var height = bounds.height * (width / bounds.width);
        $thumbnail.css({
          height: height,
        });
      });

      var $sliderSet = $('<div>').addClass('slider-set').appendTo($layer);

      var title = '';
      if (layer.tileSource.url) {
        title = layer.tileSource.url.replace(/^.*\/(.*)\.jpg$/, '$1');
      }

      if (!title && layer.slideName) {
        title = layer.slideName;
      }

      $('<div>').addClass('title').text(title).appendTo($sliderSet);

      if (args.layerIndex !== self.layers.length - 1) {
        var $moveUp = $('<div>')
          .addClass('move-up')
          .attr({
            title: 'Move layer up',
          })
          .appendTo($sliderSet)
          .on('click', function () {
            // $sliderSet.toggleClass('expanded');
            if (args.layerIndex === self.layers.length - 1) {
              return;
            }

            var layer = self.layers[args.layerIndex];
            self.layers.splice(args.layerIndex, 1);
            self.layers.splice(args.layerIndex + 1, 0, layer);
            self.addSliders();
            self.update();
          });
      }

      var $expander = $('<div>')
        .addClass('expander')
        .attr({
          title: 'Expand/collapse controls',
        })
        .appendTo($sliderSet)
        .on('click', function () {
          $sliderSet.toggleClass('expanded');
          if ($sliderSet.hasClass('expanded')) {
            var controlSet = _.find(self.controlSets, function (controlSet) {
              return controlSet.layerIndex === args.layerIndex;
            });

            if (
              controlSet &&
              controlSet.histogramViewer &&
              controlSet.histogramData &&
              !controlSet.histogramDrawn
            ) {
              controlSet.histogramViewer.draw(controlSet.histogramData);
              controlSet.histogramDrawn = true;
            }
          }
        });

      var $visible = $('<div>')
        .addClass('visible')
        .attr({
          title: 'Show/hide layer',
        })
        .toggleClass('selected', !!layer.shown)
        .appendTo($sliderSet)
        .on('click', function () {
          if (!layer.shown) {
            var shownCount = 0;
            _.each(self.layers, function (layer) {
              if (layer.shown) {
                shownCount++;
              }
            });

            var maxShown = 8;
            if (shownCount >= maxShown) {
              alert('You already have ' + maxShown + ' layers shown; hide one to show another.');
              return;
            }
          }

          layer.shown = !layer.shown;
          $visible.toggleClass('selected', !!layer.shown);
          $sliderSet.toggleClass('not-visible', !layer.shown);
          self.update();
        });

      var $extraViewerButton = $('<div>')
        .addClass('extra-viewer-button')
        .attr({
          title: 'Show/hide extra viewer for this layer',
        })
        .appendTo($sliderSet)
        .on('click', function () {
          self.toggleExtraViewer(args.layerIndex);
        });

      $sliderSet.toggleClass('not-visible', !layer.shown);

      this.addSlider({
        container: $sliderSet,
        label: 'Opacity',
        min: 0,
        max: 1,
        step: 0.01,
        value: this.layers[args.layerIndex].opacity,
        onChange: function (value) {
          self.layers[args.layerIndex].opacity = value;
          self.update();
        },
      });

      var $extras = $('<div>').addClass('extras').appendTo($sliderSet);

      var colorizeSlider = this.addSlider({
        container: $extras,
        label: 'Colorize',
        min: 0,
        max: 1,
        step: 0.01,
        value: this.layers[args.layerIndex].colorize,
        onChange: function (value) {
          self.layers[args.layerIndex].colorize = value;
          self.update();
        },
      });

      var hueSlider = this.addSlider({
        container: $extras,
        label: 'Hue',
        min: 0,
        max: 360,
        step: 1,
        value: this.layers[args.layerIndex].hue,
        onChange: function (value) {
          colorPalette.clearSelection();
          self.layers[args.layerIndex].hue = value;
          self.update();
        },
      });

      this.addSlider({
        container: $extras,
        label: 'Brightness',
        min: -1,
        max: 1,
        step: 0.01,
        value: this.layers[args.layerIndex].brightness,
        onChange: function (value) {
          self.layers[args.layerIndex].brightness = value;
          self.update();
        },
      });

      this.addSlider({
        container: $extras,
        label: 'Contrast',
        min: -1,
        max: 1,
        step: 0.01,
        value: this.layers[args.layerIndex].contrast,
        onChange: function (value) {
          self.layers[args.layerIndex].contrast = value;
          self.update();
        },
      });

      this.addSlider({
        container: $extras,
        label: 'Black Level',
        min: 0,
        max: 255,
        step: 1,
        value: this.layers[args.layerIndex].blackLevel,
        onChange: function (value) {
          self.layers[args.layerIndex].blackLevel = value;
          self.update();
        },
      });

      this.addSlider({
        container: $extras,
        label: 'White Level',
        min: 0,
        max: 255,
        step: 1,
        value: this.layers[args.layerIndex].whiteLevel,
        onChange: function (value) {
          self.layers[args.layerIndex].whiteLevel = value;
          self.update();
        },
      });

      this.addSlider({
        container: $extras,
        label: 'Low Threshold',
        min: 0,
        max: 255,
        step: 1,
        value: this.layers[args.layerIndex].lowThreshold,
        onChange: function (value) {
          self.layers[args.layerIndex].lowThreshold = value;
          self.update();
        },
      });

      this.addSlider({
        container: $extras,
        label: 'High Threshold',
        min: 0,
        max: 255,
        step: 1,
        value: this.layers[args.layerIndex].highThreshold,
        onChange: function (value) {
          self.layers[args.layerIndex].highThreshold = value;
          self.update();
        },
      });

      this.addMenu({
        container: $extras,
        label: 'Erosion',
        labels: ['None', '3x3 Kernel', '5x5 Kernel', '7x7 Kernel', '9x9 Kernel'],
        values: [1, 3, 5, 7, 9],
        value: this.layers[args.layerIndex].erosionKernel,
        onChange: function (value) {
          self.layers[args.layerIndex].erosionKernel = value;
          self.update();
        },
      });

      var shimFactor = 2;
      var pixelWidth = Math.round(this.viewer.getLayerPixelWidth(args.layerIndex) * shimFactor);
      var pixelHeight = Math.round(this.viewer.getLayerPixelWidth(args.layerIndex) * shimFactor);

      var xSlider = this.addSlider({
        container: $extras,
        label: 'Shim X',
        min: -pixelWidth,
        max: pixelWidth,
        step: 1,
        value: this.layers[args.layerIndex].shimX,
        onChange: function (value) {
          self.layers[args.layerIndex].shimX = value;
          self.update();
        },
      });

      var ySlider = this.addSlider({
        container: $extras,
        label: 'Shim Y',
        min: -pixelHeight,
        max: pixelHeight,
        step: 1,
        value: this.layers[args.layerIndex].shimY,
        onChange: function (value) {
          self.layers[args.layerIndex].shimY = value;
          self.update();
        },
      });

      colorPalette = this.addColorPalette({
        container: $extras,
        onClick: function (hue) {
          self.layers[args.layerIndex].colorize = 1;
          colorizeSlider.setValue(1);
          self.layers[args.layerIndex].hue = hue;
          hueSlider.setValue(hue);
          self.update();
        },
      });

      var histogramViewer, histogramData;
      if (this.metadata && this.metadata.meta && this.metadata.meta.frameHist) {
        var frameHist = this.metadata.meta.frameHist;
        if (frameHist && frameHist[args.layerIndex] && frameHist[args.layerIndex][0]) {
          histogramData = frameHist[args.layerIndex][0].hist;
          if (histogramData) {
            var $histogramCanvas = $('<canvas>').addClass('histogram').appendTo($extras);

            histogramViewer = new DSA.HistogramViewer({
              $el: $histogramCanvas,
            });
          }
        }
      }

      return {
        layerIndex: args.layerIndex,
        $extraViewerButton: $extraViewerButton,
        thumbnailViewer: viewer,
        histogramViewer: histogramViewer,
        histogramData: histogramData,
        histogramDrawn: false,
      };
    },

    // ----------
    toggleExtraViewer: function (layerIndex) {
      var extraViewer = _.find(this.extraViewers, function (extraViewer) {
        return extraViewer.layerIndex === layerIndex;
      });

      if (extraViewer) {
        this.closeExtraViewer(layerIndex);
      } else {
        this.openExtraViewer(layerIndex);
      }
    },

    // ----------
    openExtraViewer: function (layerIndex) {
      var self = this;
      var layer = this.layers[layerIndex];
      var container = document.querySelector('.extra-viewers');

      if (this.extraViewers.length >= 3) {
        alert(
          'You can only open three extra viewers at a time; close one to be able to open another.'
        );
        return;
      }

      var $el = $('<div>').addClass('extra-viewer').appendTo(container);

      var config = {
        prefixUrl: '/lib/openseadragon/images/',
        element: $el[0],
        crossOriginPolicy: true,
        tileSources: layer.tileSource,
        showNavigationControl: false,
        mouseNavEnabled: !this.extraViewersFollow,
      };

      var viewer = OpenSeadragon(config);

      var extraViewer = {
        layerIndex: layerIndex,
        viewer: viewer,
        $el: $el,
      };

      this.extraViewers.push(extraViewer);

      this.updateExtraViewerControls();

      viewer.addHandler('open', function () {
        self.updateExtraViewerZoomPan(true);
      });

      _.each(['add-item-failed', 'open-failed', 'tile-load-failed'], function (key) {
        viewer.addHandler(key, function (event) {
          console.error('Extra viewer error:', key, event);
        });
      });
    },

    // ----------
    closeExtraViewer: function (layerIndex) {
      var extraViewer = _.find(this.extraViewers, function (extraViewer) {
        return extraViewer.layerIndex === layerIndex;
      });

      if (extraViewer) {
        extraViewer.viewer.destroy();
        extraViewer.$el.remove();
        this.extraViewers = _.without(this.extraViewers, extraViewer);
        this.updateExtraViewerControls();
      }
    },

    // ----------
    closeAllExtraViewers: function () {
      _.each(this.extraViewers, function (extraViewer) {
        extraViewer.viewer.destroy();
        extraViewer.$el.remove();
      });

      this.extraViewers = [];
      this.updateExtraViewerControls();
    },

    // ----------
    updateExtraViewerControls: function () {
      var self = this;

      _.each(this.controlSets, function (controlSet, i) {
        var extraViewer = _.find(self.extraViewers, function (extraViewer) {
          return extraViewer.layerIndex === controlSet.layerIndex;
        });

        var active = !!extraViewer;
        controlSet.$extraViewerButton.toggleClass('selected', active);
      });
    },

    // ----------
    updateExtraViewerZoomPan: function (immediately) {
      var self = this;
      if (!this.extraViewersFollow) {
        return;
      }

      var zoom = this.viewer.getZoom();
      var pan = this.viewer.getPan();

      _.each(this.extraViewers, function (extraViewer, i) {
        extraViewer.viewer.viewport.zoomTo(zoom, null, immediately);
        extraViewer.viewer.viewport.panTo(pan, immediately);
      });
    },

    // ----------
    addGrid: function () {
      var self = this;

      if (this.canvasOverlay) {
        this.canvasOverlay.destroy();
      }

      if (this.tracker) {
        this.tracker.destroy();
      }

      this.gridSize = 100;
      this.osdViewer = this.viewer.getOsdViewer();
      var oldZoom = this.osdViewer.viewport.getZoom(true);

      this.canvasOverlay = new DSA.CanvasOverlay({
        osdViewer: this.osdViewer,
        onUpdate: function (context) {
          if (self.showGrid !== self.gridShown) {
            var canvas = context.canvas;
            if (self.showGrid) {
              context.strokeStyle = 'black';
              // context.lineWidth = 0.1;
              // context.globalAlpha = 0.5;
              var gridColumnCount = Math.ceil(canvas.width / self.gridSize);
              var gridRowCount = Math.ceil(canvas.height / self.gridSize);
              var x, y;
              for (y = 0; y < gridRowCount; y++) {
                for (x = 0; x < gridColumnCount; x++) {
                  context.strokeRect(
                    x * self.gridSize + 1,
                    y * self.gridSize + 1,
                    self.gridSize,
                    self.gridSize
                  );
                }
              }
            } else {
              context.clearRect(0, 0, canvas.width, canvas.height);
            }

            self.gridShown = self.showGrid;
          }

          var zoom = self.osdViewer.viewport.getZoom(true);
          if (zoom !== oldZoom) {
            self.throttledUpdateGridValue();
            oldZoom = zoom;
          }
        },
      });

      this.tracker = new OpenSeadragon.MouseTracker({
        element: this.osdViewer.element,
        moveHandler: function (event) {
          self.mouse = event.position;
          self.updateStats();
          self.throttledUpdateGridValue();
        },
      });
    },

    // ----------
    updateGridValue: function () {
      // console.log(this.gridShown, this.canvasOverlay, this.mouse);
      if (!this.gridShown || !this.canvasOverlay || !this.mouse) {
        return;
      }

      var overlayCanvas = this.canvasOverlay.getCanvas();
      var canvas = this.osdViewer.drawer.canvas;
      var context = this.osdViewer.drawer.context;
      var scale = canvas.width / overlayCanvas.width;
      var column = Math.floor(this.mouse.x / this.gridSize);
      var row = Math.floor(this.mouse.y / this.gridSize);
      var imageData = context.getImageData(0, 0, canvas.width, canvas.height);

      // Cell info
      var x, y, i, r, g, b, a, value;
      var histogram = new Uint32Array(256);
      var min = 255;
      var max = 0;
      var total = 0;
      var count = 0;
      var startX = this.gridSize * column * scale;
      var startY = this.gridSize * row * scale;
      var endX = startX + this.gridSize * scale;
      var endY = startY + this.gridSize * scale;
      for (y = startY; y < endY; y++) {
        for (x = startX; x < endX; x++) {
          i = (y * imageData.width + x) * 4;
          if (i >= imageData.data.length) {
            continue;
          }

          r = imageData.data[i];
          g = imageData.data[i + 1];
          b = imageData.data[i + 2];
          a = imageData.data[i + 3];
          if (a < 128) {
            continue;
          }

          // imageData.data[i] = 255 - r;
          // imageData.data[i + 1] = 255 - g;
          // imageData.data[i + 2] = 255 - b;

          value = (r + g + b) / 3;
          total += value;
          count++;
          min = Math.min(min, value);
          max = Math.max(max, value);

          histogram[Math.round(value)]++;
        }
      }

      this.histogramViewer.draw(histogram);

      var average = total / count;

      // Pixel info
      i =
        (Math.floor(this.mouse.y) * scale * imageData.width + Math.floor(this.mouse.x) * scale) * 4;

      r = imageData.data[i];
      g = imageData.data[i + 1];
      b = imageData.data[i + 2];
      a = imageData.data[i + 3];

      this.$pixelColor.css({
        background: 'rgba(' + r + ', ' + g + ', ' + b + ', ' + a / 255 + ')',
      });

      // Put it all together
      var format = function (value) {
        value /= 255;
        return Math.round(value * 1000) / 1000;
      };

      var text = '';
      if (!_.isNaN(average)) {
        text =
          'Cell: ' +
          column +
          ',' +
          row +
          ' Min: ' +
          format(min) +
          ' Mean: ' +
          format(average) +
          ' Max: ' +
          format(max) +
          ' -- Pixel(RGBA): ' +
          r +
          ', ' +
          g +
          ', ' +
          b +
          ', ' +
          a;
      }

      this.$info.text(text);
      // console.log(text);
      // console.log(scale, total, average, count);
      // context.putImageData(imageData, 0, 0);
    },

    // ----------
    addSVG: function () {
      var svgOverlay = this.viewer.svgOverlay();
      var rootNode = d3.select(svgOverlay.node());

      function handleMouseOver(d, i, nodes) {
        var node = nodes[i];
        d3.select(node).style('fill', 'orange');
      }

      function handleMouseOut(d, i, nodes) {
        var node = nodes[i];
        d3.select(node).style('fill', 'none');
      }

      rootNode
        .append('circle')
        .attr('cx', 0.5)
        .attr('cy', 0.5)
        .attr('r', 0.2)
        .style('fill', 'none')
        .style('stroke', 'green')
        .style('stroke-width', 0.005);

      rootNode
        .append('rect')
        .attr('x', 0.3)
        .attr('y', 0.5)
        .attr('width', 0.1)
        .attr('height', 0.1)
        .style('fill', 'none')
        .style('stroke', 'purple')
        .style('stroke-width', 0.005)
        .style('pointer-events', 'all')
        .on('mouseover', handleMouseOver)
        .on('mouseout', handleMouseOut);
    },

    // ----------
    update: function () {
      var self = this;
      this.viewer.setState({
        layers: this.layers,
      });

      this.updateShims();
      this.updateThumbnails();
    },

    // ----------
    updateShims: function (immediately) {
      var self = this;
      _.each(this.layers, function (layer, layerIndex) {
        self.viewer.setLayerPixelOffset(layerIndex, layer.shimX, layer.shimY, immediately);
      });
    },

    // ----------
    updateThumbnails: function () {
      var self = this;

      _.each(this.controlSets, function (controlSet) {
        var layer = self.layers[controlSet.layerIndex];
        var processors = DSA.getFilterProcessors(layer);
        controlSet.thumbnailViewer.setFilterOptions({
          loadMode: 'sync',
          filters: [
            {
              processors: processors,
            },
          ],
        });
      });
    },

    // ----------
    export: function () {
      var text = JSON.stringify(
        {
          dataSetKey: this.dataSetKey,
          fileFormatVersion: 1,
          layers: this.layers,
        },
        null,
        2
      );

      var fileName = this.dataSetKey + '-settings.json';
      var blob = new Blob([text], { type: 'application/json;charset=utf-8' });
      saveAs(blob, fileName);
    },

    // ----------
    import: function (file) {
      var self = this;

      var reader = new FileReader();

      reader.onload = function (loadEvent) {
        var text = loadEvent.target.result;
        var data;
        try {
          data = JSON.parse(text);
        } catch (e) {
          console.error(e);
          alert('Unable to read file');
          return;
        }
        // console.log(data);

        if (data.dataSetKey && data.layers) {
          self.loadDataSet(data.dataSetKey, data.layers);
        } else {
          alert('Unknown file format');
        }
      };

      reader.readAsText(file);
    },

    // ----------
    share: function () {
      var self = this;
      var defaultLayer = DSA.makeLayer();

      // Being hidden is more common, so we're treating that as our default.
      defaultLayer.shown = false;

      var keys = [
        'blackLevel',
        'brightness',
        'colorize',
        'contrast',
        'erosionKernel',
        'highThreshold',
        'hue',
        'imgProcess',
        'lowThreshold',
        'opacity',
        'shimX',
        'shimY',
        'shown',
        'whiteLevel',
      ];

      var output = {
        data: this.dataSetKey,
      };

      output.grid = this.showGrid ? 1 : 0;

      output.layers = _.map(this.layers, function (layer) {
        var newLayer = {};
        _.each(keys, function (key) {
          var value = layer[key];

          // Only include values that are not default, to save space in the URL.
          if (value !== defaultLayer[key]) {
            // Convert booleans to 1/0 to save space in the URL
            newLayer[key] = value === true ? 1 : value === false ? 0 : value;
          }
        });

        return newLayer;
      });

      var query = _.map(output, function (v, k) {
        // Remove the quotes to save space and improve readability
        return k + '=' + JSON.stringify(v).replace(/"/g, '');
      }).join('&');

      var url = location.origin + location.pathname + '?' + query;

      DSA.copyToClipboard(url);

      this.$copyAlert.removeClass('hidden');
      setTimeout(function () {
        self.$copyAlert.addClass('hidden');
      }, 5000);
    },

    // ----------
    copyLayers: function (fromLayers) {
      if (fromLayers.length !== this.layers.length) {
        alert('Layer count mismatch');
        return;
      }

      _.each(this.layers, function (layer, i) {
        _.extend(layer, DSA.deepCopy(fromLayers[i]), {
          tileSource: layer.tileSource,
        });
      });
    },
  });

  // ----------
  setTimeout(function () {
    App.init();
    //Loading the UI configurations from the webix histogram
    webix.ui({
      container: 'right-nav',
      type: 'space',
      width: 20,
      rows: [
        { template: 'Right-Top' },
        {
          cols: [
            { template: 'Right-BottomLeft' },
            { template: 'Right-BottomRight' },
            App.webixFunctions.wbxHistChart,
          ],
        },
      ],
    });

    webix.message('Loading WEBIX Functions');
  }, 1);
})();
