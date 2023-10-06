APP_NAME="SitYEA"
DMG_FILE_NAME="${APP_NAME}-Installer.dmg"
VOLUME_NAME="${APP_NAME} Installer"
SOURCE_FOLDER_PATH="/Users/eligijus/Desktop/SitYEA/"

if [[ -e ../../create-dmg ]]; then
  # We're running from the repo
  CREATE_DMG=../../create-dmg
else
  # We're running from an installation under a prefix
  CREATE_DMG=../../../../bin/create-dmg
fi

# Since create-dmg does not clobber, be sure to delete previous DMG
[[ -f "${DMG_FILE_NAME}" ]] && rm "${DMG_FILE_NAME}"

# Create the DMG
create-dmg \
  --volname "${VOLUME_NAME}" \
  --background "./images/Background_SitYEA.png" \
  --window-pos 200 120 \
  --window-size 400 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 200 190 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 600 185 \
  "${DMG_FILE_NAME}" \
  "${SOURCE_FOLDER_PATH}"