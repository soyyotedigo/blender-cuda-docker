# Vast.ai Render Manager for Blender

Este proyecto es una herramienta de interfaz gráfica (GUI) para gestionar el alquiler de instancias GPU en Vast.ai y orquestar renderizado distribuido con Blender.

## Características

- **Búsqueda de Instancias**: Filtra por GPU, precio, espacio en disco, región y versión de CUDA.
- **Alquiler Simplificado**: Alquila máquinas con un solo clic usando una imagen de Docker configurada.
- **Render Distribuido**: Divide automáticamente el rango de frames entre múltiples instancias seleccionadas.
- **Gestión de Instancias**:
    - Ver instancias activas.
    - Conectar vía SSH (abre terminal automáticamente).
    - Destruir instancias.
- **Configuración de Entorno**: Pasa automáticamente variables de entorno para Rclone, archivos de escena y configuración de render.

## Requisitos

- Windows (probado en Windows 10/11).
- Python 3.10+.
- [Vast.ai CLI](https://vast.ai/docs/cli/installation) instalado y configurado en el PATH.
- `ssh` instalado y disponible en el PATH (OpenSSH Client).

## Instalación

1.  Clonar el repositorio.
2.  Instalar dependencias:
    ```bash
    pip install PySide2
    ```
3.  Asegurarse de tener `vastai` instalado:
    ```bash
    pip install vastai
    ```

## Uso

1.  Ejecutar la aplicación:
    ```bash
    python ui/main.py
    ```
2.  **Pestaña Buscar**:
    - Configura los filtros y haz clic en "Buscar Disponibles".
    - Selecciona una o más instancias.
    - Configura los parámetros de render (Imagen, Escena, Frames).
    - Haz clic en "ALQUILAR". Si seleccionas múltiples, los frames se dividirán equitativamente.
3.  **Pestaña Instancias**:
    - Ve el estado de tus máquinas alquiladas.
    - Click derecho para conectar por SSH o destruir la instancia.

## Estructura del Proyecto

- `ui/main.py`: Punto de entrada.
- `ui/mvc/`: Arquitectura Model-View-Controller.
    - `views/`: Interfaz gráfica (Qt).
    - `controllers/`: Lógica de control.
    - `models/`: Lógica de negocio e interacción con Vast.ai CLI.
