"""These are functions related to basic image processing tasks primarily from numpy arrays"""


# regionprops from skimage.measure provides a lot of information about each labeled region in an image. When you call regionprops, it returns a list of RegionProps objects, each representing a labeled region (or blob in your case). Each RegionProps object contains various properties about the region, such as area, bounding box, centroid, and more.

# Here are some commonly used properties of a single RegionProps object:

# area: The number of pixels in the region.
# bbox: The bounding box (min_row, min_col, max_row, max_col).
# centroid: The centroid coordinate (row, column) of the region.
# convex_area: The number of pixels in the convex hull of the region.
# coords: Coordinates of all pixels in the region.
# eccentricity: The eccentricity of the ellipse that has the same second moments as the region.
# equivalent_diameter: The diameter of a circle with the same area as the region.
# euler_number: The number of objects in the region minus the number of holes in those objects.
# extent: The ratio of pixels in the region to pixels in the total bounding box.
# label: The label in the labeled input image.
# major_axis_length, minor_axis_length: The lengths of the major and minor axes of the ellipse that has the same normalized second central moments as the region.
# mean_intensity: The mean intensity of the region with respect to an intensity image.
# orientation: The angle between the x-axis and the major axis of the ellipse.
