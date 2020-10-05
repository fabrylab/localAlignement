import numpy as np
from collections import defaultdict

from skimage.segmentation import watershed
from scipy.ndimage import distance_transform_edt
from scipy.ndimage import binary_closing
from localAlignement.parameters_and_strings import *

def get_line(start, end):
    ######bresenhams line algorithm from http://www.roguebasin.com/index.php?title=Bresenham%27s_Line_Algorithm
    # also chek out https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
    """Bresenham's Line Algorithm
    Produces a list of tuples from start and end
    start end as tupels of points
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)

    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    # Swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True

    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1

    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1

    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx

    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points


def determine_left_right(p, lp1, lp2, p_ref):

    ####### not used ##############
    '''
    # following https://math.stackexchange.com/questions/274712/calculate-on-which-side-of-a-straight-line-is-a-given-point-located
    # determines if a point lies to the same side of a line as a reference point
    # needs reference point to define which site the sign signifies in the end.
    :param p: point. List or array with [y,x]
    :param p_ref: reference point. List or array with [y,x]
    :param lp1: start point of the line. List or array with [y,x]
    :param lp2: end point of the line. List or array with [y,x]
    :return:
    '''
    det = (p[1] - lp1[1]) * (lp2[0] - lp1[0]) - (p[0] - lp1[0]) * (lp2[1] - lp1[1])
    det_ref = (p_ref[1] - lp1[1]) * (lp2[0] - lp1[0]) - (p_ref[0] - lp1[0]) * (lp2[1] - lp1[1])

    det = det > 0
    det_ref = det_ref >0
    return det == det_ref


def dist_to_line(p, lp1, lp2):



    ####### not used ##############

    '''

    :param p: point. List or array with [y,x]
    :param lp1: start point of the line. List or array with [y,x]
    :param lp2: end point of the line. List or array with [y,x]
    :return:
    '''

    v1 = lp1 - lp2 # line vector
    # vectors from line starts to point(s)
    v2 = np.array([p[0] - lp1[0], p[1] - lp1[1]])
    # angle between main vector and start-to-point vector
    angle = np.arctan2(v1[0], v1[1]) - np.arctan2(v2[0], v2[1])
    # length of start-to-point vector
    length2 = np.linalg.norm(v2, axis=0)
    # distance to line
    dist = np.abs(np.sin(angle) * length2)
    return dist

def dist_to_short_line(p, l):

    ####### not used ##############

    # p is array of points [y,x]
    # l is [[y,x][y,x]] array with start and endpoint of a line

    v1 = l[1] - l[0]
    v1_n = np.array([-v1[1], v1[0]])  # vector perpendicular to v1
    pn1 = v1_n + l[0]  # normal vector endpoint at point1
    pn2 = v1_n + l[1]  # normal vector endpoint at point2
    mid_point = l[0] + (v1 / 2)

    # distance to line
    det1 = determine_left_right([p[0], p[1]], l[0], pn1, mid_point)
    det2 = determine_left_right([p[0], p[1]], l[1], pn2, mid_point)
    det = det1 & det2  # all points inside of the are that is dominated by distance ro line
    dist_p1_line = dist_to_line([p[0], p[1]], l[0], l[1])
    dist_p1_line[~det] = np.inf

    # distance to line endpoints
    dist_p1 = np.linalg.norm(np.array([p[0] - l[0][0], p[1] - l[0][1]]), axis=0)
    dist_p2 = np.linalg.norm(np.array([p[0] - l[1][0], p[1] - l[1][1]]), axis=0)
    dist = np.minimum(np.minimum(dist_p1, dist_p2), dist_p1_line)
    return dist


def process_data(full_data, interpolation_factor):
    total_forces = []
    total_areas = []
    pro_data = {}
    # a few measures for the alignement:
    for obj_id, data in full_data.items():
        x_pos, y_pos, vec_x, vec_y, dists, lvs, mps, vec = data
        # projected force by calcualting the scalar product
        proj = np.sum(np.abs(vec_x * vec[1] + vec_y * vec[0])) / np.linalg.norm(vec)
        # normalized by total force in this patch--> this is probably not usefull
        total_force = np.sum(np.linalg.norm(np.array([vec_x, vec_y]), axis=0))
        # proj_norm = proj/total_force
        total_forces.append(total_force)

        # projecting on the line and weighting by distance to the line
        proj_weighted_dist = np.sum(np.abs(vec_x * vec[1] * dists + vec_y * vec[0] * dists)) / (
                    np.linalg.norm(vec) * np.sum(dists))

        # area of the mask blob in pixels**" of the original image
        ## TODO do I need to square interpolation_factor here --> dont think so
        area = int(np.round(len(x_pos) * interpolation_factor))

        total_areas.append(area)
        proj_norm = proj / area
        proj_weighted_norm = proj_weighted_dist / area

        pro_data[obj_id] = [proj, proj_weighted_dist, proj_norm, proj_weighted_norm]

    total_forces = np.sum(total_forces)
    total_areas = np.sum(total_areas)
    return pro_data, total_forces, total_areas

def find_areas(line_vecs, mask):

    mid_points = np.array([l[0] + (l[1] - l[0]) / 2 for l in line_vecs]).astype(int)
    distance = distance_transform_edt(mask)
    markers = np.zeros(mask.shape)
    markers[mid_points[:, 0], mid_points[:, 1]] = np.arange(len(mid_points)).astype(int) + 1
    labels = watershed(-distance, markers, mask=mask)

    return labels, distance,  mid_points


def interpolation_single_point(point, shape_target, shape_origin):
    # is also works with 2d arrays of shape(n,2)
    interpol_factors = np.array([shape_target[0] / shape_origin[0], shape_target[1] / shape_origin[1]])
    point_interp = point * interpol_factors
    return point_interp

def get_index_dictionary(labels): # works flawlessly

    d = defaultdict(list)
    for ys in range(labels.shape[0]):
        for xs in range(labels.shape[1]):
            d[labels[ys,xs]].append([ys,xs])
    # converting to arrays, and loosing the zero index
    d2 = {i:np.array(v) for i,v in d.items() if i != 0}

    return d2

def translate_lables_dict(labels, line_ids, mid_points, labels_dict):
    # translating the inidices in the labeled mask (each label represents one object blob) to the clickpoints line id
    translation_dict = {}

    for id, mid in zip(line_ids, mid_points):
        translation_dict[labels[mid[0],mid[1]]] = id

    new_labels_dict = {translation_dict[key]: values for key, values in labels_dict.items()}
    return new_labels_dict


def split_areas(frame, db, target_shape):

    mask = db.getMask(frame=frame).data
    interpolation_factor = np.mean(np.array(mask.shape)/np.array(target_shape))
    line_vecs = np.array([[[l.y1, l.x1], [l.y2, l.x2]] for l in db.getLines(frame=frame, type=line_name)])
    # retrieving the clickpoints line ids to make sure they are consitend
    line_ids = np.array([l.id for l in db.getLines(frame=frame, type=line_name)])#
    # interpolation of the mask to fit vector field shape
    line_vecs = np.array(
        [[interpolation_single_point(l[0], target_shape, mask.shape), interpolation_single_point(l[1], target_shape, mask.shape)]
         for l in line_vecs])
    mask = interpolation(mask, target_shape)
    labels, distances, mid_points = find_areas(line_vecs, mask)


    return  labels, distances, mid_points, line_vecs, line_ids, interpolation_factor # all returned aftr interpolation to target shape

def interpolation(mask, dims, min_cell_size=100, dtype=bool):
    #
    # some pre clean up of the mask
   # mask = remove_small_holes(mask.astype(bool), min_cell_size)
    #mask = remove_small_objects(mask.astype(bool), 1000)  # removing other small bits
    # note: remove_small_objects labels automatically if mask is bool
    coords = np.array(np.where(mask)).astype(float)  # coordinates of all points
    interpol_factors = np.array([dims[0] / mask.shape[0], dims[1] / mask.shape[1]])
    coords[0] = coords[0] * interpol_factors[0]  # interpolating x coordinates
    coords[1] = coords[1] * interpol_factors[1]  # interpolating xy coordinates
    coords = np.round(coords).astype(int)

    coords[0, coords[0] >= dims[0]] = dims[0] - 1  # fixing issue when interpolated object is just at the image border
    coords[1, coords[1] >= dims[1]] = dims[1] - 1

    mask_int = np.zeros(dims)
    mask_int[coords[0], coords[1]] = 1
    mask_int = mask_int.astype(int)
    # filling gaps if we interpolate upwards
    if dims[0] * dims[1] >= mask.shape[0] * mask.shape[1]:
        iter = int(np.ceil(np.max([mask.shape[0] / dims[0], mask.shape[0] / dims[0]])) * 5)  # times 5 is safety factor
        mask_int = binary_closing(mask_int, iterations=10)
        print(iter)
    return mask_int.astype(bool)