import numpy as np
import matplotlib.pyplot as plt
import clickpoints
import os
def identify_block_type(line, ltype):

    if line.startswith("total force"):
        ltype = "header"
    if line.startswith("frame"):
        ltype = "main vector"
    if line.startswith("pos_x"):
        ltype = "sourrounding field"
    if line.startswith("projected force"):
        ltype = "summary"

    try:
        int(line[0])
        values = True
    except:
        values = False
    return ltype, values

main_vec_fields = ["frame", "id", "middle_x", "middle_y", "vecx", "vecy", "p1x", "p1y", "p2x", "p2y"]
vec_field_fields = ["pos_x", "pos_y", "vec_x", "vec_y", "dist_to_line", "angles"]

def parse_line(line, ltype, frame_id, header, main_vec, field):
    l = [float(x) for x in line.strip().split(", ")]
    if ltype == "header":
        header["total force"] = l[0]
        header["total area"] = l[1]
    if ltype == "sourrounding field":
        field[frame_id].append(l)
    if ltype == "main vector":
        frame_id = tuple(l[:2])
        main_vec[frame_id] = {key: value for key, value in zip(main_vec_fields,l)}

    return frame_id

from collections import defaultdict
def read_file(file):
    header = {}
    main_vec = {}
    field = defaultdict(list)
    with open(file,"r") as f:
        ltype = "header"
        frame_id = (0, 0)
        for line in f.readlines():

            ltype, values = identify_block_type(line, ltype)
            if values:
                frame_id = parse_line(line, ltype, frame_id, header, main_vec, field)
            else:
                continue
    return header, main_vec, field


def get_angles(main_vec, field, dist_weighted=False):
    angles = []
    for cid in main_vec.keys():
        frame = cid[0]
        dmain = main_vec[cid]
        cvx, cvy, vx, vy = dmain["middle_x"], dmain["middle_y"], dmain["vecx"], dmain["vecy"]
        v = np.array([vx, vy])
        xy = np.array(field[cid])[:, [0, 1]]
        vec_xy = np.array(field[cid])[:, [2, 3]]

        scalar_products = np.abs(np.sum(v * vec_xy, axis=1))
        lv = np.linalg.norm(v)
        l_vecs = np.linalg.norm(vec_xy, axis=1)
        scalar_products = scalar_products / (lv * l_vecs)

        if dist_weighted:
            dist = np.array(field[cid])[:, 4]
            sc = np.mean(scalar_products * dist / np.sum(dist))
        else:
            sc = np.mean(scalar_products)

        angle = np.rad2deg(np.arccos(sc))
        angles.append([frame, cvx, cvy, angle])
    return angles

def get_angles_from_file(file, db):
    #file = "/home/andreas/Software/localAlignement/test_data/KO_analyzed/out.txt"
    out_put = os.path.join(os.path.split(file)[0],  "angles_"+ os.path.split(file)[1])

    header, main_vec, field = read_file(file)
    angles = get_angles(main_vec, field, dist_weighted=False)

    with open(out_put, "w") as f:
        f.write("frame, center_x, center_y, angle\n")
        for l in angles:
            f.write(", ".join([str(x) for x in l]) + "\n")
    db.deleteMarkerTypes(["angles"])
    mtype = db.setMarkerType("angles", color="#00FF00")
    for angle in angles:
        db.setMarker(type=mtype, frame=angle[0], x=angle[1], y=angle[2], text="angel = " + str(np.round(angle[3], 2)))

if __name__ == "main":
    file = "/home/andreas/Software/localAlignement/test_data/KO_analyzed/out.txt"
    out_put = "/home/andreas/Software/localAlignement/test_data/KO_analyzed/angles.txt"

    header, main_vec, field = read_file(file)
    angles = get_angles(main_vec, field, dist_weighted=False)

    with open(out_put, "w") as f:
        f.write("frame, center_x, center_y, angle\n")
        for l in angles:
            f.write(", ".join([str(x) for x in l]) + "\n")

    # display in database:
    db = clickpoints.DataFile("/home/andreas/Software/localAlignement/test_data/KO_analyzed/database.cdb")
    db.deleteMarkerTypes(["angles"])
    mtype = db.setMarkerType("angles", color="#00FF00")
    for angle in angles:
        db.setMarker(type=mtype,frame=angle[0], x=angle[1], y=angle[2], text="angel = " + str(np.round(angle[3],2)))
    db.db.close()