'use strict';
(function() {
  window.DSA = window.DSA || {};

  // ----------
  var component = (window.DSA.CanvasOverlay = function(args) {
    var self = this;
    console.assert(args.osdViewer, 'must have osdViewer');

    this.viewer = args.osdViewer;

    this._containerWidth = 0;
    this._containerHeight = 0;
    this._sizeFactor = args.sizeFactor === undefined ? 1 : args.sizeFactor;

    this._canvasdiv = document.createElement('div');
    this._canvasdiv.style.position = 'absolute';
    this._canvasdiv.style.left = 0;
    this._canvasdiv.style.top = 0;
    this._canvasdiv.style.width = '100%';
    this._canvasdiv.style.height = '100%';
    this._canvasdiv.style.pointerEvents = 'none';
    this.viewer.canvas.appendChild(this._canvasdiv);

    this._canvas = document.createElement('canvas');
    this._canvas.style.position = 'absolute';
    this._canvas.style.left = 0;
    this._canvas.style.top = 0;
    this._canvas.style.width = '100%';
    this._canvas.style.height = '100%';
    this._canvas.style.opacity = args.opacity === undefined ? 1 : args.opacity;

    this._canvasdiv.appendChild(this._canvas);
    this._context = this._canvas.getContext('2d');

    this.resize();

    this.boundResize = function() {
      self.resize();
    };

    window.addEventListener('resize', this.boundResize);

    if (args.onUpdate) {
      this.viewer.addHandler('update-viewport', function() {
        args.onUpdate(self._context);
      });
    }
  });

  // ----------
  component.prototype = {
    // ----------
    destroy: function() {
      window.removeEventListener('resize', this.boundResize);
    },

    // ----------
    setOpacity: function(value) {
      this._canvas.style.opacity = value;
    },

    // ----------
    getCanvas: function() {
      return this._canvas;
    },

    // ----------
    resize: function() {
      var w = Math.round(this.viewer.container.clientWidth * this._sizeFactor);
      var h = Math.round(this.viewer.container.clientHeight * this._sizeFactor);

      if (this._containerWidth !== w) {
        this._containerWidth = w;
        this._canvasdiv.setAttribute('width', this._containerWidth);
        this._canvas.setAttribute('width', this._containerWidth);
      }

      if (this._containerHeight !== h) {
        this._containerHeight = h;
        this._canvasdiv.setAttribute('height', this._containerHeight);
        this._canvas.setAttribute('height', this._containerHeight);
      }
    }
  };
})();
