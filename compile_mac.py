import re
import os
import sys
import json
import shutil
import subprocess
from tqdm import tqdm
from glob import glob
from utils.files import load_json
from cx_Freeze import setup, Executable
from itertools import chain as iterchain
from zipfile import ZipFile, ZIP_DEFLATED
from distutils.sysconfig import get_python_lib

cert_pass = None
archive_files, copy_files = False, True # last one was false
build_version = load_json("package.json")["version"] + ".0"
app_name = "ChainHealth AI.app"
root_dir_mdl = os.path.realpath(os.path.dirname(__file__))
build_dir = os.path.abspath("%s/../build" % root_dir_mdl)
build_dir_mdl = os.path.abspath("%s/../build" % root_dir_mdl)

CEF_INCLUDES = []

# include_files = [
#     ("%s/model_full/model.xth" % root_dir, "./model_full/model.xth"),
#     ("%s/model_simple/model.xth" % root_dir, "./model_simple/model.xth"),
#     ("%s/data/label_hierarchy.json" % root_dir, "./data/label_hierarchy.json"),
# ]


def get_all_files(dirname=".", dirs=None, files=None):
    dirs = [] if dirs == None else dirs
    files = [] if files == None else files

    _, d_dirnames, d_files = next(os.walk(dirname))
    [files.append("%s/%s" % (dirname, f)) for f in d_files]
    for d in d_dirnames:
        dname = "%s/%s" % (dirname, d)
        get_all_files(dname, dirs, files)
        dirs.append(dname)

    return dirs, files

print("Installing numpy packages...")

tmp_dir = os.path.realpath("%s/../../tmp")

os.makedirs(tmp_dir, exist_ok=True)

cwd = os.getcwd()

print("Copying files...")

def copy_dir(src_dir, dst_dir):
    src_dir, dst_dir = [os.path.realpath(p) for p in [src_dir, dst_dir]]
    print("Copying '%s' -> '%s'" % (src_dir, dst_dir))

    cwd = os.getcwd()
    os.chdir(src_dir)

    REL_JS_FILES = [os.path.relpath(f) for f in get_all_files()[1]]
    ABS_JS_FILES = [os.path.realpath(f) for f in REL_JS_FILES]
    DST_JS_FILES = [os.path.realpath("%s/%s" % (dst_dir, f))
                    for f in REL_JS_FILES]
    FROM_TO_LIST = zip(ABS_JS_FILES, DST_JS_FILES)

    for src, dst in tqdm(FROM_TO_LIST, total=len(REL_JS_FILES)):
        dirname = os.path.dirname(dst)
        os.makedirs(dirname, exist_ok=True)

        if os.path.exists(dst):
            os.unlink(dst)
        shutil.copy(src, dst)
    os.chdir(cwd)

def copy_file(src_dir, file_name, dst_dir):
    src_dir, dst_dir = [os.path.realpath(p) for p in [src_dir, dst_dir]]
    print("Copying '%s' -> '%s'" % (src_dir, dst_dir))

    cwd = os.getcwd()
    os.chdir(src_dir)

    REL_JS_FILES = [os.path.relpath(f) for f in get_all_files()[1]]
    ABS_JS_FILES = [os.path.realpath(f) for f in REL_JS_FILES]
    DST_JS_FILES = [os.path.realpath("%s/%s" % (dst_dir, f))
                    for f in REL_JS_FILES]
    FROM_TO_LIST = zip(ABS_JS_FILES, DST_JS_FILES, REL_JS_FILES)

    for src, dst, file in tqdm(FROM_TO_LIST, total=1):
        dirname = os.path.dirname(dst)
        os.makedirs(dirname, exist_ok=True)

        if os.path.exists(dst):
            os.unlink(dst)
        if file_name == file:
            shutil.copy(src, dst)
            break
    os.chdir(cwd)


copy_dir("../js", build_dir)
build_dir_modules = build_dir + "/" + app_name + "/Contents/Frameworks/"
build_dir_app = build_dir + "/" + app_name + "/"
copy_dir("../module_rs.app", build_dir_modules + "/module_rs.app")
copy_dir("../module_notify.app", build_dir_modules + "/module_notify.app")
copy_dir("../module_mdl.app", build_dir_modules + "/module_mdl.app")
copy_file("./data/", "label_hierarchy.json", build_dir_modules + "/module_mdl.app/Contents/Resources/data/")
copy_file("./model_full/", "model.xth", build_dir_app + "/Contents/MacOS/model_full/")
copy_file("./model_simple/", "model.xth", build_dir_app + "/Contents/MacOS/model_simple/")
# copy_dir("./node_modules/@raygun-nickj/mmap-io/",
#          "%s/resources/app/node_modules/@raygun-nickj/mmap-io/" % build_dir)
# copy_dir("./node_modules/speaker/",
#          "%s/resources/app/node_modules/speaker/" % build_dir)

# copy_dir("../bin/Assets", "%s/Assets" % build_dir)

os.chdir(cwd)


