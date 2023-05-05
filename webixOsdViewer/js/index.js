'use strict';
(function() {
  // ----------
  window.App = _.extend(window.App || {}, {
    // ----------
    init: function() {
      var $frame = $('iframe');

      $('a').on('click', function(event) {
        event.preventDefault();
        var $target = $(event.target);
        var $parent = $target.parent();

        var link = $target.attr('href');
        $frame.attr('src', link);

        $('.selected').removeClass('selected');
        $parent.addClass('selected');
        window.location.hash = link;
      });

      var hash = window.location.hash.replace(/^#/, '');
      if (hash) {
        var $a = $('a[href="' + hash + '"]');
        $a.click();
      }
    }
  });

  // ----------
  setTimeout(function() {
    App.init();
  }, 1);
})();
