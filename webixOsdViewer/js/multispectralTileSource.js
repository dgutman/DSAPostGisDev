'use strict';

(function() {
  window.App = window.App || {};

  var theDuomo = {
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
  };

  var highsmith = {
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
  };

  var omeTileSourceF1 = {
    slideName: 'TONSIL-1.ome.tiff',
    tileSource: {
      maxLevel: 5,
      minLevel: 0,
      magnification: 30.8,
      mm_x: 0.000325,
      mm_y: 0.000325,
      width: 16843,
      height: 16125,
      tileHeight: 1024,
      tileWidth: 1024,
      getTileUrl: function(level, x, y) {
        return (
          'http://3.82.121.90/api/v1/item/5cc255e1e6291400a24f9e48/tiles/zxy/' +
          level +
          '/' +
          x +
          '/' +
          y +
          '?edge=crop&frame=1'
        );
      }
    }
  };

  var omeTileSourceF2 = {
    slideName: 'TONSIL-1.ome.tiff',
    tileSource: {
      maxLevel: 5,
      minLevel: 0,
      magnification: 30.8,
      mm_x: 0.000325,
      mm_y: 0.000325,
      width: 16843,
      height: 16125,
      tileHeight: 1024,
      tileWidth: 1024,
      getTileUrl: function(level, x, y) {
        return (
          'http://3.82.121.90/api/v1/item/5cc255e1e6291400a24f9e48/tiles/zxy/' +
          level +
          '/' +
          x +
          '/' +
          y +
          '?edge=crop&frame=2'
        );
      }
    }
  };

  var omeTileSourceF3 = {
    slideName: 'TONSIL-1.ome.tiff',
    tileSource: {
      maxLevel: 5,
      minLevel: 0,
      magnification: 30.8,
      mm_x: 0.000325,
      mm_y: 0.000325,
      width: 16843,
      height: 16125,
      tileHeight: 1024,
      tileWidth: 1024,
      getTileUrl: function(level, x, y) {
        return (
          'http://3.82.121.90/api/v1/item/5cc255e1e6291400a24f9e48/tiles/zxy/' +
          level +
          '/' +
          x +
          '/' +
          y +
          '?edge=crop&frame=3'
        );
      }
    }
  };

  var omeTileSourceF4 = {
    slideName: 'TONSIL-1.ome.tiff',
    tileSource: {
      maxLevel: 5,
      minLevel: 0,
      magnification: 30.8,
      mm_x: 0.000325,
      mm_y: 0.000325,
      width: 16843,
      height: 16125,
      tileHeight: 1024,
      tileWidth: 1024,
      getTileUrl: function(level, x, y) {
        return (
          'http://3.82.121.90/api/v1/item/5cc255e1e6291400a24f9e48/tiles/zxy/' +
          level +
          '/' +
          x +
          '/' +
          y +
          '?edge=crop&frame=4'
        );
      }
    }
  };

  var omeTileSourceF5 = {
    slideName: 'TONSIL-1.ome.tiff',
    tileSource: {
      maxLevel: 5,
      minLevel: 0,
      magnification: 30.8,
      mm_x: 0.000325,
      mm_y: 0.000325,
      width: 16843,
      height: 16125,
      tileHeight: 1024,
      tileWidth: 1024,
      getTileUrl: function(level, x, y) {
        return (
          'http://3.82.121.90/api/v1/item/5cc255e1e6291400a24f9e48/tiles/zxy/' +
          level +
          '/' +
          x +
          '/' +
          y +
          '?edge=crop&frame=5'
        );
      }
    }
  };

  var weillTileSourceF1 = {
    slideName: 'Pic1',
    tileSource: {
      maxLevel: 0,
      minLevel: 0,
      tileWidth: 956,
      width: 956,
      height: 1351,
      tileHeight: 1351,
      getTileUrl: function(level, x, y) {
        return (
          'http://localhost:8080/api/v1/item/5cec39b88593106742b59719/tiles/zxy/' +
          level +
          '/' +
          x +
          '/' +
          y +
          '?edge=crop&frame=5'
        );
      }
    }
  };

  var weillTileSourceF2 = {
    slideName: 'Pic2',
    tileSource: {
      maxLevel: 0,
      minLevel: 0,
      tileWidth: 956,
      width: 956,
      height: 1351,
      tileHeight: 1351,
      getTileUrl: function(level, x, y) {
        return (
          'http://localhost:8080/api/v1/item/5cec39b88593106742b5971c/tiles/zxy/' +
          level +
          '/' +
          x +
          '/' +
          y +
          '?edge=crop&frame=5'
        );
      }
    }
  };

  var groupTileSourceSpec = {
    height: 1588,
    maxLevel: 0,
    minLevel: 0,
    tileHeight: 1588,
    tileWidth: 2022,
    width: 2022
  };

  var pythonFolderSpec = {
    apiUrl: 'https://imaging.humantumoratlas.org/api/v1',
    grpName: 'equalized'
  };

  var channelInfo = [
    {
      _id: '5cef22aee6291400a2f67f08',
      channel: '146Nd',
      label: 'CD16',
      slideName: '146Nd_CD16.equalized.ome.tiff',
      width: groupTileSourceSpec.width,
      minLevel: 0,
      maxLevel: 0,
      tileWidth: groupTileSourceSpec.width,
      tileHeight: groupTileSourceSpec.tileHeight,
      thumbnail:
        'https://imaging.humantumoratlas.org/api/v1/item/5cef22aee6291400a2f67f08/tiles/thumbnail?frame=5',
      tileSource: {
        height: 1588,
        maxLevel: 0,
        minLevel: 0,
        tileHeight: 1588,
        tileWidth: 2022,
        width: 2022,
        getTileUrl: function(level, x, y) {
          return (
            'https://imaging.humantumoratlas.org/api/v1/item/5cef22aee6291400a2f67f08/tiles/zxy/' +
            level +
            '/' +
            x +
            '/' +
            y +
            '?edge=crop&frame=5'
          );
        }
      }
    },
    {
      _id: '5cef22b5e6291400a2f67f0b',
      channel: '158Gd',
      label: 'E-Cadherin',
      slideName: '158Gd_E-Cadherin.equalized.ome.tiff',
      width: groupTileSourceSpec.width,
      minLevel: 0,
      maxLevel: 0,
      tileWidth: groupTileSourceSpec.width,
      tileHeight: groupTileSourceSpec.tileHeight,
      thumbnail:
        'https://imaging.humantumoratlas.org/api/v1/item/5cef22b5e6291400a2f67f0b/tiles/thumbnail?frame=5',
      tileSource: {
        height: 1588,
        maxLevel: 0,
        minLevel: 0,
        tileHeight: 1588,
        tileWidth: 2022,
        width: 2022,

        getTileUrl: function(level, x, y) {
          return (
            'https://imaging.humantumoratlas.org/api/v1/item/5cef22b5e6291400a2f67f0b/tiles/zxy/' +
            level +
            '/' +
            x +
            '/' +
            y +
            '?edge=crop&frame=5'
          );
        }
      }
    },
    {
      _id: '5cef22bbe6291400a2f67f0e',
      channel: '159Tb',
      label: 'CD68',
      slideName: '159Tb_CD68.ome.equalized.tiff',
      width: groupTileSourceSpec.width,
      minLevel: 0,
      maxLevel: 0,
      tileWidth: groupTileSourceSpec.width,
      tileHeight: groupTileSourceSpec.tileHeight,
      thumbnail:
        'https://imaging.humantumoratlas.org/api/v1/item/5cef22bbe6291400a2f67f0e/tiles/thumbnail?frame=5',
      tileSource: {
        height: 1588,
        maxLevel: 0,
        minLevel: 0,
        tileHeight: 1588,
        tileWidth: 2022,
        width: 2022,

        getTileUrl: function(level, x, y) {
          return (
            'https://imaging.humantumoratlas.org/api/v1/item/5cef22bbe6291400a2f67f0e/tiles/zxy/' +
            level +
            '/' +
            x +
            '/' +
            y +
            '?edge=crop&frame=5'
          );
        }
      }
    },
    {
      _id: '5cef22c3e6291400a2f67f17',
      channel: '191Ir',
      label: 'DNA1',
      slideName: '191Ir_DNA1.equalize.ome.tiff',
      width: groupTileSourceSpec.width,
      minLevel: 0,
      maxLevel: 0,
      tileWidth: groupTileSourceSpec.width,
      tileHeight: groupTileSourceSpec.tileHeight,
      thumbnail:
        'https://imaging.humantumoratlas.org/api/v1/item/5cef22c3e6291400a2f67f17/tiles/thumbnail?frame=5',
      tileSource: {
        height: 1588,
        maxLevel: 0,
        minLevel: 0,
        tileHeight: 1588,
        tileWidth: 2022,
        width: 2022,

        getTileUrl: function(level, x, y) {
          return (
            'https://imaging.humantumoratlas.org/api/v1/item/5cef22c3e6291400a2f67f17/tiles/zxy/' +
            level +
            '/' +
            x +
            '/' +
            y +
            '?edge=crop&frame=5'
          );
        }
      }
    },
    {
      _id: '5cef22cde6291400a2f67f1a',
      channel: '193Ir',
      label: 'DNA2',
      slideName: '193Ir_DNA2.equalize.ome.tiff',
      width: groupTileSourceSpec.width,
      minLevel: 0,
      maxLevel: 0,
      tileWidth: groupTileSourceSpec.width,
      tileHeight: groupTileSourceSpec.tileHeight,
      thumbnail:
        'https://imaging.humantumoratlas.org/api/v1/item/5cef22cde6291400a2f67f1a/tiles/thumbnail?frame=5',
      tileSource: {
        height: 1588,
        maxLevel: 0,
        minLevel: 0,
        tileHeight: 1588,
        tileWidth: 2022,
        width: 2022,

        getTileUrl: function(level, x, y) {
          return (
            'https://imaging.humantumoratlas.org/api/v1/item/5cef22cde6291400a2f67f1a/tiles/zxy/' +
            level +
            '/' +
            x +
            '/' +
            y +
            '?edge=crop&frame=5'
          );
        }
      }
    }
  ];

  // channelInfo.forEach(function(item) {
  //   // if (item.tileSource && item.baseURL && item.itemId) {
  //   item.tileSource = groupTileSourceSpec;
  //   item.tileSource.getTileUrl = item.getTileUrl;
  //   // item.tileSource.getTileUrl =  function(level, x, y) {
  //   //   return (  "https://imaging.humantumoratlas.org/api/v1" + '/item/' +item._id + '/tiles/zxy/' +level +'/' + x + '/' +y +'?edge=crop&frame=5');
  //   // }

  // });

  // console.log(channelInfo);

  const omeTiffUID = '5cc255e1e6291400a24f9e48';
  const singleOMETiffExample = [
    {
      _id: '5cc255e1e6291400a24f9e48',
      channel: 'A',
      label: 'A',
      slideName: 'A.tiff',
      width: groupTileSourceSpec.width,
      minLevel: 0,
      maxLevel: 0,
      tileWidth: groupTileSourceSpec.width,
      tileHeight: groupTileSourceSpec.tileHeight,
      tileSource: {
        height: 1588,
        maxLevel: 0,
        minLevel: 0,
        tileHeight: 1588,
        tileWidth: 2022,
        width: 2022,

        getTileUrl: function(level, x, y) {
          return (
            'https://imaging.humantumoratlas.org/api/v1/item/5cc255e1e6291400a24f9e48/tiles/zxy/' +
            level +
            '/' +
            x +
            '/' +
            y +
            '?edge=crop&frame=0'
          );
        }
      }
    },
    {
      _id: '5cc255e1e6291400a24f9e48',
      channel: 'B',
      label: 'B',
      slideName: 'B.tiff',
      width: groupTileSourceSpec.width,
      minLevel: 0,
      maxLevel: 0,
      tileWidth: groupTileSourceSpec.width,
      tileHeight: groupTileSourceSpec.tileHeight,
      tileSource: {
        height: 1588,
        maxLevel: 0,
        minLevel: 0,
        tileHeight: 1588,
        tileWidth: 2022,
        width: 2022,

        getTileUrl: function(level, x, y) {
          return (
            'https://imaging.humantumoratlas.org/api/v1/item/5cc255e1e6291400a24f9e48/tiles/zxy/' +
            level +
            '/' +
            x +
            '/' +
            y +
            '?edge=crop&frame=1'
          );
        }
      }
    },
    {
      _id: '5cc255e1e6291400a24f9e48',
      channel: 'C',
      label: 'C',
      slideName: 'C.ome.tiff',
      width: groupTileSourceSpec.width,
      minLevel: 0,
      maxLevel: 0,
      tileWidth: groupTileSourceSpec.width,
      tileHeight: groupTileSourceSpec.tileHeight,
      tileSource: {
        height: 1588,
        maxLevel: 0,
        minLevel: 0,
        tileHeight: 1588,
        tileWidth: 2022,
        width: 2022,

        getTileUrl: function(level, x, y) {
          return (
            'https://imaging.humantumoratlas.org/api/v1/item/5cc255e1e6291400a24f9e48/tiles/zxy/' +
            level +
            '/' +
            x +
            '/' +
            y +
            '?edge=crop&frame=2'
          );
        }
      }
    }
  ];

  DSA.dataSetManager.register(
    'multiSpectExampleSet1',
    DSA.makeLayers([
      omeTileSourceF1,
      omeTileSourceF2,
      omeTileSourceF3,
      omeTileSourceF4,
      omeTileSourceF5
    ])
  );

  DSA.dataSetManager.register(
    'multiSpectExampleSet2',
    DSA.makeLayers([weillTileSourceF1, weillTileSourceF2])
  );

  DSA.dataSetManager.register(
    'jcADRC',
    DSA.makeLayers([
      {
        slideName: 'Base',
        tileSource:
          'http://computablebrain.emory.edu:8080/api/v1/item/5dcf2edf9f68993bf165a972/tiles/dzi.dzi'
      },
      {
        slideName: 'MASK',
        tileSource:
          'http://computablebrain.emory.edu:8080/api/v1/item/5dcf30a59f68993bf165a97b/tiles/dzi.dzi'
      }
    ])
  );

  DSA.dataSetManager.register('multiSpectExampleSet3', DSA.makeLayers(channelInfo));

  DSA.dataSetManager.register('multiSpectExampleSet4', function(callback) {
    var serverApiURL = 'https://imaging.humantumoratlas.org/api/v1/';
    var folderId = '5d5db4e0e6291400a2f67f2c';
    var multiSpectExampleSet4 = [];

    $.ajax({ url: serverApiURL + 'item?folderId=' + folderId, async: false }).then(function(data) {
      // console.log(data);

      /*Look for the word outlines and mask in the image stack, and use that to set the parameters...*/

      //Blue will be the color of an image with Nuclei in it
      //Green would be the color of a cell
      //Orange  will be the color of cytoplasm

      data.forEach(function(item, idx) {
        // console.log(item);

        if (item.largeImage != undefined) {
          //make sure I only process largeImage items...
          if (item.name.endsWith('.ome.tif')) {
            // console.log('Need to process an OME TIFF image');
            multiSpectExampleSet4.push(
              DSA.makeLayer({
                width: 7604,
                opacity: 1,
                brightness: 0,
                label: item.name + 'Ch0',
                slideName: item.name + '.' + 'CH0',
                tileSource: serverApiURL + 'item/' + item._id + '/tiles/dzi.dzi'
              })
            );
          } else if (item.name.toLowerCase().endsWith('mask.tif')) {
            multiSpectExampleSet4.push(
              DSA.makeLayer({
                width: 7604,
                opacity: 1,
                brightness: -0.5,
                label: item.name,
                slideName: item.name,
                tileSource: serverApiURL + 'item/' + item._id + '/tiles/dzi.dzi'
              })
            );
          } else {
            console.log('[multiSpectExampleSet4] unknown name', item.name);
          }
        }
        //   //for OME TIFF Files, need to generate individual names for each frame
        //   if (item.name.endsWith('.ome.tif')) {
        //     multiSpectExampleSet4.push(DSA.makeLayer({ opacity: 1, brightness: 0, label: item.name, slideName: item.name, tileSource: serverApiURL + "item/" + item._id + '/tiles/dzi.dzi?frame=0' }))
        //   } else if (item.name.contains('Mask')) {
        //     multiSpectExampleSet4.push(DSA.makeLayer({ opacity: 1, brightness: -0.31, label: item.name, slideName: item.name, tileSource: serverApiURL + "item/" + item._id + '/tiles/dzi.dzi' }))
        //   } else {
        //     multiSpectExampleSet4.push(DSA.makeLayer({ opacity: 1, brightness: -0.5, label: item.name, slideName: item.name, tileSource: serverApiURL + "item/" + item._id + '/tiles/dzi.dzi' }))
        //   }

        // }
      });

      callback(multiSpectExampleSet4);
    });
  });

  DSA.dataSetManager.register('tonsilSet', function(callback) {
    var serverApiURL = 'https://imaging.humantumoratlas.org/api/v1/';
    var itemId = '5cc255e1e6291400a24f9e48';
    var url = serverApiURL + 'item/' + itemId;
    var tonsilSet = [];

    $.ajax({ url: url }).then(function(data) {
      _.each(data.meta.omeSceneDescription, function(item, index) {
        tonsilSet.push(
          DSA.makeLayer({
            slideName: item.channel_name,
            thumbnail: url + '/tiles/thumbnail?frame=' + index,
            tileSource: url + '/tiles/dzi.dzi?frame=' + index
          })
        );
      });

      callback(tonsilSet);
    });
  });



  DSA.dataSetManager.register('multiFrameSet', function(callback) {
    var serverApiURL = 'https://imaging.htan.dev/girder/api/v1/';
    var folderId = '6036bf2b1e6134859db73021';

    var url = serverApiURL + 'item?folderId=' + folderId;
    var multiFrameSet = [];

    $.ajax({ url: url }).then(function(data) {

		console.log(data);
      _.each(data, function(item, index) {

         console.log(item);
		if ('largeImage' in item)
{
     var xOffset = (item.meta.global_x) ? item.meta.global_x: 0;
     var yOffset = (item.meta.global_y) ? item.meta.global_y: 0;
     var startFrame = 218;

        multiFrameSet.push(
          DSA.makeFrameLayer({
            slideName: item.name,
            thumbnail: serverApiURL + '/item/' + item._id + '/tiles/thumbnail?frame=' + startFrame,
            tileSource: serverApiURL + '/item/' + item._id + '/tiles/dzi.dzi?frame=' + startFrame,
			defaultColor: "#0000ff",
			xOffset: xOffset,
		    yOffset: yOffset
          })
        ); }
      });

      callback(multiFrameSet);
    });
  console.log(multiFrameSet)

  });








  DSA.makeServerDataSet = function(key, serverUrl, itemId) {
    DSA.dataSetManager.register(key, function(callback) {
      var url = serverUrl + '/item/' + itemId + '/';

      var tilesPromise = new Promise(function(resolve, reject) {
        var set = [];

        $.ajax({ url: url + 'tiles' }).then(function(data) {
          _.each(data.frames, function(item, index) {
            set.push(
              DSA.makeLayer({
                slideName: item.Channel,
                thumbnail: url + 'tiles/thumbnail?frame=' + index,
                tileSource: url + 'tiles/dzi.dzi?frame=' + index
              })
            );
          });

          resolve(set);
        });
      });

      var metaPromise = new Promise(function(resolve, reject) {
        $.ajax({ url: url }).then(function(data) {
          resolve(data);
        });
      });

      Promise.all([tilesPromise, metaPromise]).then(function(results) {
        var tiles = results[0];
        var meta = results[1];

        callback(tiles, meta);
      });
    });
  };

  // $.ajax('js/cellMask.json', function(data) {
  //   console.log(data);
  // });
})();
