'use strict';
(function() {
  window.DSA = window.DSA || {};
  var xmlns = 'http://www.w3.org/2000/svg';

  // ----------
  DSA.extend = function(base) {
    var i, k, obj;
    for (i = 1; i < arguments.length; i++) {
      obj = arguments[i];
      if (typeof obj === 'object') {
        for (k in obj) {
          base[k] = obj[k];
        }
      }
    }

    return base;
  };

  // ----------
  DSA.extend(DSA, {
    // ----------
    deepCopy: function(value) {
      if (Array.isArray(value)) {
        return value.map(DSA.deepCopy);
      }

      if (typeof value === 'object') {
        var output = {};
        for (var k in value) {
          output[k] = DSA.deepCopy(value[k]);
        }

        return output;
      }

      return value;
    },

    // ----------
    createSVGElement: function(type, parent, attrs) {
      var node = document.createElementNS(xmlns, type);

      if (parent) {
        parent.appendChild(node);
      }

      if (attrs) {
        for (var k in attrs) {
          node.setAttribute(k, attrs[k]);
        }
      }

      return node;
    },

    // ----------
    getUrlParams: function() {
      var urlParams = {};
      var rawParams = location.search.replace(/^\?/, '').split('&');
      var i, parts;
      for (i = 0; i < rawParams.length; i++) {
        parts = rawParams[i].split('=');
        urlParams[parts[0]] = parts[1];
      }

      return urlParams;
    },

    // ----------
    mapLinear: function(x, a1, a2, b1, b2, clamp) {
      var output = b1 + ((x - a1) * (b2 - b1)) / (a2 - a1);
      if (clamp) {
        var min = Math.min(b1, b2);
        var max = Math.max(b1, b2);
        return Math.max(min, Math.min(max, output));
      }

      return output;
    },

    // ----------
    getFilterProcessors: function(layer) {
      var self = this;

      var processors = [];
      if (layer.brightness) {
        var brightness = DSA.mapLinear(layer.brightness, -1, 1, -255, 255, true);
        processors.push(OpenSeadragon.Filters.BRIGHTNESS(brightness));
      }

      if (layer.contrast) {
        var contrast =
          layer.contrast < 0 ?
            DSA.mapLinear(layer.contrast, -1, 0, 0, 1, true) :
            DSA.mapLinear(layer.contrast, 0, 1, 1, 5, true);

        processors.push(OpenSeadragon.Filters.CONTRAST(contrast));
      }

      if (
        layer.blackLevel !== undefined &&
        layer.whiteLevel !== undefined &&
        (layer.blackLevel > 0 || layer.whiteLevel < 255)
      ) {
        var precomputedLevels = [];
        for (var i = 0; i < 256; i++) {
          precomputedLevels[i] = Math.round(
            this.mapLinear(i, layer.blackLevel, layer.whiteLevel, 0, 255, true)
          );
        }

        processors.push(function(context, callback) {
          self.processPixels(context, function(r, g, b, a) {
            r = precomputedLevels[r];
            g = precomputedLevels[g];
            b = precomputedLevels[b];

            return [r, g, b, a];
          });

          callback();
        });
      }

      if (layer.colorize) {
        processors.push(function(context, callback) {
          context.save();
          context.fillStyle = 'hsl(' + layer.hue + ', 100%, 50%)';
          context.globalCompositeOperation = 'color';
          context.globalAlpha = layer.colorize;
          context.fillRect(0, 0, context.canvas.width, context.canvas.height);
          context.restore();
          callback();
        });
      }

      if (
        layer.lowThreshold !== undefined &&
        layer.highThreshold !== undefined &&
        (layer.lowThreshold > 0 || layer.highThreshold < 255)
      ) {
        processors.push(function(context, callback) {
          self.processPixels(context, function(r, g, b, a) {
            var average = (r + g + b) / 3;
            if (average < layer.lowThreshold || average > layer.highThreshold) {
              return [r, g, b, 0];
            }

            return null;
          });

          callback();
        });
      }

      if (layer.erosionKernel > 1) {
        processors.push(
          OpenSeadragon.Filters.MORPHOLOGICAL_OPERATION(layer.erosionKernel, Math.min)
        );
      }

      if (layer.imgProcess > 1) {
        var kernelSize = layer.imgProcess;
        // console.log(kernelSize);
        processors.push(function(context, callback) {
          context.save();
          //            console.log(context);
          context.restore();
          callback();
        });
        //         context.save();
        //   OpenSeadragon.Filters.MO  RPHOLOGICAL_OPERATION(kernelSize, Math.max)
        //         context.restore();
        //       }

        //     );
      }

      return processors;
    },

    // ----------
    processPixels: function(context, iterator) {
      var imgData = context.getImageData(0, 0, context.canvas.width, context.canvas.height);
      var pixels = imgData.data;
      for (var i = 0; i < pixels.length; i += 4) {
        var r = pixels[i];
        var g = pixels[i + 1];
        var b = pixels[i + 2];
        var a = pixels[i + 3];
        var result = iterator(r, g, b, a);
        if (result) {
          pixels[i] = result[0];
          pixels[i + 1] = result[1];
          pixels[i + 2] = result[2];
          pixels[i + 3] = result[3];
        }
      }

      context.putImageData(imgData, 0, 0);
    },

    // ----------
    validateLayer: function(layer, dataSetName) {
      var fields = [
        'tileSource',
        'colorize',
        'hue',
        'brightness',
        'contrast',
        'blackLevel',
        'whiteLevel',
        'erosionKernel',
        'imgProcess',
        'lowThreshold',
        'highThreshold',
        'markers',
        'opacity',
        'shimX',
        'shimY',
        'shown'
      ];

      // Optional fields: x, y, width, height, slideName, rotation

      var ok = true;
      _.each(fields, function(field) {
        if (layer[field] === undefined) {
          console.error('layer field in', dataSetName, 'missing:', field);
          ok = false;
        }
      });

      return ok;
    },

    // ----------
    makeLayer: function(layer) {
      return _.defaults({}, layer, {
        colorize: 0,
        hue: 0,
        brightness: 0,
        contrast: 0,
        blackLevel: 0,
        whiteLevel: 255,
        erosionKernel: 1,
        imgProcess: 1,
        lowThreshold: 0,
        highThreshold: 255,
        markers: [],
        opacity: 1,
        shimX: 0,
        shimY: 0,
        shown: true
      });
    },
    makeFrameLayer: function(frameLayer) {
      var xOffset =  (frameLayer.xOffset) ? frameLayer.xOffset: 0;
      var yOffset =  (frameLayer.yOffset) ? frameLayer.yOffset: 0;
 
      return _.defaults({}, frameLayer, {
        colorize: 0,
        hue: 0,
        brightness: 0,
        contrast: 0,
        blackLevel: 0,
        whiteLevel: 255,
        erosionKernel: 1,
        imgProcess: 1,
        lowThreshold: 0,
        highThreshold: 255,
        markers: [],
        opacity: 0.75,
        shimX: xOffset,
        shimY: yOffset,
        shown: true
      });
    },

    // ----------
    makeLayers: function(layers) {
      return _.map(layers, function(layer) {
        return DSA.makeLayer(layer);
      });
    },

    // ----------
    makeLayersFromTileSources: function(tileSources) {
      return _.map(tileSources, function(tileSource) {
        return DSA.makeLayer({
          tileSource: tileSource
        });
      });
    },

    // ----------
    // From: https://www.w3schools.com/howto/howto_js_copy_clipboard.asp
    copyToClipboard: function(string) {
      var element = document.createElement('input');
      document.body.appendChild(element);
      element.type = 'text';
      element.value = string;
      element.select();
      element.setSelectionRange(0, 99999);
      document.execCommand('copy');
      document.body.removeChild(element);
    }
  });
})();
