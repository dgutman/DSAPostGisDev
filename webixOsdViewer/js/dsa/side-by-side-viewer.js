'use strict';
(function () {
  window.DSA = window.DSA || {};

  // ----------
  var component = (window.DSA.SideBySideViewer = function (args) {
    var self = this;
    console.assert(
      args.state && args.state.layers && args.state.layers.length === 2,
      'must have 2 layers'
    );
    console.assert(args.container, 'container is required');

    this._container = args.container;
    this._osdViews = [];
    this._clickMode = 'none';
    this._syncMode = false;
    this._offset = new OpenSeadragon.Point(0, 0);

    this._props = {
      onAddMarker: args.onAddMarker,
      onRemoveMarker: args.onRemoveMarker
    };

    var config = DSA.extend({}, args.options);
    if (args.prefixUrl) {
      config.prefixUrl = args.prefixUrl;
    }

    var openPromise0 = new Promise(function (resolve, reject) {
      self._osdViews.push(
        self._createOsdView({
          index: 0,
          tileSource: args.state.layers[0].tileSource,
          options: config,
          onOpen: resolve
        })
      );
    });

    var openPromise1 = new Promise(function (resolve, reject) {
      self._osdViews.push(
        self._createOsdView({
          index: 1,
          tileSource: args.state.layers[1].tileSource,
          options: config,
          onOpen: resolve
        })
      );
    });

    Promise.all([openPromise0, openPromise1]).then(function () {
      if (args.onOpen) {
        args.onOpen();
      }
    });

    this.setState(args.state);
  });

  // ----------
  component.prototype = {
    // ----------
    destroy: function () {
      this._osdViews.forEach(function (osdView) {
        osdView.viewer.element.remove();
        osdView.viewer.destroy();
      });
    },

    // ----------
    setClickMode: function (value) {
      this._clickMode = value;
    },

    // ----------
    setSyncMode: function (flag) {
      this._syncMode = flag;
      this._updateSync();
    },

    // ----------
    setState: function (state) {
      var self = this;
      var needsSyncUpdate = false;
      var needsFilterUpdate = false;
      var needsRotationUpdate = false;

      _.each(state.layers, function (layer, layerIndex) {
        var osdView = self._osdViews[layerIndex];
        console.assert(osdView, 'Must have valid index', layerIndex);
        var oldLayer = self._state && self._state.layers && self._state.layers[layerIndex];

        if (!oldLayer || !_.isEqual(oldLayer.markers, layer.markers)) {
          needsSyncUpdate = true;
          var svgNode = osdView.overlay.node();

          _.each(osdView.markers, function (marker) {
            marker.group.remove();
          });

          osdView.markers = _.map(layer.markers, function (marker, markerIndex) {
            var pos = marker;
            var size = 30;
            var halfSize = size * 0.5;

            var group = DSA.createSVGElement('g', svgNode);

            var line = DSA.createSVGElement('line', group, {
              x1: pos.x - halfSize,
              x2: pos.x + halfSize,
              y1: pos.y,
              y2: pos.y,
              stroke: 'red',
              'stroke-width': 2
            });

            line = DSA.createSVGElement('line', group, {
              x1: pos.x,
              x2: pos.x,
              y1: pos.y - halfSize,
              y2: pos.y + halfSize,
              stroke: 'red',
              'stroke-width': 2
            });

            var text = DSA.createSVGElement('text', group, {
              x: pos.x + halfSize * 0.5,
              y: pos.y - halfSize * 0.5,
              fill: 'red',
              'font-size': halfSize
            });

            text.innerHTML = markerIndex + 1;

            var output = {
              group: group,
              pos: pos
            };

            return output;
          });
        }

        if (
          !oldLayer ||
          oldLayer.colorize !== layer.colorize ||
          oldLayer.hue !== layer.hue ||
          oldLayer.brightness !== layer.brightness ||
          oldLayer.contrast !== layer.contrast ||
          oldLayer.erosionKernel !== layer.erosionKernel
        ) {
          needsFilterUpdate = true;
        }

        if (!oldLayer || oldLayer.rotation !== layer.rotation) {
          needsRotationUpdate = true;
        }
      });

      this._state = DSA.deepCopy(state);

      if (needsSyncUpdate) {
        this._updateSync();
      }

      if (needsRotationUpdate) {
        this._updateRotation();
      }

      if (needsFilterUpdate) {
        this._updateFilters();
      }
    },

    // ----------
    getLayerPixelWidth: function (index) {
      var osdView = this._osdViews[index];
      console.assert(
        osdView,
        '[DSA.SideBySideViewer.getLayerPixelWidth] layer index must be valid',
        index
      );
      return osdView.viewer.world.getItemAt(0).source.width;
    },

    // ----------
    setLayerPixelOffset: function (index, x, y, immediately) {
      var osdView = this._osdViews[index];
      console.assert(
        osdView,
        '[DSA.SideBySideViewer.setLayerPixelOffset] layer index must be valid',
        index
      );

      var tiledImage = osdView.viewer.world.getItemAt(0);

      var bounds = tiledImage.getBounds();
      var pixelSize = bounds.width / tiledImage.source.width;
      tiledImage.setPosition(new OpenSeadragon.Point(x * pixelSize, y * pixelSize), immediately);
    },

    // ----------
    _updateFilters: function () {
      var self = this;

      var filters = this._state.layers.map(function (layer, layerIndex) {
        var osdView = self._osdViews[layerIndex];
        console.assert(osdView, 'Must have valid index', layerIndex);

        osdView.viewer.setFilterOptions({
          loadMode: 'sync',
          filters: {
            processors: DSA.getFilterProcessors(layer)
          }
        });
      });
    },

    // ----------
    _updateRotation: function () {
      var self = this;
      var filters = this._state.layers.map(function (layer, layerIndex) {
        var osdView = self._osdViews[layerIndex];
        console.assert(osdView, 'Must have valid index', layerIndex);

        var tiledImage = osdView.viewer.world.getItemAt(0);
        if (!tiledImage) {
          // console.log('Not loaded.', layerIndex);
          return;
        }

        tiledImage.setRotation(layer.rotation, true);
      });
    },

    // ----------
    _createOsdView: function (args) {
      var self = this;

      var element = document.createElement('div');
      element.style.height = '50%';
      this._container.appendChild(element);

      var config = DSA.extend(
        {
          crossOriginPolicy: 'Anonymous'
        },
        args.options,
        {
          element: element,
          tileSources: {
            tileSource: args.tileSource,
            width: 1000
          }
        }
      );

      var viewer = OpenSeadragon(config);

      var overlay = viewer.svgOverlay();

      var osdView = {
        viewer: viewer,
        overlay: overlay,
        index: args.index,
        markers: []
      };

      viewer.addHandler('open', function () {
        self._updateRotation();

        if (args.onOpen) {
          args.onOpen();
        }
      });

      viewer.addHandler('canvas-click', function (event) {
        if (!event.quick) {
          return;
        }

        var pos = viewer.viewport.pointFromPixel(event.position);
        self._handleClick(osdView, pos);

        event.preventDefaultAction = true;
      });

      viewer.addHandler('zoom', function () {
        self._sync(osdView);
      });

      viewer.addHandler('pan', function () {
        self._sync(osdView);
      });

      return osdView;
    },

    // ----------
    _handleClick: function (osdView, pos) {
      if (this._clickMode === 'add') {
        this._props.onAddMarker(osdView.index, pos);
      } else if (this._clickMode === 'remove') {
        var best;
        osdView.markers.forEach(function (marker, i) {
          var distance = Math.abs(pos.x - marker.pos.x) + Math.abs(pos.y - marker.pos.y);
          if (!best || best.distance > distance) {
            best = {
              marker: marker,
              distance: distance,
              index: i
            };
          }
        });

        if (best && best.distance < 30) {
          this._props.onRemoveMarker(osdView.index, best.index);
        }
      }
    },

    // ----------
    _updateSync: function () {
      var self = this;

      if (!this._syncMode) {
        return;
      }

      this._synchronizing = true;

      this._offset.x = 0;
      this._offset.y = 0;

      var osdView0 = this._osdViews[0];
      var osdView1 = this._osdViews[1];
      var count = Math.min(osdView0.markers.length, osdView1.markers.length);

      if (count) {
        var offsets = [];
        var i, marker0, marker1;
        for (i = 0; i < count; i++) {
          marker0 = osdView0.markers[i];
          marker1 = osdView1.markers[i];
          offsets.push(
            new OpenSeadragon.Point(marker0.pos.x - marker1.pos.x, marker0.pos.y - marker1.pos.y)
          );
        }

        offsets.forEach(function (offset) {
          self._offset.x += offset.x;
          self._offset.y += offset.y;
        });

        this._offset.x /= count;
        this._offset.y /= count;
      }

      var p1 = osdView0.viewer.viewport.getCenter();
      var p2 = osdView1.viewer.viewport.getCenter();
      var c = new OpenSeadragon.Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2);

      this._osdViews.forEach(function (osdView, i) {
        var c2 = c.clone();
        if (i === 0) {
          c2.x += self._offset.x / 2;
          c2.y += self._offset.y / 2;
        } else {
          c2.x -= self._offset.x / 2;
          c2.y -= self._offset.y / 2;
        }

        osdView.viewer.viewport.panTo(c2);
      });

      this._synchronizing = false;
    },

    // ----------
    _sync: function (fromOsdView) {
      var self = this;

      if (!this._syncMode || this._synchronizing) {
        return;
      }

      this._synchronizing = true;

      var pan = fromOsdView.viewer.viewport.getCenter();
      var zoom = fromOsdView.viewer.viewport.getZoom();

      this._osdViews.forEach(function (osdView, i) {
        if (osdView === fromOsdView) {
          return;
        }

        var pan2 = pan.clone();
        if (i === 0) {
          pan2.x += self._offset.x;
          pan2.y += self._offset.y;
        } else {
          pan2.x -= self._offset.x;
          pan2.y -= self._offset.y;
        }

        osdView.viewer.viewport.zoomTo(zoom);
        osdView.viewer.viewport.panTo(pan2);
      });

      this._synchronizing = false;
    }
  };
})();
