"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""
import glob
import os
import sys
from setuptools import setup

APP = ['module_rs.py']
APP_NAME = ['module_rs']
DATA_FILES = [('data', ['/Users/eligijus/Desktop/Projektai/Posture-prediction/executable/SitYea/bin/data/label_hierarchy.json'])]
OPTIONS = {
        'argv_emulation': False,
        'iconfile': 'ico.ico',
        'extra-scripts':['module_mdl.py']
}
FRAMEWORKS = []

torch_libs = glob.glob(os.path.join(sys.exec_prefix, '**/libcrypto.3*'), recursive=True)
torch_libs = glob.glob(os.path.join(sys.exec_prefix, '**/libssl.3*'), recursive=True)
FRAMEWORKS += torch_libs

sys.setrecursionlimit(10000)
setup(
    app=APP,
    data_files=DATA_FILES,
    options=dict(py2app=dict(
        plist=dict(
            LSBackgroundOnly=False,
            LSPrefersPPC=False,
            NSCameraUsageDescription='this app requires camera for tracking posture',
            CFBundleName='modules',
            CFBundleDevelopmentRegion='English',
            CFBundleDisplayName='module_rs',
            CFBundleExecutable='module_rs',
            DTSDKName='macosx12.3',
            CFBundleIdentifier='com.sityea.sityea.module_rs',
            CFBundleInfoDictionaryVersion='6.0',
            CFBundlePackageType='APPL',
            CFBundleShortVersionString='0.4.9',
            CFBundleVersion='0.4.9'
        ),
        iconfile='ico.ico',
        argv_emulation=False,
        packages=['mediapipe', 'torch', 'aiohttp', 'torchvision', 'scipy', 'notifypy', 'ArgumentParser', 'OpenSSL'],
        extra_scripts=['module_mdl.py', 'module_notify.py'],
        frameworks=FRAMEWORKS,
        )

    ),

    setup_requires=['py2app'],
)
# pabandyti visiems pritaikyti ta pati entitelment, ir pabandyti pritaikyti sityea kameros entitelment