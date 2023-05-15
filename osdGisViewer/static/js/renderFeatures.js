/*This will deal with overlays to render features we pull from the database */
import constants from "./constants.js";

function componentToHex(c) {
  var hex = c.toString(16);
  return hex.length == 1 ? "0" + hex : hex;
}

function rgbToHex(r, g, b) {
  return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

function genRandColorData() {
  //This is for testing, but it will generate random color data I can use for the graphs
  //Adding in some synthetic RGB data
  var limit = 255;
  var rgbColorData = [
    { color: "red", mean: Math.floor(Math.random() * (limit + 1)) },
    { color: "green", mean: Math.floor(Math.random() * (limit + 1)) },
    { color: "blue", mean: Math.floor(Math.random() * (limit + 1)) },
  ];

  return rgbColorData;
}

function findSimilarTiles(avgColor, refFeatureId) {
  /* Query the backend server and pull tiles within some distance threshold */
  var distanceThresh = webix.$$("similarityCutOff").getValue();
  var selectedFeatureSet = webix.$$("featureSetTable").getSelectedItem();

  var ftxract_id = webix.$$("featureSetTable").getSelectedItem().ftxract_id;
  console.log(selectedFeatureSet);
  console.log(avgColor, distanceThresh, ftxract_id);
  //console.log(selectedFeatureSet);
  console.log(ftxract_id);

  $.getJSON(
    constants.SIMILAR_FEATURES_URL +
      "?ftxtract_id=" +
      22 +
      "&distanceThresh=" +
      distanceThresh +
      "&refFeatureId=" +
      refFeatureId
  ).then((similarFeatureData) => {
    //    console.table(similarFeatureData);
  });

  // ).then((featureData) => {
  //   // console.table(featureData);
  //   currentFeatureData.parse(featureData); //Update local copy so I can run stats
  //   renderFeatures.renderGrid(featureData, overlay);
  // });

  //fxtract_id
}

function handleMouseOver(d, i) {
  // Add interactivity
  // Use D3 to select element, change color and size
  //console.log(this )
  var avgColor = this.getAttribute("averageColor");
  var localTileId = this.getAttribute("localTileId");

  webix
    .$$("mouseTrackerBox")
    .setHTML(
      "<div style='background-color:rgb(" +
        avgColor +
        ")'>" +
        this.id +
        "</div>"
    );

  /* this is the logic that grabs the tile data and passes it to compute similarity */

  findSimilarTiles(avgColor, localTileId);

  //   d3.selectAll("#" + this.id).style("fill", "blue");
  //   d3.selectAll("#" + this.id).style("opacity", "0.5");

  //   origTileColor = d3.select(this).attr("origColor");
  //   // fillColor =   d3.select(this).style('fill');

  //   // console.log(origTileColor);
  //   // console.log(d3.selectAll("#" + this.id));

  //   //    tileAvgColor = JSON.parse(d3.selectAll("#" + this.id).style('fill'))
  //   tileAvgColor = d3.selectAll("#" + this.id).style("fill");
  //   tileDataInfo = JSON.parse(d3.selectAll("#" + this.id).attr("tileDataInfo"));

  //   colorLookupData = JSON.parse(
  //     d3.selectAll("#" + this.id).attr("colorLookupData")
  //   );
  //   //this used to be colorlookupData
  //   // console.log(colorLookupData,tileDataInfo);

  //   //This should only run if I am in that mode..
  //   if ($$("findSimilarTiles").getValue()) {
  //     lookupSimilars(origTileColor, tileDataInfo);
  //   } else if ($$("paintMode").getValue()) {
  //     console.log("paint/....");
  //   }

  //   //THIS IS A DISASTER IN TERMS OF EFFICIENCY
  //   //THIS ITERATION ALLOWS ME TO PAINT!!
  //   $$("spxName").setValue(this.id);
  //   $$("rgbChart").clearAll();

  //   //need to reformat the HEX color and put it into the chart format
  //   rgb = colorToRGBArray(origTileColor);
  //   chartData = [
  //     { color: "red", mean: rgb[0] },
  //     { color: "blue", mean: rgb[1] },
  //     { color: "green", mean: rgb[2] },
  //   ];

  //   //Convert the colorLookupData to the format the
  //   $$("rgbChart").parse(chartData);
}

function renderGrid(gridData, overlayHandler) {
  /* This will take the current viewer and generate a square grid on top */
  d3.selectAll(".gutmansSquare").remove();
  console.log(gridData);
  // print(gridData.length);
  var tileIndex = 0;
  // randInt = Math.floor(Math.random() * 20);
  // fillColor = d3.schemeCategory20[randInt % 20];
  gridData.forEach(function (r, idx) {
    var randColorLookup = genRandColorData();
    randColorLookup = JSON.stringify(randColorLookup);
    var a = r.average;
    // fillColor = d3.rgb(a[0], a[1], a[2]);
    var fillColor = rgbToHex(parseInt(a[0]), parseInt(a[1]), parseInt(a[2]));
    // console.log(idx);
    d3.select(overlayHandler.node())
      .append("rect")
      .attr("x", r.topX)
      .attr("y", r.topY)
      .attr("width", r.width)
      .attr("height", r.width)
      .style("fill", fillColor)
      .attr("opacity", 0.7)
      .attr("class", "gutmansSquare")
      .attr("stroke", "blue")
      .attr("stroke-width", 1)
      .attr("id", "grid-" + idx)
      .attr("origColor", fillColor) //need this if I want to switch color back
      .attr("colorImgLookup", randColorLookup)
      .attr("averageColor", a)
      .attr("tileDataInfo", r.tileDataInfo)
      .attr("localTileId", r.localTileId)
      .on("mouseover", handleMouseOver);
    // .on("mouseout", handleMouseOut);
  });
}

export default { rgbToHex: rgbToHex, renderGrid: renderGrid };
