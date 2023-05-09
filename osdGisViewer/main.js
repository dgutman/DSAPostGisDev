import constants from "./js/constants.js";
import renderFeatures from "./js/renderFeatures.js";

// import ajaxActions from "./services/ajaxActions";

console.log(renderFeatures.rgbToHex(1, 2, 3));

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
};

var main_layout = {
  rows: [
    dsaSpxHeader,
    {
      cols: [imageSelector, mouseInfoBox],
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
