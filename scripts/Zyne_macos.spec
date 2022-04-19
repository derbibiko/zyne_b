# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

a = Analysis(['../Zyne.py'],
             pathex=[],
             binaries=[],
             datas=[('../Resources', 'Resources')],
             hiddenimports=['wx._xml'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Zyne_B',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='../Resources/zyneicon.icns')
app = BUNDLE(exe,
             name='Zyne_B.app',
             icon='../Resources/zyneicon.icns',
             bundle_identifier='org.pythonmac.bibiko.Zyne_B',
             version='1.0.1',
             info_plist={
                        'NSHumanReadableCopyright': '(c) 2022 Olivier Bélanger\nHans-Jörg Bibiko',
                        'NSPrincipalClass': 'NSApplication',
                        'NSMainNibFile': 'MainMenu',
                        'CFBundleDisplayName': 'Zyne_B',
                        'CFBundleName': 'Zyne_B',
                        'CFBundleDevelopmentRegion': 'English',
                        'CFBundleDocumentTypes': [
                            {
                              'CFBundleTypeExtensions': ['zy'],
                              'CFBundleTypeOSTypes': ['TEXT'],
                              'CFBundleTypeIconFile': 'zyneiconDoc.icns',
                              'CFBundleTypeRole': 'Editor',
                              'LSIsAppleDefaultForType': False
                            }
                        ]
               })
