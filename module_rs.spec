# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['module_rs.py'],
             pathex=[],
             binaries=None,
             datas=[('/Users/eligijus/Desktop/Projektai/Posture-prediction/executable/SitYea/bin/data/*.json','data')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

a2 = Analysis(['module_mdl.py'],
             pathex=[],
             binaries=None,
             datas=[('env/lib/python3.10/site-packages/mediapipe/modules', 'mediapipe/modules'),],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False,
)

pyz2 = PYZ(a2.pure, a2.zipped_data,
             cipher=block_cipher)

a3 = Analysis(['module_notify.py'],
             pathex=[],
             binaries=None,
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False,
)

pyz3 = PYZ(a3.pure, a3.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='module_rs',
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

exe2 = EXE(pyz2,
          a2.scripts,
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

exe3 = EXE(pyz3,
          a3.scripts,
          exclude_binaries=True,
          name='module_notify',
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
               exe2,
               exe3,
               a.binaries,
               a.zipfiles,
               a.datas,
               a2.binaries,
               a2.zipfiles,
               a2.datas,
               a3.binaries,
               a3.zipfiles,
               a3.datas,
               strip=False,
               upx=True,
               name='modules')

app = BUNDLE(coll,
         name='modules.app',
         icon=None,
         bundle_identifier='com.sityea.sityea.modules',
         version='0.4.9',
         info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleName': 'SitYEA',
            'CFBundleDisplayName': 'modules',
            'CFBundleVersion': '0.4.9',
            'CFBundleShortVersionString': '0.4.9',
            'DTSDKName': 'macosx12.3',
            'DTXcode': '1331',
            'DTXcodeBuild': '13E500a',
            'LSHandlerRank': 'Owner'
            }
)