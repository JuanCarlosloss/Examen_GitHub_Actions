#!/usr/bin/env bash

# Script para automatizar la instalación y configuración del runner self-hosted de GitHub Actions
# para el repositorio: https://github.com/JuanCarlosloss/GitHub_Actions

set -euo pipefail

RUNNER_VERSION="2.321.0"
RUNNER_DIR="/home/jchrisso/actions-runner"
REPO_URL="https://github.com/JuanCarlosloss/GitHub_Actions"
LABELS="custom-runner-lab5,self-hosted,linux,x64"
RUNNER_NAME="local-runner-lab5"

echo "========================================================="
echo " Configuración del Self-Hosted Runner — Laboratorio 5"
echo "========================================================="

# Solicitar el Token de Registro si no se pasa como variable de entorno o argumento
TOKEN="${1:-${RUNNER_TOKEN:-}}"

if [ -z "$TOKEN" ]; then
    echo "⚠️  No se ha proporcionado un token de registro."
    echo "Por favor, consíguelo en tu repositorio GitHub:"
    echo "   Settings -> Actions -> Runners -> New self-hosted runner"
    echo ""
    read -r -p "Introduce el token de registro de GitHub Actions: " TOKEN
fi

if [ -z "$TOKEN" ]; then
    echo "❌ Error: El token no puede estar vacío."
    exit 1
fi

# Crear directorio para el runner
echo "--> Creando directorio de instalación en: $RUNNER_DIR"
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Descargar el paquete del runner si no existe ya
TARBALL="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
if [ ! -f "$TARBALL" ]; then
    echo "--> Descargando el runner versión ${RUNNER_VERSION}..."
    curl -o "$TARBALL" -L "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${TARBALL}"
else
    echo "--> El instalador $TARBALL ya está descargado."
fi

# Extraer el instalador
echo "--> Extrayendo el runner..."
tar xzf "./$TARBALL"

# Configurar el runner
echo "--> Configurando el runner para el repositorio $REPO_URL..."
echo "Etiquetas asociadas: $LABELS"

# Comprobar si ya existe una configuración previa
if [ -f ".runner" ]; then
    echo "⚠️  Ya existe un runner configurado en este directorio. Reemplazando..."
    ./config.sh --url "$REPO_URL" --token "$TOKEN" --name "$RUNNER_NAME" --labels "$LABELS" --work "_work" --unattended --replace
else
    ./config.sh --url "$REPO_URL" --token "$TOKEN" --name "$RUNNER_NAME" --labels "$LABELS" --work "_work" --unattended
fi

echo ""
echo "========================================================="
echo "✅ Runner configurado exitosamente!"
echo "========================================================="
echo "Para iniciar el runner de manera interactiva (primer plano):"
echo "  cd $RUNNER_DIR && ./run.sh"
echo ""
echo "Para configurarlo como servicio del sistema (segundo plano):"
echo "  sudo $RUNNER_DIR/svc.sh install"
echo "  sudo $RUNNER_DIR/svc.sh start"
echo "========================================================="
