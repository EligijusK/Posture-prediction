# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

def get_mediapipe_path():
    import mediapipe
    mediapipe_path = mediapipe.__path__[0]
    return mediapipe_path

a = Analysis(['module_mdl.py'],
             pathex=[],
             binaries=None,
             datas=[('/Users/eligijus/Desktop/Projektai/Posture-prediction/executable/SitYea/bin/data/*.json','../../Resources/data')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=True,
)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

mediapipe_tree = Tree(get_mediapipe_path(), prefix='mediapipe', excludes=["*.pyc"])
a.datas += mediapipe_tree
a.binaries = filter(lambda x: 'mediapipe' not in x[0], a.binaries)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='module_mdl',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          argv_emulation=False,
          target_arch=None,
          codesign_identity='Developer ID Application: Eligijus Kiudys (3Z24U3RF5U)',
          entitlements_file='/Users/eligijus/Desktop/Projektai/Posture-prediction/executable/SitYea/entitlements.mas.plist', )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='module_mdl')

app = BUNDLE(coll,
         name='module_mdl.app',
         icon=None,
         bundle_identifier='com.sityea.sityea.module_mdl',
         version='0.4.9',
         info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleName': 'SitYEA',
            'CFBundleDisplayName': 'module_mdl',
            'CFBundleVersion': '0.4.9',
            'CFBundleShortVersionString': '0.4.9',
            'DTSDKName': 'macosx12.3',
            'DTXcode': '1331',
            'DTXcodeBuild': '13E500a',
            'LSHandlerRank': 'Owner'
            }
)