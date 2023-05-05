 tcgaSPXExample = {
   maxLevel: 9,
   minLevel: 0,
   slideName: "TCGA-3L-AA1B-01Z-00-DX2",
   magnification: 40.0,
   "mm_x": 0.000252699,
   "mm_y": 0.000252699,
   width: 87647,
   height: 52434,
   tileHeight: 240,
   tileWidth: 240,
   getTileUrl: function(level, x, y) {
     return "http://imaging.htan.dev/girder/api/v1/item/597de1bd92ca9a000de4bacd/tiles/zxy/" + level + "/" + x + "/" + y + "?edge=crop";
   }
 }

 tcgaCoadExample = {
   maxLevel: 9,
   minLevel: 0,
   slideName: "TCGA-COADSOMETHING",
   magnification: 40.0,
   "mm_x": 0.000252699,
   "mm_y": 0.000252699,
   width: 95615,
   height: 74462,
   tileHeight: 240,
   tileWidth: 240,
   getTileUrl: function(level, x, y) {
     return "http://api.digitalslidearchive.org/api/v1/item/5b9efefee62914002e94b6c6/tiles/zxy/" + level + "/" + x + "/" + y + "?edge=crop";
   }
 }


 function resetColors(id) {
   /*This will reset an SVG back the original color it started as and also restore its
     opacity to what the viewier is currently set at */
   curTileOpacity = $$("gridOpacity").getValue();

   d3.selectAll('.gutmansSquare').each(function(d) {
     origTileColor = d3.select(this).attr('origColor');
     d3.select(this).style('fill', origTileColor)
     d3.select(this).style('opacity', curTileOpacity)
   })
 }


  function computeEuclideanDistance(a, b) {
    var sum = 0
    var n
    for (n = 0; n < a.length; n++) {
      sum += Math.pow(a[n] - b[n], 2)
    }
    return sum
  }




 function genRandColorData() {
   //This is for testing, but it will generate random color data I can use for the graphs
   //Adding in some synthetic RGB data
   limit = 255;
   rgbColorData = [{ color: "red", mean: Math.floor(Math.random() * (limit + 1)) },
     { color: "green", mean: Math.floor(Math.random() * (limit + 1)) },
     { color: "blue", mean: Math.floor(Math.random() * (limit + 1)) }
   ]

   return rgbColorData;
 }


 function componentToHex(c) {
   var hex = c.toString(16);
   return hex.length == 1 ? "0" + hex : hex;
 }

 function rgbToHex(r, g, b) {
   return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
 }

 //hello


 function hexToRgb(hex) {
   var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
   return result ? {
     r: parseInt(result[1], 16),
     g: parseInt(result[2], 16),
     b: parseInt(result[3], 16)
   } : null;
 }



 function handleMouseOut(d, i) {
   // Use D3 to select element, change color back to normal
   // console.log(this);
   // console.log(d, i);

   if ($$("paintMode").getValue()) {
     d3.select(this).style('fill', 'black')


   } else {
     origTileColor = d3.select(this).attr('origColor');
     curTileOpacity = $$("gridOpacity").getValue();
     d3.select(this).style('fill', origTileColor);
     d3.select(this).style('opacity', curTileOpacity);




   }

 }



 function lookupSimilars(selectedRGBData, tileDataInfo) {
  /*compute euclidean distance and show similar tiles...*/
  /* Walk through the color tiles and paint all of the tiles that share the same color... */
  //Currently selected tile kicks this off...
  referenceRGB = colorToRGBArray(selectedRGBData);
  referenceLAB = rgb2lab(referenceRGB);

  d3.selectAll('.gutmansSquare').each(function(d) {
    curTileColor = d3.select(this).attr('origColor');
    useLab = true;
    if (useLab) {
      curLabColor = rgb2lab(colorToRGBArray(curTileColor))
      colorDistance = deltaE(curLabColor, referenceLAB);
    } else {
      colorDistance = computeEuclideanDistance(colorToRGBArray(curTileColor), referenceRGB);
    }

    if (colorDistance < $$("similarityCutOff").getValue()) {
      d3.select(this).style('fill', 'orange');
      d3.select(this).style('opacity', 1)
    } else {
      d3.select(this).style('opacity', 0);
    }
  })
}
 //PAINT BY NUMBER MODE..
