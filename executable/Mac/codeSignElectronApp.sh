#!/bin/bash

APP="SitYEA"
APP_PATH="./SitYEA/js/$APP.app"
APP_KEY="Developer ID Application: Eligijus Kiudys (3Z24U3RF5U)"

PARENT_PLIST="./entitlements.camera.mac.plist"
PARENT_PLIST_INHERIT="./entitlements.mac.inherit.plist"
FRAMEWORKS_PATH="$APP_PATH/Contents/Frameworks"
NODE_FRAMEWORKS_PATH="$APP_PATH/Contents/Resources/app"

./codesignPyinstaller.sh "modules" $FRAMEWORKS_PATH "true"

find "$FRAMEWORKS_PATH" -maxdepth 1 -type d ! -name "module*.app" -print0 >> tmpFile
find "$NODE_FRAMEWORKS_PATH" -type f -name "*.node" -print0 >> tmpNodeFileExe
find "$NODE_FRAMEWORKS_PATH/node_modules/speaker/build/node_gyp_bins" -type f -perm +0111 -name "*" -print0 >> tmpNodeFileExe

arrayPath=()
while IFS="\n" read -r -d $'\0'; do
  arrayPath+=("$REPLY")
done < tmpFile
rm -f tmpFile

count=$((${#arrayPath[@]}-1))
for i in $(seq 1 $count); do
  libarypath=${arrayPath[i]}
  echo $libarypath
  codesign -s "$APP_KEY" -f --deep --verbose --entitlements "$PARENT_PLIST_INHERIT" "$libarypath"
  find "$libarypath" -type f -name "*.so" -print0 >> tmpFileExe
  find "$libarypath" -type f -name "*.o" -print0 >> tmpFileExe
  find "$libarypath" -type f -name "*.dylib" -print0 >> tmpFileExe
  find "$libarypath" -type f -name "*.libitclstub" -print0 >> tmpFileExe
  find "$libarypath" -perm +0111 -type f ! -name "*.sh" ! -name "*.so" ! -name "*.dylib" -print0 >> tmpFileExeRuntime
done

while IFS="\n" read -r -d $'\0'; do
  codesign -s "$APP_KEY" -f --deep --verbose --options=runtime --entitlements "$PARENT_PLIST_INHERIT" "$REPLY"
done < tmpNodeFileExe
rm -f tmpNodeFileExe

while IFS="\n" read -r -d $'\0'; do
  codesign -s "$APP_KEY" -f --deep --verbose --entitlements "$PARENT_PLIST_INHERIT" "$REPLY"
done < tmpFileExe
rm -f tmpFileExe

while IFS="\n" read -r -d $'\0'; do
  codesign -s "$APP_KEY" -f --deep --verbose --entitlements "$PARENT_PLIST_INHERIT" --options=runtime "$REPLY"
done < tmpFileExeRuntime
rm -f tmpFileExeRuntime

codesign -s "$APP_KEY" -f --entitlements "$PARENT_PLIST" "$APP_PATH"
codesign -s "$APP_KEY" -f --entitlements "$PARENT_PLIST" --options=runtime "$APP_PATH/Contents/MacOS/$APP"

#productbuild --component "$APP_PATH" /Applications --sign "$INSTALLER_KEY" "$RESULT_PATH"
