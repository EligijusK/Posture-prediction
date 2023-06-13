import os
import shutil
import subprocess
import sys
import torch
import base64
from cryptography.fernet import Fernet
import pickle
import compileall
import py_compile
from app.configs.app_key import encryption_key

out_dir = "executable/SitYEA"
root_path = os.path.realpath("./%s/bin" % out_dir)
# deps_path = os.path.realpath("./%s/dist/deps" % out_dir)
model_path = os.path.realpath("./%s/bin/model" % out_dir)
model_dir = "/home/ratchet/Documents/torch-posture-prediction/output_models/chk_1614151230"
model_type = "model_best_train"

if os.path.exists(model_path):
    shutil.rmtree(model_path)

if os.path.exists(root_path):
    shutil.rmtree(root_path)

# if os.path.exists(deps_path):
#     shutil.rmtree(deps_path)

os.makedirs(root_path, exist_ok=True)
# os.makedirs(deps_path, exist_ok=True)
os.makedirs(model_path, exist_ok=True)

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

    # if out_file.endswith(".py"):
    #     compile_file(out_file)


def make_init(path):
    dir_name = os.path.dirname(path)
    out_dir = "%s/%s" % (root_path, dir_name)
    os.makedirs(out_dir, exist_ok=True)

    out_file = "%s/%s" % (root_path, path)
    cmp_file = out_file.replace(".py", ".pyc")

    with open(out_file, "w") as f:
        pass

    compile_file(out_file)


# def pip_download(package):
#     subprocess.check_call([
#         sys.executable, "-m",
#         "pip", "download", "-r", package,
#         "--platform", "win_amd64",
#         "--python-version", "37",
#         "--only-binary=:all:",
#         "--no-binary=:none:",
#         # "--abi", "none",
#         # "--implementation", "cp"
#         "-d", deps_path
#     ])


def copy_model():
    in_dir = "%s/file_copies/network/models" % model_dir
    os.makedirs("%s/models" % model_path)

    for file in next(os.walk(in_dir))[2]:
        inp_path = "%s/%s" % (in_dir, file)
        out_path = "%s/%s" % ("%s/models" % model_path, file)
        shutil.copy(inp_path, out_path)
        compile_file(out_path)

    # shutil.copytree("%s/file_copies/network/models" %
    #                 model_dir, "%s/models" % model_path)

    state = torch.load("%s/%s.pth" % (model_dir, model_type), map_location="cpu")
    model_weights = state["state_model"]

    for key in model_weights:
        model_weights[key] = model_weights[key].cpu().numpy()

    pickled = pickle.dumps(model_weights)

    fernet = Fernet(encryption_key)
    encrypted = fernet.encrypt(pickled)

    with open("%s/model.xth" % model_path, "wb") as f:
        f.write(encrypted)

    # state = {"state_model": model_weights}
    # torch.save(state, "%s/model.pth" % model_path)

    shutil.copy(
        "%s/file_copies/network/stripped_network.py" % model_dir,
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
        f.write("from .half_points import HalfPoints\n")
        f.write("from .sit_straight import SitStraightNet\n")
        f.write("from .pointnet_feat import PointNetfeat\n")

    compile_file(out_file_init)
    compile_file(out_file_models)


copy_file("app.py")
copy_file("recorder.py")

make_init("configs/__init__.py")
copy_file("configs/config.py")

make_init("utils/__init__.py")
copy_file("utils/image_to_points.py")
copy_file("utils/math.py")
copy_file("utils/get_asset.py")

make_init("rs/__init__.py")
copy_file("rs/config.py")
copy_file("rs/pipeline.py")

make_init("data/__init__.py")
copy_file("data/label_manager.py")
copy_file("data/label_hierarchy.json")

make_init("app/__init__.py")
copy_file("app/note.py")
copy_file("app/config.py")
copy_file("app/realsense.py")
copy_file("app/audio.py")
copy_file("app/notifications.py")
copy_file("app/images.py")
copy_file("app/labels.py")
copy_file("app/model.py")
copy_file("app/frame.py")
copy_file("app/user_interface.py")

make_init("app/configs/__init__.py")
copy_file("app/configs/models.py")
copy_file("app/configs/section.py")
# copy_file("app/configs/sounds.py")
# copy_file("app/configs/notifications.py")
copy_file("app/configs/bad_posture.py")
copy_file("app/configs/take_break.py")
copy_file("app/configs/notification_section.py")
copy_file("app/browser_frame.py")
copy_file("app/configs/history.py")

copy_file("images/background.png")
copy_file("images/ico.png")
copy_file("images/settings.png")
copy_file("images/calibration.png")
copy_file("images/workspace.png")
copy_file("images/exercises.png")
copy_file("images/btn_on.png")
copy_file("images/btn_off.png")
copy_file("images/silhouette.png")
copy_file("ico.ico")
copy_file("compile.py")

copy_model()