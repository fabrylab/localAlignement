# contains the default parameters, parameters for plotting, messages that are printed while the programming is executed
# and tooltips for the tfm addon
import re
from collections import defaultdict
import numpy as np


tooltips = defaultdict(lambda: "")
tooltips["button_start"] = "Start the calculation"

# could make options to read external config files in the addon and in normal applications.)
line_color = "#f3ff0a" # markertype color in the clickpoints database
mask_name ="ROI"
line_name = "SingleFibre"
mask_color = "#30ff0c"

allowed_vf_endings = [".npy"]
plot_layer ="vector field"