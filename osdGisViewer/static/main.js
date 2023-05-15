import constants from "./js/constants.js";
import renderFeatures from "./js/renderFeatures.js";
import similarityCompute from "./js/similarityCompute.js";
// import ajaxActions from "./services/ajaxActions";

/* Basic initialization for all webix components */
var osdViewer = OpenSeadragon({
  id: "osdViewer1",
  prefixUrl: "/node_modules/openseadragon/build/openseadragon/images/",
  tileSources: [{ tileSource: constants.TEST_TILE_SRC }],
});

function viewerOpened() {
  //This needs to clear any prexisting annotations
  d3.selectAll(".gutmansSquare").remove();
}

osdViewer.addHandler("open", viewerOpened);
var overlay = osdViewer.svgOverlay();

let currentFeatureData = new webix.DataCollection({ id: "currentFeatureData" }); //While I am putting the feature data into the overlay
//I am also keeping a copy in case I need to reprocess things

/* TO DO: See how to better scope the overlay object, I think maybe I can grab it from the viewer */
function buildImageTileSource(imageInfo) {
  console.log(imageInfo);
  var tileSourceUrl =
    imageInfo.apiURL + "/item/" + imageInfo.imageId + "/tiles/dzi.dzi";

  return { tileSource: tileSourceUrl, width: imageInfo.sizeX };
}

var imageSelector = {
  view: "combo",
  label: "Image Selector",
  id: "imageSelectCombo",
  dataFeed: "http://localhost:82/getImageList/",
  options: { body: { template: "#imageName#" } },
  width: 400,
  on: {
    onChange: function (newv, oldv) {
      /* get the imageId for the selected image, and then need to populate the list of available features */
      var selectedImage = $$(this).getPopup().getList().getItem(newv);
      var ts = buildImageTileSource(selectedImage);
      var ftrLookupUrl =
        constants.FEATURE_LIST_URL + "?imageId=" + selectedImage.imageId;
      osdViewer.open(ts);

      $.getJSON(ftrLookupUrl).then(function (featureSetData) {
        $$("featureSetTable").clearAll();
        $$("featureSetTable").parse(featureSetData);
      });
    },
  },
};

var similarityCutOff = {
  view: "slider",
  id: "similarityCutOff",
  label: "SimCutOff",
  value: 5,
  min: 0,
  max: 255,
  step: 5,
  inputWidth: 200,
  labelWidth: 100,
  title: "#value#",
  on: {
    onChange: function (newv, oldv) {
      webix.message("Something slid" + newv);
    },
  },
};

var opacitySlider = {
  view: "slider",
  label: "gridOpacity",
  value: constants.START_GRID_OPACITY,
  inputWidth: 200,
  labelWidth: 100,
  min: 0,
  step: 0.05,
  max: 1,
  id: "gridOpacity",
  on: {
    onChange: function (newv, oldv) {
      d3.selectAll(".gutmansSquare").style("opacity", newv);
    },
  },
};

var featureDataStore = { view: "datastore", id: "featureDataStore" };

var dsaSpxHeader = {
  view: "label",
  type: "header",
  css: "osdGisHeader",
  label: "DSA OSD PostGis Viewer",
  align: "center",
  height: 20,
};

var featureColumns = [
  { id: "featureType" },
  { id: "magnification" },
  { id: "tilesProcessed" },
];

var featureSetSelector = {
  rows: [
    { type: "header", template: "gridSize" },
    {
      view: "datatable",
      columns: featureColumns,
      select: "row",
      id: "featureSetTable",
      on: {
        onAfterSelect: function (id) {
          // webix.message("table was clicked");
          var item = $$(this).getItem(id);
          //console.log(item);

          $.getJSON(
            constants.TILE_FEATURES_URL +
              "?imageId=" +
              item.imageId +
              "&ftxtract_id=" +
              item.ftxtract_id
          ).then((featureData) => {
            // console.table(featureData);
            currentFeatureData.parse(featureData); //Update local copy so I can run stats
            renderFeatures.renderGrid(featureData, overlay);
          });
        },
      },
    },
  ],
};

var mouseInfoBox = {
  view: "label",
  id: "mouseTrackerBox",
  label: "Active ROI",
  value: "1",
  inputWidth: 150,
};

var main_layout = {
  rows: [
    dsaSpxHeader,
    {
      cols: [imageSelector, mouseInfoBox, opacitySlider, similarityCutOff],
    },
    {
      cols: [
        featureSetSelector,
        {
          content: "osdContainer",
          gravity: 4,
        },
      ],
    },
  ],
};

// webix.debug({ events: true });
webix.ui(main_layout);

webix
  .$$("imageSelectCombo")
  .getPopup()
  .getList()
  .data.attachEvent("onParse", function () {
    console.log(this.getFirstId());
  });

webix.ready(function () {
  //Kick start the process, this will load the list of available images

  /* This will pull the list of images that have been loaded into the local database */
  $.getJSON(constants.IMAGE_LIST_URL).then((imageListData) => {
    var imgList = $$("imageSelectCombo").getPopup().getList();
    imgList.parse(imageListData);
  });
});
