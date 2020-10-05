import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from contextlib import suppress
from localAlignement.database_functions import check_epty_vector, split_areas
from localAlignement.parameters_and_strings import *
from localAlignement.lines_masks import *
import os
from peewee import DoesNotExist
from peewee import IntegrityError



def display_selections(x, y, frame, db):

    if not check_epty_vector(x, y, frame):
        return


    labels, distances, mid_points, line_vecs, line_ids, interpolation_factor = split_areas(frame, db, x.shape)

    plt.ion()
    fig, ax = show_quiver(x, y, filter=[0,6], plot_cbar=False)
    for id, l,mid in zip(line_ids, line_vecs, mid_points):
        dl= l[1] - l[0]
        ax.arrow(l[0][1],l[0][0],dl[1],dl[0],head_width=3,color="red")
        ax.text(mid[1],mid[0],str(id))

    labels = labels.astype(float)
    labels[labels==0] = np.nan
    im = ax.imshow(labels, alpha=0.8)
    plt.colorbar(im,label="area ID")
    plt.show()
    plt.ioff()


def make_iterable(value):
    if not hasattr(value, '__iter__') or isinstance(value, str):
        return [value]
    else:
        return value


def except_error(func, error, print_error=True, return_v=False, **kwargs):  # take functino and qkwarks
    '''
    wraper to handle errors and return false if the exception is encountered
    :param func:
    :param error:
    :param kwargs:
    :param return_values:
    :return:
    '''

    try:
        values = func(**kwargs)
    except error as e:
        if print_error:
            print(e)
        return return_v
    return values

def create_layers_on_demand(db, layer_list):
    '''
    :param db: clickpointsw database
    :param layer_list: list of layer names that should be created
    :return:
    '''
    layer_list = make_iterable(layer_list)
    base_layer = db.getLayer(id=1)
    for pl in layer_list:
        db.getLayer(pl, base_layer=base_layer, create=True)

def write_image(db, layer, sort_index, filename):
    try:  # deleting all entries that might have been in this sot_index/layer slot
        prev_img = db.getImages(layer=layer, frame=sort_index)
        for im in prev_img:
            db.deleteImages(id=im.id)
    except DoesNotExist:
        pass
    # setting a new image
    except_error(db.setImage, IntegrityError, print_error=True, filename=filename,
                 layer=layer, path=1, sort_index=sort_index)


def add_plot(db, values, frame):
    # values: values (args) that are needed as input for the plotting functions
    fig_shape = db.getImage(frame=frame).getShape()
    create_layers_on_demand(db, [plot_layer])
    plt.ioff()

    filter1 = [0, int(int(np.ceil(values[0].shape[0]/ 50)) * 1)]
    fig, ax = show_quiver(values[0],values[1], filter=filter1, figsize=(fig_shape[1]/200,fig_shape[0]/200))

    # saving the the plot
    file_name = os.path.join(os.path.split(db._database_filename)[0], str(frame).zfill(2) + "vector_field.png")
    fig.savefig(file_name, facecolor=fig.get_facecolor(),
                edgecolor=fig.get_facecolor(), dpi=200)
    plt.close(fig)
    plt.ion()
    # adding the plot to the database
    write_image(db, layer=plot_layer, sort_index=frame, filename=file_name)




def set_vmin_vmax(x, vmin, vmax):
    if not isinstance(vmin, (float, int)):
        vmin = np.nanmin(x)
    if not isinstance(vmax, (float, int)):
        vmax = np.nanmax(x)
    if isinstance(vmax, (float, int)) and not isinstance(vmin, (float, int)):
        vmin = vmax - 1 if vmin > vmax else None
    return vmin, vmax



def show_quiver(fx, fy, filter=[0, 1], scale_ratio=0.2, headwidth=None, headlength=None, headaxislength=None,
                width=None, cmap="rainbow",
                figsize=None, cbar_str="", ax=None, fig=None
                , vmin=None, vmax=None, cbar_axes_fraction=0.2, cbar_tick_label_size=15
                , cbar_width="2%", cbar_height="50%", cbar_borderpad=0.1,
                cbar_style="not-clickpoints", plot_style="not-clickpoints", cbar_title_pad=1, plot_cbar=True, alpha=1,
                ax_origin="upper", filter_method="regular", filter_radius=5, **kwargs):
    # list of all necessary quiver parameters
    quiver_parameters = {"headwidth": headwidth, "headlength": headlength, "headaxislength": headaxislength,
                         "width": width, "scale_units": "xy", "angles": "xy", "scale": None}
    quiver_parameters = {key: value for key, value in quiver_parameters.items() if not value is None}

    fx = fx.astype("float64")
    fy = fy.astype("float64")
    dims = fx.shape  # needed for scaling
    if not isinstance(ax, matplotlib.axes.Axes):
        fig = plt.figure(figsize=figsize)
        ax = plt.axes()
    map_values = np.sqrt(fx ** 2 + fy ** 2)
    vmin, vmax = set_vmin_vmax(map_values, vmin, vmax)
    im = plt.imshow(map_values, cmap=cmap, vmin=vmin, vmax=vmax, alpha=alpha, origin=ax_origin)  # imshowing
    if plot_style == "clickpoints":
        ax.set_position([0, 0, 1, 1])
    ax.set_axis_off()
    # plotting arrows
    # filtering every n-th value and every value smaller then x
    fx, fy, xs, ys = filter_values(fx, fy, abs_filter=filter[0], f_dist=filter[1],filter_method=filter_method, radius=filter_radius)
    if scale_ratio:  # optional custom scaling with the image axis lenght
        fx, fy = scale_for_quiver(fx, fy, dims=dims, scale_ratio=scale_ratio)
        quiver_parameters["scale"] = 1  # disabeling the auto scaling behavior of quiver
    plt.quiver(xs, ys, fx, fy, **quiver_parameters)  # plotting the arrows
    if plot_cbar:
        add_colorbar(vmin, vmax, cmap, ax=ax, cbar_style=cbar_style, cbar_width=cbar_width, cbar_height=cbar_height,
                     cbar_borderpad=cbar_borderpad, v=cbar_tick_label_size, cbar_str=cbar_str,
                     cbar_axes_fraction=cbar_axes_fraction, cbar_title_pad=cbar_title_pad)
    return fig, ax



def filter_values(ar1, ar2, abs_filter=0, f_dist=3, filter_method="regular", radius=5):
    '''
    function to filter out values from an array for better display
    :param ar1:
    :param ar2:
    :param ar:
    :param f_dist: distance betweeen filtered values
    :return:
    '''


    if filter_method == "regular":
        pixx = np.arange(np.shape(ar1)[0])
        pixy = np.arange(np.shape(ar1)[1])
        xv, yv = np.meshgrid(pixy, pixx)

        def_abs = np.sqrt((ar1 ** 2 + ar2 ** 2))
        select_x = ((xv - 1) % f_dist) == 0
        select_y = ((yv - 1) % f_dist) == 0
        select_size = def_abs > abs_filter
        select = select_x * select_y * select_size
        s1 = ar1[select]
        s2 = ar2[select]
        x_ind = xv[select]
        y_ind = yv[select]
    if filter_method == "local_maxima":
        y_ind,x_ind = find_maxima(ar1, ar2, radius=radius,shape="circle")
        s1 = ar1[y_ind, x_ind]
        s2 = ar2[y_ind, x_ind]
    if filter_method == "local_maxima_square":
        y_ind,x_ind = find_maxima(ar1, ar2, radius=radius,shape="square")
        s1 = ar1[y_ind, x_ind]
        s2 = ar2[y_ind, x_ind]
    return s1, s2, x_ind, y_ind

def add_colorbar(vmin, vmax, cmap="rainbow", ax=None, cbar_style="not-clickpoints", cbar_width="2%",
                 cbar_height="50%", cbar_borderpad=0.1, cbar_tick_label_size=15, cbar_str="",
                 cbar_axes_fraction=0.2, shrink=0.8, aspect=20, cbar_title_pad=1, **kwargs):
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    sm = plt.cm.ScalarMappable(cmap=matplotlib.cm.get_cmap(cmap), norm=norm)
    sm.set_array([])  # bug fix for lower matplotlib version
    if cbar_style == "clickpoints":  # colorbar inside of the plot
        cbaxes = inset_axes(ax, width=cbar_width, height=cbar_height, loc=5, borderpad=cbar_borderpad * 30)
        cb0 = plt.colorbar(sm, cax=cbaxes)
        with suppress(TypeError, AttributeError):
            cbaxes.set_title(cbar_str, color="white", pad=cbar_title_pad)
        cbaxes.tick_params(colors="white", labelsize=cbar_tick_label_size)
    else:  # colorbar outide of the plot
        cb0 = plt.colorbar(sm, aspect=aspect, shrink=shrink, fraction=cbar_axes_fraction,
                           pad=cbar_borderpad)  # just exploiting the axis generation by a plt.colorbar
        cb0.outline.set_visible(False)
        cb0.ax.tick_params(labelsize=cbar_tick_label_size)
        with suppress(TypeError, AttributeError):
            cb0.ax.set_title(cbar_str, color="black", pad=cbar_title_pad)
    return cb0



def find_maxima(ar1,ar2,radius=5,shape="circle"):
    # generating circle

    ys,xs = np.indices((radius*2 + 1,radius*2+1))
    xs = (xs - radius).astype(float)
    ys = (ys - radius).astype(float)
    if shape=="circle":
        out = np.sqrt(xs ** 2 + ys ** 2) <= radius
        xs[~out] = np.nan
        ys[~out] = np.nan
    abs = np.sqrt(ar1**2+ar2**2)
    lmax = np.unravel_index(np.nanargmax(abs),shape=abs.shape)
    maxis  = [lmax]
    while True:
        x_exclude = (lmax[1] + xs).flatten()
        y_exclude = (lmax[0] + ys).flatten()
        outside_image = (x_exclude>=abs.shape[1]) | (x_exclude<0) |  (y_exclude>=abs.shape[0]) | (y_exclude<0) | (np.isnan(x_exclude)) | (np.isnan(y_exclude))
        x_exclude = x_exclude[~outside_image]
        y_exclude = y_exclude[~outside_image]
        abs[y_exclude.astype(int),x_exclude.astype(int)] = np.nan
        try:
            lmax = np.unravel_index(np.nanargmax(abs), shape=abs.shape)
        except ValueError:
            break
        maxis.append(lmax)

    maxis_y = [i[0] for i in maxis]
    maxis_x = [i[1] for i in maxis]
    return maxis_y, maxis_x



def scale_for_quiver(ar1, ar2, dims, scale_ratio=0.2, return_scale=False):
    scale = scale_ratio * np.max(dims) / np.nanmax(np.sqrt((ar1) ** 2 + (ar2) ** 2))
    if return_scale:
        return scale
    return ar1 * scale, ar2 * scale
