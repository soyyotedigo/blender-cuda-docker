# ==========================
# Dockerfile: Blender + CUDA + Rclone
# ==========================
ARG CUDA_IMAGE_TAG=12.2.0-runtime-ubuntu22.04
FROM nvidia/cuda:${CUDA_IMAGE_TAG}

# Permitir volver a usar los args después del FROM
ARG BLENDER_VERSION=4.5.2
ARG BLENDER_TAR=blender-${BLENDER_VERSION}-linux-x64.tar.xz

ENV DEBIAN_FRONTEND=noninteractive

# Paquetes básicos
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        ca-certificates \
        xz-utils \
        curl \
        unzip \
        fuse \
        libfuse2 \
        libx11-6 \
        libxi6 \
        libxxf86vm1 \
        libxfixes3 \
        libxrender1 \
        libxrandr2 \
        libxinerama1 \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxkbcommon0 \
        libasound2 && \
    rm -rf /var/lib/apt/lists/*


# Instalar rclone
RUN curl https://rclone.org/install.sh | bash

# Directorio de trabajo
WORKDIR /opt

# Descargar e instalar Blender
RUN wget -q https://download.blender.org/release/Blender${BLENDER_VERSION%.*}/${BLENDER_TAR} && \
    tar -xf ${BLENDER_TAR} && \
    rm ${BLENDER_TAR} && \
    ln -s /opt/blender-${BLENDER_VERSION}-linux-x64/blender /usr/local/bin/blender

# Copiar OCIO desde el build context
COPY ocio/ /opt/blender-${BLENDER_VERSION}-linux-x64/4.5/datafiles/colormanagement/

# Entrypoint para crear rclone.conf desde variable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Directorio por defecto
RUN mkdir -p /scenes /output
WORKDIR /scenes

# Vars de entorno útiles
ENV BLENDER_VERSION=${BLENDER_VERSION}
ENV CUDA_VISIBLE_DEVICES=0

ENTRYPOINT ["/entrypoint.sh"]
CMD ["blender", "-v"]

