'use strict';
(function() {
  window.DSA = window.DSA || {};

  // ----------
  var component = (window.DSA.OverlaidViewer = function(args) {
    var self = this;
    console.assert(
      args.state.layers && args.state.layers.length > 1,
      'must have at least 2 layers'
    );
    console.assert(args.container, 'container is required');

    this._container = args.container;
    this._layers = [];

    var element = document.createElement('div');
    element.style.left = 0;
    element.style.top = 0;
    element.style.width = '100%';
    element.style.height = '100%';
    this._container.appendChild(element);

    var config = DSA.extend(
      {
        crossOriginPolicy: 'Anonymous'
      },
      args.options,
      {
        element: element,
        tileSources: _.map(args.state.layers, function(layer) {
          return {
            tileSource: layer.tileSource,
            x: layer.x,
            y: layer.y,
            width: layer.width,
            height: layer.height
          };
        })
      }
    );

    if (args.prefixUrl) {
      config.prefixUrl = args.prefixUrl;
    }

    this._viewer = OpenSeadragon(config);

    // We have to do this here, because OSD defaults it to relative
    element.style.position = 'absolute';

    this._overlay = this._viewer.svgOverlay();

    this._viewer.addHandler('open', function() {
      var count = self._viewer.world.getItemCount();
      var layer;
      for (var i = 0; i < count; i++) {
        layer = {
          tiledImage: self._viewer.world.getItemAt(i),
          tileSource: args.state.layers[i].tileSource,
          offset: {
            x: 0,
            y: 0
          }
        };

        self._layers.push(layer);
      }

      self._updateRotation();
      self._updateFilters();
      self._updateOpacities();

      if (args.onOpen) {
        args.onOpen();
      }
    });

    if (args.onZoom) {
      this._viewer.addHandler('zoom', args.onZoom);
    }

    if (args.onPan) {
      this._viewer.addHandler('pan', args.onPan);
    }

    this.setState(args.state);
  });

  // ----------
  component.prototype = {
    // ----------
    destroy: function() {
      this._viewer.element.remove();
      this._viewer.destroy();
    },

    // ----------
    getOsdViewer: function() {
      return this._viewer;
    },

    // ----------
    svgOverlay: function() {
      return this._overlay;
    },

    // ----------
    getLayerPixelWidth: function(index) {
      var layer = this._layers[index];
      console.assert(
        layer,
        '[DSA.OverlaidViewer.getLayerPixelWidth] layer index must be valid',
        index
      );
      return layer.tiledImage.source.width;
    },

    // ----------
    getLayerPixelHeight: function(index) {
      var layer = this._layers[index];
      console.assert(
        layer,
        '[DSA.OverlaidViewer.getLayerPixelHeight] layer index must be valid',
        index
      );
      return layer.tiledImage.source.height;
    },

    // ----------
    getLayerPixelOffset: function(index) {
      var layer = this._layers[index];
      console.assert(
        layer,
        '[DSA.OverlaidViewer.getLayerPixelOffset] layer index must be valid',
        index
      );
      return {
        x: layer.offset.x,
        y: layer.offset.y
      };
    },

    // ----------
    setLayerPixelOffset: function(index, x, y, immediately) {
      var layer = this._layers[index];
      console.assert(
        layer,
        '[DSA.OverlaidViewer.setLayerPixelOffset] layer index must be valid',
        index
      );
      var bounds = layer.tiledImage.getBounds();
      var pixelSize = bounds.width / layer.tiledImage.source.width;
      layer.tiledImage.setPosition(
        new OpenSeadragon.Point(x * pixelSize, y * pixelSize),
        immediately
      );
      layer.offset.x = x;
      layer.offset.y = y;
    },

    // ----------
    getZoom: function(current) {
      return this._viewer.viewport.getZoom(current);
    },

    // ----------
    getPan: function(current) {
      return this._viewer.viewport.getCenter(current);
    },

    // ----------
    setState: function(state) {
      var self = this;
      var needsFilterUpdate = false;
      var needsRotationUpdate = false;
      var needsOpacityUpdate = false;
      var needsOrderUpdate = false;

      _.each(state.layers, function(layer, layerIndex) {
        var oldLayer = self._state && self._state.layers && self._state.layers[layerIndex];

        if (
          !oldLayer ||
          oldLayer.colorize !== layer.colorize ||
          oldLayer.hue !== layer.hue ||
          oldLayer.brightness !== layer.brightness ||
          oldLayer.contrast !== layer.contrast ||
          oldLayer.erosionKernel !== layer.erosionKernel ||
          oldLayer.lowThreshold !== layer.lowThreshold ||
          oldLayer.highThreshold !== layer.highThreshold ||
          oldLayer.blackLevel !== layer.blackLevel ||
          oldLayer.whiteLevel !== layer.whiteLevel
        ) {
          needsFilterUpdate = true;
        }

        if (!oldLayer || oldLayer.rotation !== layer.rotation) {
          needsRotationUpdate = true;
        }

        if (!oldLayer || oldLayer.opacity !== layer.opacity || oldLayer.shown !== layer.shown) {
          needsOpacityUpdate = true;
        }

        if (oldLayer && oldLayer.tileSource !== layer.tileSource) {
          needsOrderUpdate = true;
        }
      });

      this._state = DSA.deepCopy(state);

      if (needsOrderUpdate) {
        this._updateOrder();
      }

      if (needsRotationUpdate) {
        this._updateRotation();
      }

      if (needsFilterUpdate) {
        this._updateFilters();
      }

      if (needsOpacityUpdate) {
        this._updateOpacities();
      }
    },

    // ----------
    _updateOrder: function() {
      var self = this;

      _.each(this._state.layers, function(stateLayer, i) {
        var layerIndex = _.findIndex(self._layers, function(layer) {
          return _.isEqual(layer.tileSource, stateLayer.tileSource);
        });

        if (layerIndex === -1) {
          console.error('unknown tilesource', stateLayer.tileSource, self._layers);
        } else {
          var layer = self._layers[layerIndex];
          self._layers.splice(layerIndex, 1);
          self._layers.splice(i, 0, layer);

          var tiledImage = self._viewer.world.getItemAt(layerIndex);
          self._viewer.world.setItemIndex(tiledImage, i);
        }
      });
    },

    // ----------
    _updateFilters: function() {
      var self = this;
      var filters = this._state.layers.map(function(stateLayer, layerIndex) {
        var layer = self._layers[layerIndex];
        if (!layer) {
          // console.log('Not loaded.', layerIndex);
          return null;
        }

        return {
          items: layer.tiledImage,
          processors: DSA.getFilterProcessors(stateLayer)
        };
      });

      filters = _.filter(filters, function(filter) {
        return !!filter;
      });

      this._viewer.setFilterOptions({
        loadMode: 'sync',
        filters: filters
      });
    },

    // ----------
    _updateRotation: function() {
      var self = this;
      this._state.layers.forEach(function(stateLayer, layerIndex) {
        var layer = self._layers[layerIndex];
        if (!layer) {
          // console.log('Not loaded.', layerIndex);
          return;
        }

        layer.tiledImage.setRotation(stateLayer.rotation || 0, true);
      });
    },

    // ----------
    _updateOpacities: function() {
      var self = this;
      this._state.layers.forEach(function(stateLayer, layerIndex) {
        var layer = self._layers[layerIndex];
        if (!layer) {
          // console.log('Not loaded.', layerIndex);
          return;
        }

        layer.tiledImage.setOpacity(stateLayer.shown ? stateLayer.opacity : 0);
      });
    }
  };
})();
