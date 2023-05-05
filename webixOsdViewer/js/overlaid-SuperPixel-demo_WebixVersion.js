var GlobalViewerObject = {};

(function() {
  // ----------
  window.App = {
    // ----------
    init: function() {
      var self = this;

      this.$stats = $('.stats');

      var tileSize = 128;

      var SuperPixelImage = {
        type: 'image',
        url: '/demoImages/sampleSuperPixelImage.png',
        buildPyramid: true
      };

      var SampleThumbNailImage = {
        type: 'image',
        url: '/demoImages/sampleThumbnail.png',
        buildPyramid: true
      };

      var tileSources = [
        { tileSource: SuperPixelImage, width: 1024 },
        { tileSource: SampleThumbNailImage, width: 1024 }
      ]; //removed duomo example

      console.log(tileSources)
      console.log(this)

      this.layers = _.map(tileSources, function(tileSource) {
        return DSA.makeLayer({
          tileSource: tileSource
        });
      });

      this.viewer = new DSA.OverlaidViewer({
        container: document.querySelector('.viewer-container'),
        prefixUrl: '/lib/openseadragon/images/',
        state: {
          layers: this.layers
        },
        onZoom: function() {
          self.updateStats();
        }
      });
      // console.log(this.viewer);
      var overlay = this.viewer.svgOverlay();

      d3.select(overlay.node()).on('mousemove', function(event) {
        var mouse = d3.mouse(this);
        self.mouse = {
          x: mouse[0],
          y: mouse[1]
        };

        self.updateStats();

        var gridX = Math.floor(mouse[0] / tileSize);
        var gridY = Math.floor(mouse[1] / tileSize);
        var id = self.getGridId(gridX, gridY);

        self.deselectGridSquare(d3.select(overlay.node()).selectAll('.gutmansSquare'));
        self.selectGridSquare(d3.select(overlay.node()).select('#' + id));
      });

      //.attr("points", "1,1 1,28 2,29 3,29 4,30 6,30 7,31")
      //[[1.0, 1.0], [1.0, 28.0], [2.0, 29.0], [3.0, 29.0], [4.0, 30.0], [6.0, 30.0], [7.0, 31.0], [12.0, 31.0], [13.0, 32.0], [15.0, 32.0], [19.0, 28.0], [29.0, 28.0], [29.0, 26.0], [30.0, 25.0], [30.0, 23.0], [31.0, 22.0], [31.0, 13.0], [30.0, 12.0], [30.0, 8.0], [31.0, 7.0], [31.0, 3.0], [30.0, 2.0], [30.0, 1.0]]

      // Create Event Handlers for mouse
      function handleMouseOver(d, i) {
        self.deselectCell(d3.select(overlay.node()).selectAll('.boundaryClass'));
        self.selectCell(d3.select(overlay.node()).select('#' + this.id));
      }

      //IAN PLEASE CLARIFY-- I ASSUME LAYER 1 is below LAYER2--- not intuitive..
      // Ian says: Standardizing the layer order is on my todo list.

      //d3.selectAll("polygon").style('fill', 'orange')
      ///d3.selectAll("polygon").style('opacity', 1)

      //d3.selectAll("polygon").style('stroke-width', '2')
      function addOverlay(tiles) {
        $.each(tiles, function(index, tile) {
          var fillColor = d3.schemeCategory20[index % 20];
          // console.log(index, tile, fillColor);

          var node = d3
            .select(overlay.node())
            .append('polygon')
            .style('fill', fillColor)
            .attr('points', tile.geometry.coordinates.join(' '))
            .attr('class', 'boundaryClass')
            .attr('id', 'boundaryLI' + tile.properties.labelindex)
            .on('mouseover', handleMouseOver);

          self.deselectCell(node);
        });
      }

      addOverlay(sampleSVG);

      ///        addSquareOverlay
      // d3.select(overlay.node()).append("polygon")
      //    .attr("points", "250,250 250,500 500,500 500,250 250,250")
      //         .style('fill', fillColor)
      //         .attr('opacity', 1)
      //         .attr('class', 'gutmansSquare')
      //         .attr('stroke', 'green')
      //         .attr('stroke-width', 1);

      // d3.select(overlay.node()).append("polygon")
      //    .attr("points", "0,0 0,250 250,250 250,0 0,0")
      //         .style('fill', fillColor)
      //         .attr('opacity', 1)
      //         .attr('class', 'gutmansSquare')
      //         .attr('stroke', 'green')
      //         .attr('stroke-width', 1);

      // d3.select(overlay.node()).append("polygon")
      //    .attr("points", "750,750 750,1000 1000,1000 1000,750 750,750")
      //         .style('fill', fillColor)
      //         .attr('opacity', 1)
      //         .attr('class', 'gutmansSquare')
      //         .attr('stroke', 'green')
      //         .attr('stroke-width', 1);

      var tileIndex = 0;
      var imageWidth = 1024;
      var i, j, pointArray, node;

      for (i = 0; i < 1024 / tileSize; i++) {
        for (j = 0; j < 1024 / tileSize; j++) {
          pointArray =
            i * tileSize +
            ',' +
            j * tileSize +
            ' ' +
            i * tileSize +
            ',' +
            (j + 1) * tileSize +
            ' ' +
            (i + 1) * tileSize +
            ',' +
            (j + 1) * tileSize +
            ' ' +
            (i + 1) * tileSize +
            ',' +
            j * tileSize +
            ' ' +
            i * tileSize +
            ',' +
            j * tileSize;

          node = d3
            .select(overlay.node())
            .append('polygon')
            .attr('points', pointArray)
            .attr('class', 'gutmansSquare')
            .attr('id', this.getGridId(i, j))
            .attr('pointer-events', 'none');

          this.deselectGridSquare(node);
        }
      }

      //To Do:  Set the number of images based on the number of tilesources so I don't have to remember to keep this in synxc!
      for (i = 0; i < 2; i++) {
        this.addCheckbox(i);
        this.addSlider(i);
        // this.addShim(i);
      }
    },

    // ----------
    updateStats: function() {
      var stats = '';
      var zoom = this.viewer.getZoom();
      stats += 'Zoom: ' + zoom;
      if (this.mouse) {
        stats += ', Mouse: ' + Math.round(this.mouse.x) + ',' + Math.round(this.mouse.y);
      }

      this.$stats.text(stats);
    },

    // ----------
    getGridId: function(x, y) {
      return 'grid-' + x + '-' + y;
    },

    // ----------
    deselectGridSquare: function(node) {
      node
        .style('fill', 'pink')
        .attr('opacity', 0.2)
        .attr('stroke', 'green')
        .attr('stroke-width', 1);
    },

    // ----------
    selectGridSquare: function(node) {
      node
        .style('fill', 'none')
        .attr('opacity', 0.8)
        .attr('stroke', 'green')
        .attr('stroke-width', 4);
    },

    // ----------
    deselectCell: function(node) {
      node
        .attr('opacity', 0.4)
        .attr('stroke', 'red')
        .attr('stroke-width', 1);
    },

    // ----------
    selectCell: function(node) {
      node
        .attr('opacity', 0.8)
        .attr('stroke', 'red')
        .attr('stroke-width', 3);
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
      checkbox.checked = this.layers[index].shown;
      label.appendChild(checkbox);

      var labelText = document.createTextNode(' Layer ' + (index + 1));
      label.appendChild(labelText);

      label.addEventListener('click', function() {
        self.layers[index].shown = !!checkbox.checked;
        self.update();
      });
    },

    // ----------
    addSlider: function(index) {
      var self = this;
      var layers = document.querySelector('.layers');

      var div = document.createElement('div');
      layers.appendChild(div);

      var sliderText = document.createTextNode(' Opacity: '); //TO DO: Put this in front of the range slider instead of on top
      div.appendChild(sliderText);

      var slider = document.createElement('input');
      slider.type = 'range';
      slider.max = 1;
      slider.step = 0.01;
      slider.value = this.layers[index].opacity;
      div.appendChild(slider);

      slider.addEventListener('input', function() {
        self.layers[index].opacity = slider.value;
        self.update();
      });
    },

    // ----------
    update: function() {
      this.viewer.setState({
        layers: this.layers
      });
    }
  };

  // function createRadioElement( name, checked ) {
  //     var radioInput;
  //     try {
  //         var radioHtml = '<input type="radio" name="' + name + '"';
  //         if ( checked ) {
  //             radioHtml += ' checked="checked"';
  //         }
  //         radioHtml += '/>';
  //         radioInput = document.createElement(radioHtml);
  //     } catch( err ) {
  //         radioInput = document.createElement('input');
  //         radioInput.setAttribute('type', 'radio');
  //         radioInput.setAttribute('name', name);
  //         if ( checked ) {
  //             radioInput.setAttribute('checked', 'checked');
  //         }
  //     }

  //     return radioInput;
  // }

  //Add in a grid radio button
  function addGridRadio() {
    var self = this;
    var layers = document.querySelector('.layers');

    var div = document.createElement('div');
    layers.appendChild(div);

    var gridText = document.createTextNode(' Grid Size: '); //TO DO: Put this in front of the range slider instead of on top
    div.appendChild(gridText);

    var radio = document.createElement('input');
    radio.type = 'radio';
    radio.max = 1;
    radio.options = ['128', '256', '512'];
    div.appendChild(radio);

    radio.addEventListener('radio', function() {
      console.log('radio clicked');
    });
  }

  // <div id="radio_home"></div>

  // var radio_home = document.getElementById("radio_home");

  // function makeRadioButton(name, value, text) {

  //   var label = document.createElement("label");
  //   var radio = document.createElement("input");
  //   radio.type = "radio";
  //   radio.name = name;
  //   radio.value = value;

  //   label.appendChild(radio);

  //   label.appendChild(document.createTextNode(text));
  //   return label;
  // }

  // var yes_button = makeRadioButton("yesbutton", "yes", "Oh yea! do it!");
  // radio_home.appendChild(yes_button);

  addGridRadio();
  // superPixelData = {};
  //  var svgJSONData = webix.ajax().sync().get("demoImages/sampleSuperPixelImage.png.svg.json", function(data)

  //    {
  //      spxData = JSON.parse(data);
  //      // console.log(spxData);
  // //      addOverlay(spxData);
  //    });
  // ----------
  setTimeout(function() {
    App.init();
  }, 1);
})();
