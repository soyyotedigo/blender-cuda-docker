#!/bin/bash
set -e

# Crear config de rclone desde variable RCLONE_CONF_B64
if [ ! -z "$RCLONE_CONF_B64" ]; then
    mkdir -p /root/.config/rclone
    echo "$RCLONE_CONF_B64" | base64 -d > /root/.config/rclone/rclone.conf
    echo "[INFO] rclone.conf generado desde variable de entorno"
else
    echo "[WARN] No se proporcionó RCLONE_CONF_B64. Rclone no tendrá config."
fi

echo "[INFO] Ejecutando comando: $@"
exec "$@"

