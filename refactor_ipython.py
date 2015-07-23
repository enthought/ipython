#
# This utility refactors the IPython directory structure to reduce the path length.  The
# problem is that Windows has a 260 character path name limit and the combination of
# IPython's long paths when used with Canopy's install path or the Jenkin's build path
# causes headaches.
#

import sys
import os
import shutil
import tempfile
import zipfile
import endist.ziputils
from os.path import join, splitext
import urllib2
import glob

# Phase 1: rename the long image file names.
def reduce_jquery_theme_image_path_length(staticDir):
    """ Renames jquery theme's image files to reduce path length
    """
    jqueryDir = join(staticDir, "jquery-ui", "themes", "smoothness")
    imageDir = join(jqueryDir, 'images')
    images = os.listdir(imageDir)
    jqueryCss = join(jqueryDir, 'jquery-ui.min.css')

    # Read the css file
    with open(jqueryCss) as f:
        css = f.read()

    # Rename each file and change the corresponding css
    for i, image in enumerate(images):
        name = "%02d%s" % (i, splitext(image)[-1])
        print 'Replacing %s with %s' %(image, name)
        css = css.replace(image, name)
        shutil.move(join(imageDir, image), join(imageDir, name))

    # Write back the new css file
    with open(jqueryCss, 'w') as f:
        f.write(css)

# Phase 2: Download and dump the mathjax dir to staticDir
def dump_mathjax_here(staticDir):
    """ Downloads the latest mathjax, cleans it up, and dumps it to staticDir
    """
    zip_path = join(staticDir, 'mathjax')
    tmp_zip = join(staticDir, 'tmp.zip')
    url = 'https://github.com/mathjax/MathJax/archive/2.4.0.zip'

    print 'Downloading and saving %s' % url
    with open(tmp_zip, 'wb') as f:
        SIZE = 1024 * 8
        w = urllib2.urlopen(url)
        while True:
            data = w.read(SIZE)
            if len(data) > 0:
                f.write(data)
            else:
                break

    print 'Extracting the downloaded zip'
    with zipfile.ZipFile(tmp_zip) as z:
        z.extractall(staticDir)
    mathjax_dir = glob.glob(join(staticDir, 'MathJax*'))[0]
    print 'Packing into a zip without the top-level dir'
    shutil.make_archive(zip_path, 'zip', mathjax_dir)
    shutil.rmtree(mathjax_dir)
    os.unlink(tmp_zip)
    
    
    
def do_refactor(egg):
    if not os.path.exists(egg):
        print "Error: egg '{0}' does not exist.".format(egg)
        exit(1)

    # Extract the egg to a temporary location, refactor the tree, then repackage it.
    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(egg) as zf:
            zf.extractall(tmp)
        staticDir = join(tmp, "IPython", "html", "static")
        jqueryDir = join(staticDir, "components")
        reduce_jquery_theme_image_path_length(jqueryDir)
        # Copy the mathjax zip file to this location
        dump_mathjax_here(staticDir)

        # Re-zip the egg.
        shutil.move(egg, egg+".tmp")
        endist.ziputils.zip_r(egg, tmp)
    finally:
        shutil.rmtree(tmp)

    print "Re-wrote egg '{0}', original saved as '{1}'.".format(egg, egg+".tmp")
    
    
    
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print "Usage: refactor_ipython.py <ipython egg>"
        exit(1)
    egg = args[1]
    do_refactor(egg)
