'use strict';
(function() {
  window.DSA = window.DSA || {};

  // ----------
  var component = (window.DSA.HistogramViewer = function(args) {
    this.$canvas = args.$el;
    this.canvas = this.$canvas[0];
    this.width = this.canvas.width = this.$canvas.width();
    this.height = this.canvas.height = this.$canvas.height();
    this.context = this.canvas.getContext('2d');
  });

  // ----------
  component.prototype = {
    // ----------
    draw: function(values) {
      var self = this;
      var min = 0;
      var max = 0;

      this.context.clearRect(0, 0, this.width, this.height);
      this.context.fillStyle = '#000';

      _.each(values, function(value) {
        max = Math.max(value, max);
      });

      _.each(values, function(value, i) {
        var x = i;
        var height = DSA.mapLinear(value, min, max, 0, self.height);

        self.context.fillRect(x, self.height - height, 1, height);
      });
    }
  };
})();
