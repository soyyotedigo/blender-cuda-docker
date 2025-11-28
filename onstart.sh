#!/bin/bash
set -e

echo "[INFO] Generating rclone.conf from RCLONE_CONF_B64..."
mkdir -p /root/.config/rclone
echo "$RCLONE_CONF_B64" | base64 -d > /root/.config/rclone/rclone.conf

# Parameters from ENV (with defaults)
SCENE_REMOTE="${SCENE_REMOTE:-drive:escenas/test}"          # folder in Drive with the scene
SCENE_FILE="${SCENE_FILE:-escena.blend}"                     # .blend file
OUTPUT_REMOTE="${OUTPUT_REMOTE:-drive:renders/test}"        # folder in Drive for renders
START_FRAME="${START_FRAME:-1}"                              # start frame
END_FRAME="${END_FRAME:-250}"                                # end frame

LOCAL_SCENE_DIR="/mnt/data/scene"
LOCAL_OUTPUT_DIR="/mnt/data/output"

echo "[INFO] SCENE_REMOTE = $SCENE_REMOTE"
echo "[INFO] SCENE_FILE   = $SCENE_FILE"
echo "[INFO] OUTPUT_REMOTE= $OUTPUT_REMOTE"
echo "[INFO] START_FRAME  = $START_FRAME"
echo "[INFO] END_FRAME    = $END_FRAME"

echo "[INFO] Downloading scene from Drive..."
mkdir -p "$LOCAL_SCENE_DIR"
rclone copy "$SCENE_REMOTE" "$LOCAL_SCENE_DIR" -P --drive-team-drive=0ANBdOnuvcZHsUk9PVA

echo "[INFO] Contents in $LOCAL_SCENE_DIR:"
ls -la "$LOCAL_SCENE_DIR"

echo "[INFO] Starting render with Blender..."
mkdir -p "$LOCAL_OUTPUT_DIR"

/usr/local/bin/blender -b "$LOCAL_SCENE_DIR/$SCENE_FILE" \
  -o "$LOCAL_OUTPUT_DIR/frame_####" \
  -s "$START_FRAME" -e "$END_FRAME" -a

echo "[INFO] Render finished. Uploading to Drive..."
rclone copy "$LOCAL_OUTPUT_DIR" "$OUTPUT_REMOTE" -P --drive-team-drive=0ANBdOnuvcZHsUk9PVA

echo "[INFO] Done. Files in $OUTPUT_REMOTE"