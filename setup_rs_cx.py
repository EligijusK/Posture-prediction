from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
# build_options = {'packages': [], 'excludes': ['absl-py', 'aiohttp', 'aiosignal', 'altgraph', 'argumentparser', 'async-timeout', 'attrs', 'bidict', 'cchardet', 'certifi', 'cffi', 'charset-normalizer', 'contourpy', 'cryptography', 'cx-Freeze', 'cycler', 'easydict', 'filelock', 'flatbuffers', 'fonttools', 'frozenlist', 'functorch', 'idna', 'installer', 'Jinja2', 'kiwisolver', 'loguru', 'macholib', 'MarkupSafe', 'matplotlib', 'mediapipe', 'modulegraph', 'mpmath', 'multidict', 'netifaces', 'networkx', 'notify-py', 'numpy', 'opencv-contrib-python', 'opencv-python', 'packaging', 'Pillow', 'pip', 'protobuf', 'py2app', 'pybind11', 'pycparser', 'pyinstaller-hooks-contrib', 'pyparsing', 'pyrealsense2', 'python-dateutil', 'python-engineio', 'python-xz', 'PyYAML', 'requests', 'scipy', 'setuptools', 'six', 'sounddevice', 'sympy', 'torch', 'torchaudio', 'torchvision', 'typing_extensions', 'urllib3', 'wheel', 'yarl']}

base = 'console'

DATA_FILES = [('data', ['/Users/eligijus/Desktop/Projektai/Posture-prediction/executable/SitYea/bin/data/label_hierarchy.json'])]

executables = [
    Executable('module_rs.py', base=base),
]

setup(name='modules',
        version = '1.0',
        description = '',
        executables = executables,
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
            )
        )
    )
