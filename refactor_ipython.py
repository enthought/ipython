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
from os.path import join, splitext, normpath
import requests
import glob
import zipfile

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
        resp = requests.get(url)
        resp.raise_for_status()
        f.write(resp.content)

    print 'Extracting the downloaded zip'
    with zipfile.ZipFile(tmp_zip) as z:
        z.extractall(staticDir)
    mathjax_dir = glob.glob(join(staticDir, 'MathJax*'))[0]
    print 'Packing into a zip without the top-level dir'
    shutil.make_archive(zip_path, 'zip', mathjax_dir)
    shutil.rmtree(mathjax_dir)
    os.unlink(tmp_zip)
    
    
# This is no longer in the released endist?
def zip_r(zip_file, dir_path, compress=True, exclude_svn=True):
    """
    Create zip_file which contains the content of the directory dir_path.
    Empty directories are archived by default, i.e. an empty directory will
    be archived as an empty file with the path of the empty directory ending
    with '/'.  Note that only empty directories are archived.  In other words,
    if `archive_empty_dirs` is set to False, or they the directory tree being
    archived contains no empty directories, directory path are not archived
    at all.
    Links are ignored.
    """
    dir_path = normpath(dir_path)

    print 'Creating zip-file %r of dir %r' % (zip_file, dir_path)

    z = zipfile.ZipFile(
             zip_file, 'w',
             [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED][int(bool(compress))])

    ld = len(dir_path)
    for root, dirs, files in os.walk(dir_path):
        if exclude_svn and '.svn' in root.split(os.sep):
            continue
        for f in files:
            absname = join(root, f)
            arcname = absname[ld:].replace(os.sep, '/')
            z.write(absname, arcname)

    z.close()

    
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
        zip_r(egg, tmp)
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
