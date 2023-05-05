'use strict';
(function() {
  // ----------
  window.App = _.extend(window.App || {}, {
    colorPaletteLength: 12,

    // ----------
    addSlider: function(args) {
      var self = this;
      var container = $(args.container)[0];

      var div = document.createElement('div');
      div.classList.add('input-row');
      container.appendChild(div);

      var sliderLabel = document.createTextNode(' ' + args.label + ': ');
      div.appendChild(sliderLabel);

      var slider = document.createElement('input');
      slider.type = 'range';
      slider.min = args.min || 0;
      slider.max = args.max || 100;
      slider.step = args.step || 1;
      slider.value = args.value || 0;
      div.appendChild(slider);

      var sliderValue = document.createTextNode(' ' + slider.value);
      div.appendChild(sliderValue);

      slider.addEventListener('input', function() {
        args.onChange(parseFloat(slider.value));
        sliderValue.textContent = ' ' + slider.value;
      });

      return {
        getValue: function() {
          return slider.value;
        },
        setValue: function(value) {
          slider.value = value;
          sliderValue.textContent = ' ' + slider.value;
        }
      };
    },

    // ----------
    addMenu: function(args) {
      console.assert(args.container, 'container is required');
      console.assert(args.label, 'label is required');
      console.assert(args.labels, 'labels is required');
      console.assert(args.values, 'values is required');
      console.assert(args.value !== undefined, 'value is required');
      console.assert(args.onChange, 'onChange is required');
      console.assert(
        args.labels.length === args.values.length,
        'labels and values must have the same number of items'
      );

      var $div = $('<div>')
        .text(args.label + ': ')
        .appendTo($(args.container));

      var $menu = $('<select>').appendTo($div);

      _.each(args.values, function(value, i) {
        var label = args.labels[i];
        $('<option>')
          .val(value)
          .text(label)
          .appendTo($menu);
      });

      $menu.val(args.value).on('change', function() {
        args.onChange($menu.val());
      });
    },

    // ----------
    getHueFromPaletteIndex: function(index) {
      return Math.round(DSA.mapLinear(index, 0, this.colorPaletteLength, 0, 360, true));
    },

    // ----------
    addColorPalette: function(args) {
      console.assert(args.container, 'container is required');
      console.assert(args.onClick, 'onClick is required');

      var normalBorder = '1px solid #eee';
      var selectedBorder = '1px solid #000';
      var $boxes = $();

      var $div = $('<div>')
        .css({
          display: 'flex',
          width: '100%',
          height: 20,
          margin: '4px 0'
        })
        .on('click', function(event) {
          $boxes.css({
            border: normalBorder
          });

          var $target = $(event.target);
          $target.css({
            border: selectedBorder
          });

          var hue = parseFloat($target.data('hue'));
          if (!_.isNaN(hue)) {
            args.onClick(hue);
          }
        })
        .appendTo($(args.container));

      var i, hue, color;
      for (i = 0; i < this.colorPaletteLength; i++) {
        hue = this.getHueFromPaletteIndex(i);
        color = 'hsl(' + hue + ', 100%, 50%)';

        $boxes = $boxes.add(
          $('<div>')
            .css({
              background: color,
              'flex-grow': 1,
              border: normalBorder,
              cursor: 'pointer'
            })
            .data('hue', hue)
            .appendTo($div)
        );
      }

      return {
        clearSelection: function() {
          $boxes.css({
            border: normalBorder
          });
        }
      };
    }
  });
})();
