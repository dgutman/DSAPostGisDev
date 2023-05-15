import numpy

import numpy as np
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000


def patch_asscalar(a):
    return a.item()


setattr(numpy, "asscalar", patch_asscalar)


R = 6371


def build_adress(x):
    adress = x["adress"].lower() + " " + str(x["cp"]) + " " + x["city"].lower()
    adress = " ".join([e.capitalize() if len(e) >= 3 else e for e in adress.split(" ")]).replace(" l ", " l'")
    adress = "-".join([e[0].upper() + e[1:] if len(e) >= 3 else e for e in adress.split("-")])

    return pretify_address(adress)


def pretify_address(adress):
    adress = " ".join([e.capitalize() if len(e) >= 3 else e for e in adress.lower().split(" ")]).replace(" l ", " l'")

    adress = "-".join([e[0].upper() + e[1:] if len(e) >= 3 else e for e in adress.split("-")])

    return adress


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points (lat1,lon1) and (lat2, lon2) in km"""

    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    distance = R * c
    return distance


def extend_dict(x_, avg, clat, clon):
    new_address = build_adress(x_)
    delta_average = -float(np.round(float(x_["valeur"]) * 60 - avg * 60, 1))
    return {
        "address": new_address,
        "price_per_L": float(np.round(float(x_["valeur"]), 2)),
        "price_tank": round(float(x_["valeur"]) * 60),
        "delta_average": delta_average,
        "better_average": (delta_average > 0) * 1 + (delta_average < 0) * -1,
        "google_map_link": f"https://www.google.com/maps/search/?api=1&query={new_address.replace(' ','+')}",
        "distance": haversine_distance(x_["latitude"], x_["longitude"], clat, clon),
        "latitude": x_["latitude"],
        "longitude": x_["longitude"],
    }


def computeColorSimilarityForFeatureSet(featureSet, refFeatureVector, distanceThreshold):
    ### This expects a featureset, in this case it will simply be the average color for each tile
    ## I also am passing the referenceColor (i.e. feature) separately... this should then go through each individual
    ## feature and convert it to LAB space and use the colormath library to compute the delta_e score
    ## In the futurue I may want to look into cython or HIT
    """referenceColor: [Array]"""

    referenceColor = [240, 220, 240]

    refColor_rgb = sRGBColor(
        float(referenceColor[0]), float(referenceColor[1]), float(referenceColor[2]), is_upscaled=True
    )
    refColor_lab = convert_color(refColor_rgb, LabColor)

    tilesInRange = []  ### This will store the tiles that are within the specified unit distance and also their ID
    for i in featureSet:
        tileColor_rgb = sRGBColor(i.average[0], i.average[1], i.average[2], is_upscaled=True)
        tileColor_lab = convert_color(tileColor_rgb, LabColor)
        delta_e = delta_e_cie2000(refColor_lab, tileColor_lab)
        tilesInRange.append((i.localTileId, delta_e))

    return tilesInRange
