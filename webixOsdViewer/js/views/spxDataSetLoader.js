/*This view will load data from a static JSON file for now... but eventually will grab data from
a girder instance...*/


var dsHeader = { view: "template", type: "header", template: "Select Data" };

var dataSelector = { id: "dataSelector", rows: [dsHeader] }

var dataSelector = dsHeader;
myDataSetItem = {}

var dataSetCombo = {
  view: "combo",
  id: "dataSetCombo",
  url: "http://localhost:82/getImageList/",//'multiPatientGridData.json",
  options: { body: { template: "#imageName#" } },
  on: {
    onChange: function(id) {
      dataSetItem = $$(this).getPopup().getList().getItem(id);


      myDataSetItem = buildOSDTileSource(dataSetItem);
      //      console.log(myDataSetItem);
      osdViewer.open(myDataSetItem);
      		console.log(dataSetItem);

        var getTileFeatureUrl = "http://localhost:82/getFeatureSets?imageId="+dataSetItem.imageId
        console.log(getTileFeatureUrl)
          $.getJSON(getTileFeatureUrl).then(function(tileGridData) {
            console.log(tileGridData)
          var   featureData =   [{
            "segmentType": "grid", 
            "tileSizeFullRes": 1024, 
            "downSampleFactor": 64,
            "gridData": tileGridData 
                      }]
                      $$("gridSizeDataTable").clearAll()	
                      console.log(featureData)

                      $$("gridSizeDataTable").parse(featureData)
          
          // renderGrid(data.tileDa
            })

          //  $$("gridSizeDataTable").parse(dataSetItem.tileData) 


    }
  }
}

var gridSizeSelector = {
  rows: [{ type: "header", template: "gridSize" },
    {
      view: "datatable",
      autoConfig: true,
      id: "gridSizeDataTable",
      on: {
        onAfterSelect: function(id) {
          webix.message("table was clicked")
          item = $$(this).getItem(id);
          console.log(item);
          renderGrid(item.gridData,overlay);


		
        }
      }
    }
  ]
}

var dataSelector = {
  rows: [{ view: "template", type: "header", template: "Data Selector" },
    dataSetCombo,
    gridSizeSelector,
    {}
  ]
}

function createTileUrlFunction(imageID, baseURL) {
  dziTileUrl = baseURL + "/item/" + imageId;
  return dziTileUrl
}


function buildOSDTileSource(itemInfo) {
  /*Given the item Info from girder and the associated image params
  will build a tile source that is in the right format for OSD*/
  i = itemInfo;
  var tileSourceFunction = (function(i) {
    return function(level, x, y) {
      return i.apiURL + '/item/' + i.imageId + '/tiles/zxy/' + level + '/' + x + '/' + y + '?edge=crop'
    }
  })(i);

  tileSource = {
    width: i.sizeX,
    height: i.sizeY,
    tileWidth: i.tileWidth,
    tileHeight: i.tileHeight,
    minLevel: 0,
    maxLevel: i.levels - 1,
    getTileUrl: tileSourceFunction

  }

  tileObject = { tileSource: tileSource, width: i.sizeX }
  return tileObject
};
