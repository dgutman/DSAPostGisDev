'use strict';

(function() {
  function dsaTileSource(baseURL, itemId, callback) {
    //this formats an item ID from a GIRDER based DSA instance into an OSD friendly
    //tilesource
    //need to get the tiles.sizeX from the thumbnail url
    //how do I pass the itemId to the chained function...
    $.ajax(baseURL + '/item/' + itemId + '/tiles').done(function(tiles) {
      // console.log(tiles);

      var tileSource = {
        width: tiles.sizeX,
        height: tiles.sizeY,
        tileWidth: tiles.tileWidth,
        tileHeight: tiles.tileHeight,
        minLevel: 0,
        maxLevel: tiles.levels - 1,
        getTileUrl: function(level, x, y) {
          return (
            baseURL + '/item/' + itemId + '/tiles/zxy/' + level + '/' + x + '/' + y + '?edge=crop'
          );
        }
      };
      console.log('Trying to create tile source for ');
      console.log(tileSource);
      callback(tileSource);
    });
  }

  var config = {};
  config.BASE_URL = 'http://dermannotator.org:8080/api/v1';

  var theDuomo = {
    Image: {
      xmlns: 'http://schemas.microsoft.com/deepzoom/2008',
      Url: 'http://openseadragon.github.io/example-images/duomo/duomo.dzi',
      Format: 'jpg',
      Overlap: '2',
      TileSize: '256',
      Size: {
        Width: '13920',
        Height: '10200'
      }
    }
  };

  window.App = window.App || {};

  App.demoTileSources = {
    duomo: {
      Image: {
        xmlns: 'http://schemas.microsoft.com/deepzoom/2008',
        Url: 'http://openseadragon.github.io/example-images/duomo/duomo_files/',
        Format: 'jpg',
        Overlap: '2',
        TileSize: '256',
        Size: {
          Width: '13920',
          Height: '10200'
        }
      }
    },
    highsmith: {
      Image: {
        xmlns: 'http://schemas.microsoft.com/deepzoom/2008',
        Url: 'http://openseadragon.github.io/example-images/highsmith/highsmith_files/',
        Format: 'jpg',
        Overlap: '2',
        TileSize: '256',
        Size: {
          Width: '7026',
          Height: '9221'
        }
      }
    },
    superPixel: {
      type: 'image',
      url: 'demoImages/sampleSuperPixelImage.png',
      buildPyramid: true
    },

    sampleThumbnail: {
      type: 'image',
      url: 'demoImages/sampleThumbnail.png',
      buildPyramid: true
    },

    exampleSet1: [],
    exampleSet2: [theDuomo, theDuomo, theDuomo, theDuomo, theDuomo],
    ThriveExampleSet: [
      {
        type: 'image',
        url: 'demoImages/CellSeg.png',
        buildPyramid: true
      },
      {
        type: 'image',
        url: 'demoImages/NaKATPase_AFRemoved_004.png',
        buildPyramid: true
      },
      {
        type: 'image',
        url: 'demoImages/pERK_CD31_AGA_260_3_S001_P004_dapi.png',
        buildPyramid: true
      }
    ],
    AD_ImageStack: [],
    tcgaSPXExample: {
      maxLevel: 9,
      minLevel: 0,
      slideName: 'TCGA-3L-AA1B-01Z-00-DX2',
      magnification: 40.0,
      mm_x: 0.000252699,
      mm_y: 0.000252699,
      width: 87647,
      height: 52434,
      tileHeight: 240,
      tileWidth: 240,
      getTileUrl: function(level, x, y) {
        return (
          'http://candygram.neurology.emory.edu:8080/#item/597de1bd92ca9a000de4bacd/tiles/zxy/' +
          level +
          '/' +
          x +
          '/' +
          y +
          '?edge=crop'
        );
      }
    }
  };

  var i, number, url;
  for (i = 0; i < 66; i++) {
    url = 'zStackExamples/exampleSet1/v00000';
    number = '' + i;
    if (number.length === 1) {
      url += '0';
    }

    url += number + '.jpg';
    App.demoTileSources.exampleSet1.push({
      type: 'image',
      url: url
    });
  }

  DSA.dataSetManager.register(
    'exampleSet1With2',
    DSA.makeLayersFromTileSources(App.demoTileSources.exampleSet1.slice(0, 2))
  );

  DSA.dataSetManager.register(
    'exampleSet1With5',
    DSA.makeLayersFromTileSources(App.demoTileSources.exampleSet1.slice(0, 5))
  );

  DSA.dataSetManager.register(
    'exampleSet1',
    DSA.makeLayersFromTileSources(App.demoTileSources.exampleSet1)
  );




  // ----------
  DSA.dataSetManager.register('dermPathImageSet', function(callback) {
    dsaTileSource(config.BASE_URL, '5bb7abc5e62914001b06be44', function(tileSource) {
      callback(
        DSA.makeLayersFromTileSources([
          tileSource,
          {
            width: 87296,
            height: 75520,
            tileWidth: 256,
            tileHeight: 256,
            minLevel: 0,
            maxLevel: 9,
            getTileUrl: function(level, x, y) {
              return (
                'http://dermannotator.org:8080/api/v1/item/5bb7abb5e62914001b06be41/tiles/zxy/' +
                level +
                '/' +
                x +
                '/' +
                y +
                '?edge=crop'
              );
            }
          },
          {
            width: 87296,
            height: 75520,
            tileWidth: 256,
            tileHeight: 256,
            minLevel: 0,
            maxLevel: 9,
            getTileUrl: function(level, x, y) {
              return (
                'http://dermannotator.org:8080/api/v1/item/5bb7abc5e62914001b06be44/tiles/zxy/' +
                level +
                '/' +
                x +
                '/' +
                y +
                '?edge=crop'
              );
            }
          },
          {
            width: 87296,
            height: 75520,
            tileWidth: 256,
            tileHeight: 256,
            minLevel: 0,
            maxLevel: 9,
            getTileUrl: function(level, x, y) {
              return (
                'http://dermannotator.org:8080/api/v1/item/5bb7abc5e62914001b06be44/tiles/zxy/' +
                level +
                '/' +
                x +
                '/' +
                y +
                '?edge=crop'
              );
            }
          }
        ])
      );
    });
  });
console.log(config);


DSA.dataSetManager.register(
  'dermviva',
DSA.makeLayersFromTileSources(

[ 
{      type: 'image',
      url: 'demoImages/DermoscopyResized.jpg',
      buildPyramid: true
    },
{      type: 'image',
      url: 'demoImages/Vivacam.jpg',
      buildPyramid: true
    }

]))




// console.log(App.dsaItems)

  DSA.dataSetManager.register(
    'llmpp',
    DSA.makeLayersFromTileSources(App.dsaItems.slice(0, 2))
  );




  // ----------
  if (App.dsaItems) {
    App.dsaItems.forEach(function(item) {
      if (item.tileSource && item.baseURL && item.itemId) {
        item.tileSource.getTileUrl = function(level, x, y) {
          return (
            item.baseURL +
            '/item/' +
            item.itemId +
            '/tiles/zxy/' +
            level +
            '/' +
            x +
            '/' +
            y +
            '?edge=crop'
          );
        };
      } else {
        console.warn('DSA item is missing tileSource or baseURL or itemId', item);
      }
    });
  }
})();
