#!/bin/bash

APP_PATH="./$1"
# The name of certificates you requested.
APP_KEY="Developer ID Application: Eligijus Kiudys (3Z24U3RF5U)"
INSTALLER_KEY="3rd Party Mac Developer Installer: Eligijus Kiudys (KD96Z4GRH7)"
# The path of your plist files.
CHILD_PLIST="/path/to/child.plist"
PARENT_PLIST="./entitlements.mas.plist"

#array=()
#find . -type f -name "*.so" -print0 > tmpfile
#echo '' > tmpfile

#find $APP_PATH -type f -name "*.so" -print0 >> tmpfile
#find $APP_PATH -type f -name "*.o" -print0 >> tmpfile
#find $APP_PATH -type f -name "*.dylib" -print0 >> tmpfile
#find $APP_PATH -type f -name "*.libitclstub" -print0 >> tmpfile
#find $APP_PATH -type f -name "*.0" -print0 >> tmpfile
#
#while IFS="\n" read -r -d $'\0'; do
#  array+=("$REPLY")
#done < tmpfile
#rm -f tmpfile
#
#count=$((${#array[@]}-1))
#for i in $(seq 0 $count); do
#  libarypath=${array[i]}
##  echo $libarypath
#  codesign -s "$APP_KEY" -f --deep --verbose "$libarypath"
#done
#
#echo $count

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