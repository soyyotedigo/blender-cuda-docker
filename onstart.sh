#!/bin/bash
set -e

echo "[INFO] Generando rclone.conf desde RCLONE_CONF_B64..."
mkdir -p /root/.config/rclone
echo "$RCLONE_CONF_B64" | base64 -d > /root/.config/rclone/rclone.conf

# Parámetros por ENV (con defaults)
SCENE_REMOTE="${SCENE_REMOTE:-drive:escenas/test}"          # carpeta en Drive con la escena
SCENE_FILE="${SCENE_FILE:-escena.blend}"                     # archivo .blend
OUTPUT_REMOTE="${OUTPUT_REMOTE:-drive:renders/test}"        # carpeta en Drive para los renders
START_FRAME="${START_FRAME:-1}"                              # frame inicio
END_FRAME="${END_FRAME:-250}"                                # frame final

LOCAL_SCENE_DIR="/mnt/data/scene"
LOCAL_OUTPUT_DIR="/mnt/data/output"

echo "[INFO] SCENE_REMOTE = $SCENE_REMOTE"
echo "[INFO] SCENE_FILE   = $SCENE_FILE"
echo "[INFO] OUTPUT_REMOTE= $OUTPUT_REMOTE"
echo "[INFO] START_FRAME  = $START_FRAME"
echo "[INFO] END_FRAME    = $END_FRAME"

echo "[INFO] Bajando escena desde Drive..."
mkdir -p "$LOCAL_SCENE_DIR"
rclone copy "$SCENE_REMOTE" "$LOCAL_SCENE_DIR" -P --drive-team-drive=0ANBdOnuvcZHsUk9PVA

echo "[INFO] Contenido en $LOCAL_SCENE_DIR:"
ls -la "$LOCAL_SCENE_DIR"

echo "[INFO] Tirando render con Blender..."
mkdir -p "$LOCAL_OUTPUT_DIR"

/usr/local/bin/blender -b "$LOCAL_SCENE_DIR/$SCENE_FILE" \
  -o "$LOCAL_OUTPUT_DIR/frame_####" \
  -s "$START_FRAME" -e "$END_FRAME" -a

echo "[INFO] Render terminado. Subiendo a Drive..."
rclone copy "$LOCAL_OUTPUT_DIR" "$OUTPUT_REMOTE" -P --drive-team-drive=0ANBdOnuvcZHsUk9PVA

echo "[INFO] Listo. Archivos en $OUTPUT_REMOTE"