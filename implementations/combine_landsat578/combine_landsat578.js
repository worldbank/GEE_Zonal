var imageCollection = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR"),
    table = ee.FeatureCollection("users/jbelanger/IOM_round11_BDG_1kmbuff");

/*

follows GEE tutorial : https://developers.google.com/earth-engine/tutorials/community/landsat-etm-to-oli-harmonization#references

*/

Map.centerObject(table, 7);
var bbox = table.geometry().bounds();


//Establish image visualization parameters
var imageVisParam1 = {bands: ['B5', 'B4', 'B3'], min: 0, max: 5800};
var imageVisParam2 = {bands: ['B5', 'B4', 'B3'], min: 0, max: 0.58};


// the wavelengths between the two sensors are different,
// so you have to perform a linear transform. multiply by 10,000 for surfce reflectance.
var coefficients = {
  itcps: ee.Image.constant([0.0003, 0.0088, 0.0061, 0.0412, 0.0254, 0.0172])
             .multiply(10000),
  slopes: ee.Image.constant([0.8474, 0.8483, 0.9047, 0.8462, 0.8937, 0.9071])
};

// rename bands so that they can be compared.
// Function to get and rename bands of interest from OLI.
function renameOli(img) {
  return img.select(
      ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'pixel_qa'],
      ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']);
}

// Function to get and rename bands of interest from ETM+.
function renameEtm(img) {
  return img.select(
      ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'pixel_qa'],
      ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']);
}

// define the transfornation function to apply the linear model to the TM data
function etmToOli(img) {
  return img.select(['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2'])
      .multiply(coefficients.slopes)
      .add(coefficients.itcps)
      .round()
      .toShort()
      .addBands(img.select('pixel_qa'));
}

// cloud and shadow masking
function fmask(img) {
  var cloudShadowBitMask = 1 << 3;
  var cloudsBitMask = 1 << 5;
  var qa = img.select('pixel_qa');
  var mask = qa.bitwiseAnd(cloudShadowBitMask)
                 .eq(0)
                 .and(qa.bitwiseAnd(cloudsBitMask).eq(0));
  return img.updateMask(mask);
}


function addBands(image){
  var ndvi = image.normalizedDifference(['Red', 'NIR']).rename('NDVI'); // ndvi = (nir - red) / (nir + red)
  var ndwi = image.normalizedDifference(['NIR', 'SWIR1']).rename('NDWI'); // ndbi = (red - nir) / (red + nir)
  var mndwi = image.normalizedDifference(['Green', 'SWIR1']).rename('MNDWI'); // ndbi = (red - nir) / (red + nir)
  var evi = image.expression(
    '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
      'NIR': image.select('NIR'),
      'RED': image.select('Red'),
      'BLUE': image.select('Blue')
}).rename('EVI');
  return image.addBands(ndvi).addBands(ndwi).addBands(mndwi).addBands(evi);
}

// combine functions
// Define function to prepare OLI images.
function prepOli(img) {
  var orig = img;
  img = renameOli(img);
  img = fmask(img);
  img = addBands(img);
  return ee.Image(img.copyProperties(orig, orig.propertyNames()));
}

// Define function to prepare ETM+ images.
function prepEtm(img) {
  var orig = img;
  img = renameEtm(img);
  img = fmask(img);
  img = etmToOli(img);
  img = addBands(img);
  return ee.Image(img.copyProperties(orig, orig.propertyNames()));
}

// create collections and map the prepEtm/Oli functions on each
var tmCol = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR")
                      .filterDate('2006-09-01', '2013-06-05')
                      .filterBounds(table)
                      .map(prepEtm);

print("tmCol: ", tmCol);

var etmCol = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR")
                      .filterDate('2010-01-01', '2015-01-01')
                      .filterBounds(table)
                      .map(prepEtm);
print("etmCol: ", etmCol);

var oliCol = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR")
                      .filterDate('2013-03-01', '2020-09-30')
                      .filterBounds(table)
                      .map(prepEtm);
print("oliCol: ", oliCol);


// run gap fill algorithm on landsat 7 to correct striping
var kernelSize = 10;
var kernel = ee.Kernel.square(kernelSize * 30, 'meters', false);

var GapFill = function(image) {
  var start = image.date().advance(-1, 'year');
  var end = image.date().advance(1, 'year');
  var fill = etmCol.filterDate(start, end).median();
  var regress = fill.addBands(image);
  regress = regress.select(regress.bandNames().sort());
  var fit = regress.reduceNeighborhood(ee.Reducer.linearFit().forEach(image.bandNames()), kernel, null, false);
  var offset = fit.select('.*_offset');
  var scale = fit.select('.*_scale');
  var scaled = fill.multiply(scale).add(offset);
  return image.unmask(scaled, true);
};
// map gapfill algorithm to the etm collection
var etmCol_gapfill = etmCol.map(GapFill);

// merge collection
var col = oliCol.merge(etmCol_gapfill).merge(tmCol);
print("merged col w indices: ", col.first());

/*
//----------------- export col to asset -----------------------//
print('//----------------- export col to asset  -----------------------//');

// Export the image to an Earth Engine asset.
Export.image.toAsset({
  image: col,
  description: 'landsat578_gapfill_2006_2020_evi_ndvi_ndwi_mndwi',
  assetId: 'landsat578_2006_2020',
  scale: 30,
  region: bbox,
});
*/
