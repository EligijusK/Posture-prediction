#!/bin/bash

# Name of your app.
APP_PATH="$2/$1.app"
# The path of your app to sign.
APP_PATH_COMPONENTS="$APP_PATH/Contents/Resources"
FRAMEWORKS_PATH="$APP_PATH/Contents/Frameworks"
# The name of certificates you requested.
APP_KEY="Developer ID Application: Eligijus Kiudys (3Z24U3RF5U)"
INSTALLER_KEY="3rd Party Mac Developer Installer: Eligijus Kiudys (KD96Z4GRH7)"

#cp "/opt/homebrew/opt/xz/lib/liblzma.5.dylib" "${PROJECT_VENV}/lib/python3.10/site-packages/PIL/.dylibs" # liblzma fix

APP_EXECUTABLE_PATHS="$APP_PATH/Contents/MacOS"
APP_PYTHON_EXECUTABLE_PATH="$APP_PATH/Contents/MacOS/python"
APP_RS_EXECUTABLE_PATH="$APP_PATH/Contents/MacOS/module_rs"
APP_MDL_EXECUTABLE_PATH="$APP_PATH/Contents/MacOS/module_mdl"
# The path to the location you want to put the signed package.
#RESULT_PATH="~/Desktop/$APP.pkg"

PARENT_PLIST_CAMERA="./entitlements.camera.mas.plist"
PARENT_PLIST_NO_CAMERA="./entitlements.mas.plist"
PARENT_PLIST="./entitlements.mas.plist"

case $3 in
    "TRUE") PARENT_PLIST=$PARENT_PLIST_CAMERA ;;
    "True") PARENT_PLIST=$PARENT_PLIST_CAMERA ;;
    "true") PARENT_PLIST=$PARENT_PLIST_CAMERA ;;
    "FALSE") PARENT_PLIST=$PARENT_PLIST_NO_CAMERA ;;
    "False") PARENT_PLIST=$PARENT_PLIST_NO_CAMERA ;;
    "false") PARENT_PLIST=$PARENT_PLIST_NO_CAMERA ;;
    *) PARENT_PLIST=$PARENT_PLIST_NO_CAMERA ;;
   esac

echo $3
echo $PARENT_PLIST

# Codesign ZIP -----------------------------------------------------

echo $APP_PATH

export OPTIONS="--verbose --force --timestamp --options=runtime "
export ZIP_NAME="python310.zip"
export ORIGINAL_ZIP_DIR="${APP_PATH}/Contents/Resources/lib"
export PYTHON_ZIP="${ORIGINAL_ZIP_DIR}/${ZIP_NAME}"
export TEMP_DIR="/tmp"
export UNZIP_DIR="python310"
echo "Get copy of unsigned zip file"
cp -p ${PYTHON_ZIP} ${TEMP_DIR}
echo "Unzip it"
/usr/bin/ditto -x -k "${TEMP_DIR}/${ZIP_NAME}" "${TEMP_DIR}/${UNZIP_DIR}"

export PYTHON_UNZIP_DIR=${TEMP_DIR}/${UNZIP_DIR}
find "${PYTHON_UNZIP_DIR}/" -iname '*.dylib' |
 while read libfile; do
   codesign  --sign "${APP_KEY}" "${libfile}" ${OPTIONS} # codesign sign "${IDENTITY}" "${libfile}" ${OPTIONS}
done;

find "${PYTHON_UNZIP_DIR}/" -iname '*.so' |
 while read libfile; do
   codesign  --sign "${APP_KEY}" "${libfile}" ${OPTIONS} # codesign sign "${IDENTITY}" "${libfile}" ${OPTIONS}
done;

echo "Remove old temp copy zip file"
rm -vrf "${TEMP_DIR}/${ZIP_NAME}"
echo "recreate zip file"
/usr/bin/ditto -c -k "${TEMP_DIR}/${UNZIP_DIR}" "${TEMP_DIR}/${ZIP_NAME}"
echo "Move signed zip back"
cp -p "${TEMP_DIR}/${ZIP_NAME}" ${ORIGINAL_ZIP_DIR}

# ------------------------------------------------------------------------

array=()
arrayExe=()

find $APP_PATH_COMPONENTS -type f -name "*.so" -print0 >> tmpfile
find $APP_PATH_COMPONENTS -type f -name "*.o" -print0 >> tmpfile
find $APP_PATH_COMPONENTS -type f -name "*.dylib" -print0 >> tmpfile
find $APP_PATH_COMPONENTS -type f -name "*.libitclstub" -print0 >> tmpfile
find $APP_PATH_COMPONENTS -perm +0111 -type f ! -name "*.sh" ! -name "*.so" ! -name "*.dylib" -print0 >> tempFileExe

find $FRAMEWORKS_PATH -type f -name "*.so" -print0 >> tmpfile
find $FRAMEWORKS_PATH -type f -name "*.o" -print0 >> tmpfile
find $FRAMEWORKS_PATH -type f -name "*.dylib" -print0 >> tmpfile
find $FRAMEWORKS_PATH -type f -name "*.libitclstub" -print0 >> tmpfile
find $FRAMEWORKS_PATH -perm +0111 -type f ! -name "*.sh" ! -name "*.so" ! -name "*.dylib" -print0 >> tempFileExe

find $APP_EXECUTABLE_PATHS -type f ! -name "python" -print0 >> tempFileExeApp

#codesign -s "$APP_KEY" -f --verbose --options=runtime --entitlements "$PARENT_PLIST" "$APP_RS_EXECUTABLE_PATH"
#codesign -s "$APP_KEY" -f --verbose --options=runtime "$APP_MDL_EXECUTABLE_PATH"
while IFS="\n" read -r -d $'\0'; do
  codesign -s "$APP_KEY" -f --verbose --deep --options=runtime --entitlements "$PARENT_PLIST" "$REPLY"
#  codesign -s "$APP_KEY" -f --verbose --deep --options=runtime --entitlements "$PARENT_PLIST_NO_CAMERA" "$REPLY"
done < tempFileExeApp
rm -f tempFileExeApp

while IFS="\n" read -r -d $'\0'; do
#  codesign -s "$APP_KEY" -f --verbose "$REPLY"
  codesign -s "$APP_KEY" -f --verbose --entitlements "$PARENT_PLIST_NO_CAMERA" "$REPLY"
done < tmpfile
rm -f tmpfile

while IFS="\n" read -r -d $'\0'; do
#  codesign -s "$APP_KEY" -f --verbose --options=runtime  "$REPLY"
  codesign -s "$APP_KEY" -f --verbose --options=runtime --entitlements "$PARENT_PLIST_NO_CAMERA" "$REPLY"
done < tempFileExe
rm -f tempFileExe

codesign -s "$APP_KEY" --verbose -f --entitlements "$PARENT_PLIST" "$APP_PATH"
#codesign -s "$APP_KEY" --verbose -f --deep --options=runtime --entitlements "$PARENT_PLIST" "$APP_EXECUTABLE_PATH"
codesign -s "$APP_KEY" --verbose -f --options=runtime --entitlements "$PARENT_PLIST_NO_CAMERA" "$APP_PYTHON_EXECUTABLE_PATH"
echo $count



#productbuild --component "$APP_PATH" /Applications --sign "$INSTALLER_KEY" "$RESULT_PATH"
