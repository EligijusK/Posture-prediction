import os
import shutil
import subprocess
import sys
import torch
from glob import glob
import base64
import shutil
from cryptography.fernet import Fernet
import pickle
import compileall
import py_compile
from app.configs.app_key import encryption_key
from utils.files import load_json, save_json
import numpy

out_dir = "executable/SitYEA"
root_path = os.path.realpath("./%s/bin" % out_dir)
js_path = os.path.realpath("./%s/js" % out_dir)


model_lst = [["full", "chk_1614151230"], ["simple", "chk_1630345558"]]
model_dir = "/froze_models"
model_type = "model_best_train"

if os.path.exists("model_full"):
    os.unlink("model_full")
if os.path.exists("model_simple"):
    os.unlink("model_simple")

if os.path.exists(root_path):
    shutil.rmtree(root_path)

if os.path.exists(js_path):
    shutil.rmtree(js_path)


def make_commands(app_ver):
    """
    const commandRS = "/home/envs/tensorflow/bin/python module_rs.py";
    const commandMDL = "/home/envs/tensorflow/bin/python module_mdl.py";

    module.exports = { commandRS, commandMDL, commandNotify };
    """
    with open("%s/resources/app/eapp/main/proc-commands.js" % js_path, "w") as f:
        f.write('const { getTrueSettingsPath } = require("./writable-path-utils");\n')
        f.write('const commandRS = [getTrueSettingsPath("./module_rs.exe")];\n')
        f.write('const commandMDL = [getTrueSettingsPath("./module_mdl.exe")];\n\n')
        f.write('const commandNotify = [getTrueSettingsPath("./module_notify.exe")];\n\n')
        f.write('module.exports = { commandRS, commandMDL, commandNotify };\n')

    with open("%s/resources/app/eapp/main/add-reloader.js" % js_path, "w") as f:
        f.write('// This file is not used in production build.\n')

    with open("%s/resources/app/eapp/main/app-version.js" % js_path, "w") as f:
        f.write('module.exports = "%s";\n' % app_ver)

# app_platform, app_arch = "darwin", "arm64"
app_platform, app_arch = "win32", "x64"
app_name = "SitYEA-%s-%s" % (app_platform, app_arch)
# res = subprocess.run("npx electron-packager . SitYEA --derefSymlinks=false --out=executable/SitYEA --appCopyright SitYEA --overwrite --prune=true --platform=%s --arch=%s --icon='ico.ico' --ignore='^((?!(notification.wav|\\node_modules|images|eapp|package|\\.(js|css|html)$)).)+$'" % (app_platform, app_arch), shell=True)
res = subprocess.run("npx electron-packager . SitYEA --derefSymlinks=false --out=executable/SitYEA --appCopyright SitYEA --overwrite --prune=true --platform=%s --arch=%s --icon=ico.ico" % (app_platform, app_arch), shell=True )

res.check_returncode()

shutil.move("executable/SitYEA/%s" % app_name, js_path)

# mac os
# js_path = ("%s/SitYEA.app/Contents" % js_path)

if os.path.exists("%s/resources/app/node_modules/tar/test" % js_path):
    shutil.rmtree("%s/resources/app/node_modules/tar/test" % js_path)

package = load_json("%s/resources/app/package.json" % js_path)
package.homepage = "http://sityea.com"
package.name = "com.sityea"
del package["repository"]
del package["scripts"]
del package["devDependencies"]
save_json("%s/resources/app/package.json" % js_path, package)

make_commands(package.version)
JS_FILES = glob(os.path.join("%s/resources/app" % js_path, "*.js")) + glob(os.path.join("%s/resources/app/eapp/**/" % js_path, "*.js"), recursive=True)

for path in JS_FILES:
    subprocess.run("npx terser %s --compress --mangle --toplevel -o %s" % (path, path), shell=True)

os.makedirs(root_path, exist_ok=True)

def compile_file(file):
    return
    cmp_file = file.replace(".py", ".pyc")
    py_compile.compile(file, cmp_file)

    os.unlink(file)

def copy_file(path):
    dir_name = os.path.dirname(path)
    os.makedirs("%s/%s" % (root_path, dir_name), exist_ok=True)

    out_file = "%s/%s" % (root_path, path)

    shutil.copy(path, "%s/%s" % (root_path, path))

def make_init(path):
    dir_name = os.path.dirname(path)
    out_dir = "%s/%s" % (root_path, dir_name)
    os.makedirs(out_dir, exist_ok=True)

    out_file = "%s/%s" % (root_path, path)
    cmp_file = out_file.replace(".py", ".pyc")

    with open(out_file, "w") as f:
        pass

    compile_file(out_file)

def copy_model(model_name, model_dir):
    in_dir = ".%s/file_copies/network/models" % model_dir
    # in_dir = ".%s/file_copies/network" % model_dir

    model_path = os.path.realpath("./%s/bin/model_%s" % (out_dir, model_name))
    os.symlink(model_path, "model_%s" % model_name)
    if os.path.exists(model_path):
        shutil.rmtree(model_path)
    os.makedirs(model_path, exist_ok=True)

    os.makedirs("%s/models" % model_path)

    datatemp = os.walk(in_dir)

#new
    for (root, dirs, files) in os.walk(in_dir):
        for file in files:
            print(os.path.join(root, file))
            inp_path = "%s/%s" % (in_dir, file)
            out_path = "%s/%s" % ("%s/models" % model_path, file)
            shutil.copy(inp_path, out_path)
            compile_file(out_path)
        break


    # for (root, dirs, files) in os.walk('.', topdown=True):
    #     print(root)
    #     print(dirs)
    #     print(files)
    #     print('--------------------------------')

#old
    # for file in next(os.walk(in_dir)):
    #     inp_path = "%s/%s" % (in_dir, file)
    #     out_path = "%s/%s" % ("%s/models" % model_path, file)
    #     shutil.copy(inp_path, out_path)
    #     compile_file(out_path)

    state = torch.load(".%s/%s.pth" % (model_dir, model_type), map_location="cpu")
    model_weights = state["state_model"]

    for key in model_weights:
        model_weights[key] = model_weights[key].cpu().numpy()

    pickled = pickle.dumps(model_weights)

    fernet = Fernet(encryption_key)
    encrypted = fernet.encrypt(pickled)

    with open("%s/model.xth" % model_path, "wb") as f:
        f.write(encrypted)

    shutil.copy(
        ".%s/file_copies/network/stripped_network.py" % model_dir,
        "%s/stripped_network.py" % model_path
    )

    compile_file("%s/stripped_network.py" % model_path)

    out_file_init = "%s/__init__.py" % model_path
    cmp_file_init = out_file_init.replace(".py", ".pyc")

    with open(out_file_init, "w") as f:
        f.write("from .stripped_network import StrippedNetwork\n")
        f.write("encryption_key=\"%s\"" % encryption_key.decode("utf-8"))

    out_file_models = "%s/models/__init__.py" % model_path
    cmp_file_models = out_file_models.replace(".py", ".pyc")

    with open(out_file_models, "w") as f:
        if model_name == "full":
            f.write("from .half_points import HalfPoints\n")
        f.write("from .sit_straight import SitStraightNet\n")
        f.write("from .pointnet_feat import PointNetfeat\n")

    compile_file(out_file_init)
    compile_file(out_file_models)


copy_file("package.json")
copy_file("module_rs.py")
copy_file("module_mdl.py")
copy_file("module_notify.py")
copy_file("recorder.py")

make_init("utils/__init__.py")
copy_file("utils/files.py")
copy_file("utils/fetch_string.py")
copy_file("utils/image_to_points.py")
copy_file("utils/math.py")
copy_file("utils/mediapipe.py")
copy_file("utils/skeleton.py")
copy_file("utils/get_asset.py")
copy_file("utils/fetch_cameras.py")

copy_file("app/win_notify.py")

make_init("rs/__init__.py")
copy_file("rs/config.py")
copy_file("rs/pipeline.py")
copy_file("rs/exceptions.py")

make_init("data/__init__.py")
copy_file("data/label_manager.py")
copy_file("data/label_hierarchy.json")

make_init("configs/__init__.py")
copy_file("configs/config.py")

copy_file("ico.ico")
copy_file("compile.py")
copy_file("certificate.pfx")
copy_file("small.ism.json")

copy_file("AppxManifest.xml")
copy_file("Assets/SitYEA-AppList.png")
copy_file("Assets/SitYEA-MedTile.png")
copy_file("Assets/StoreLogo.png")

shutil.copy("installer.nsi", "%s/installer.nsi" % out_dir)
shutil.copy("SitYEA-install.ism", "%s/SitYEA-install.ism" % out_dir)
shutil.copytree("./win_libs", "%s/win_libs" % root_path)

[copy_model(name, "%s/%s" % (model_dir, mdl)) for name, mdl in model_lst]