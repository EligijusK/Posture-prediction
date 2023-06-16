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

dir_winsdk = "C:/Program Files (x86)/Windows Kits/10/bin/10.0.19041.0/x64"
ishield_build = "C:/Program Files (x86)/InstallShield/2020/System/IsCmdBld.exe"
sign_tool = "%s/signtool.exe" % dir_winsdk
makeappx = "%s/makeappx.exe" % dir_winsdk
cert_path = "./certificate.pfx"
cert_pass = None
archive_files, copy_files = False, True # last one was false
build_version = load_json("package.json")["version"] + ".0"

root_dir = os.path.realpath(os.path.dirname(__file__))
build_dir = os.path.abspath("%s/../build" % root_dir)

CEF_INCLUDES = []
# cefPath = os.path.join(get_python_lib(), "cefpython3")
# CEF_INCLUDES = glob(os.path.join(cefPath, "*"))
# CEF_INCLUDES.remove(os.path.join(cefPath, "examples"))

torchPath = os.path.join(get_python_lib(), "torch")
TORCH_INCLUDES = [(path, path.replace(torchPath, "./lib/torch"))
                  for path in glob(os.path.join(torchPath, "*"))]

winrtPath = os.path.join(get_python_lib(), "winrt")
WINRT_INCLUDES = [(path, path.replace(winrtPath, "./lib/winrt"))
                  for path in glob(os.path.join(winrtPath, "*"))]

cryptoPath = os.path.join("%s/win_libs", "cryptography")
CRYPTO_INCLUDES = [(path, path.replace(cryptoPath, "./lib/cryptography"))
                   for path in glob(os.path.join(cryptoPath, "*"))]

include_libs = CEF_INCLUDES + TORCH_INCLUDES + WINRT_INCLUDES + CRYPTO_INCLUDES
include_files = [
    ("%s/model_full/model.xth" % root_dir, "./model_full/model.xth"),
    ("%s/model_simple/model.xth" % root_dir, "./model_simple/model.xth"),
    ("%s/data/label_hierarchy.json" % root_dir, "./data/label_hierarchy.json"),
]

includes = []
excludes = []
packages = []
executables = {
    # "recorder.exe": Executable(
    #     script="%s/recorder.py" % root_dir,
    #     target_name="recorder.exe",
    #     base="Win32GUI"
    # ),
    "module_mdl.exe": Executable(
        script="%s/module_mdl.py" % root_dir,
        # icon="%s/ico.ico" % root_dir,
        target_name="module_mdl.exe",
        # base="Win32GUI"
    ),
    "module_rs.exe": Executable(
        script="%s/module_rs.py" % root_dir,
        # icon="%s/ico.ico" % root_dir,
        target_name="module_rs.exe",
        # base="Win32GUI"
    ),
    "module_notify.exe": Executable(
        script="%s/module_notify.py" % root_dir,
        # icon="%s/ico.ico" % root_dir,
        target_name="module_notify.exe",
        # base="Win32GUI"
    ),
}


def sign_exe(signable):
    path = os.path.realpath("%s/%s" % (build_dir, signable))

    args = [
        "\"%s\"" % sign_tool,
        "sign",
        "/debug",
        "/f",
        "\"%s\"" % os.path.realpath(cert_path),
        "/t",
        "http://timestamp.digicert.com",
        *([
            "/p",
            cert_pass
        ] if cert_pass is not None else []),
        "/fd",
        "SHA256",
        "\"%s\"" % path,
    ]

    proc_string = " ".join(args)
    print(f"Signing '{path} with '{os.path.realpath(cert_path)}''")
    subprocess.run(proc_string, shell=True).check_returncode()


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


if os.path.exists(build_dir):
    shutil.rmtree(build_dir)

setup(
    name="SitYEA",
    version=build_version,
    description="SitYEA",
    options={
        "build_exe": {
            "build_exe": "%s/python_modules" % (build_dir) if copy_files and not archive_files else build_dir,
            "includes": includes, "excludes": excludes,
            "packages": packages, "include_files": include_libs + include_files,
            "include_msvcr": True
        }
    },
    executables=[e for e in executables.values()]
)

[sign_exe("python_modules/%s" % p if copy_files and not archive_files else p) for p in executables.keys()]

if archive_files:
    print("Compiled python binaries, packaging python into archive...")
    python_modules_path = "%s/python_modules.bin" % build_dir

    if os.path.exists(python_modules_path):
        os.unlink(python_modules_path)

    cwd = os.getcwd()
    os.chdir(build_dir)
    dir_list, file_list = get_all_files()

    with ZipFile(python_modules_path, "w", compression=ZIP_DEFLATED) as archive:
        for fpath in tqdm(file_list):
            if not os.path.exists(fpath) or os.path.isdir(fpath):
                continue
            archive.write(fpath)
            os.unlink(fpath)

    for dpath in dir_list:
        if not os.path.exists(dpath) or not os.path.isdir(dpath):
            continue
        os.rmdir(dpath)

    os.chdir(cwd)
else:
    print("Compiled python binaries.")

print("Installing numpy packages...")

tmp_dir = os.path.realpath("%s/../../tmp")

os.makedirs(tmp_dir, exist_ok=True)

with open("%s/package.json" % tmp_dir, "w") as f:
    modules = {
        "name": "winPackages",
        "version": "1.0.0",
        "description": "",
        "main": "index.js",
        "scripts": {
            "rebuild-mmap": "electron-rebuild ./node_modules/@raygun-nickj/mmap-io/",
            "rebuild-sound": "electron-rebuild ./node_modules/speaker/"
        },
        "keywords": [],
        "author": "",
        "license": "ISC",
        "dependencies": {
            "@raygun-nickj/mmap-io": "1.2.3",
            "speaker": "0.5.3"
        },
        "devDependencies": {
            "electron": "^23.1.4",
            "@electron/rebuild": "^3.2.13",
        }
    }

    json.dump(modules, f)

cwd = os.getcwd()
os.chdir(tmp_dir)

subprocess.run("npm install --ignore-scripts", shell=True).check_returncode()
subprocess.run("npm install node-pre-gyp", shell=True).check_returncode()
subprocess.run("npm run rebuild-mmap", shell=True).check_returncode()
subprocess.run("npm run rebuild-sound", shell=True).check_returncode()

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


copy_dir("../js", build_dir)
copy_dir("./node_modules/@raygun-nickj/mmap-io/",
         "%s/resources/app/node_modules/@raygun-nickj/mmap-io/" % build_dir)
copy_dir("./node_modules/speaker/",
         "%s/resources/app/node_modules/speaker/" % build_dir)
copy_dir("../bin/Assets", "%s/Assets" % build_dir)

os.chdir(cwd)

sign_exe("SitYEA.exe")

if os.path.exists("../MsixPackage"):
    shutil.rmtree("../MsixPackage")
os.mkdir("../MsixPackage")

with open(os.path.join(os.path.realpath("./AppxManifest.xml")), "r") as f:
    lines = f.readlines()
    lines = "".join(lines)

    lines = lines.replace("@__PUBLISHER__@", "CN=7D066D12-9EC9-4F0C-9F36-C32195B5FB92")
    lines = lines.replace("@__VERSION__@", build_version)

with open(os.path.join(os.path.realpath("%s/AppxManifest.xml" % build_dir)), "w") as f:
    f.write(lines)

subprocess.run(
    "\"%s\" pack /v /h SHA256 /p ../MsixPackage/SitYEA-install_%s_x64_store.msix /d ../build" % (makeappx, build_version), shell=True).check_returncode()

with open(os.path.join(os.path.realpath("./AppxManifest.xml")), "r") as f:
    lines = f.readlines()
    lines = "".join(lines)

    lines = lines.replace("@__PUBLISHER__@", "CN=UAB SitYEA, O=UAB SitYEA, S=Kaunas, C=LT")
    lines = lines.replace("@__VERSION__@", build_version)

with open(os.path.join(os.path.realpath("%s/AppxManifest.xml" % build_dir)), "w") as f:
    f.write(lines)

subprocess.run(
    "\"%s\" pack /v /h SHA256 /p ../MsixPackage/SitYEA-install_%s_x64.msix /d ../build" % (makeappx, build_version), shell=True).check_returncode()

sign_exe("../MsixPackage/SitYEA-install_%s_x64.msix" % build_version)
