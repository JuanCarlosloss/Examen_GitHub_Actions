# Laboratorio 5 — Guía de Troubleshooting y Análisis de Seguridad

Este documento aborda las fases de diagnóstico de incidentes, activación de logs detallados y mitigación de riesgos de seguridad para entornos de integración continua que utilizan **self-hosted runners** en GitHub Actions.

---

## Parte 3 — Troubleshooting: Diagnóstico y Resolución de Errores Comunes

A continuación se detalla cómo identificar y resolver los errores provocados más frecuentes en entornos de infraestructura propia:

### 1. Label Incorrecto (Etiquetas Erróneas)
*   **Síntoma:** El Job se queda en estado "Queued" (En cola) indefinidamente, mostrando un mensaje como *"Waiting for a runner to pick up this job..."*.
*   **Diagnóstico:** GitHub Actions busca runners registrados que contengan exactamente todas las etiquetas especificadas en la clave `runs-on` del YAML. Si escribimos `runs-on: [self-hosted, wrong-label]`, el job no se asignará a ningún runner a menos que exista uno con ambas etiquetas.
*   **Solución:**
    1.  Verificar las etiquetas reales del runner registrado en **Settings -> Actions -> Runners**.
    2.  Corregir la directiva `runs-on` en el archivo del workflow (ej. corregir a `custom-runner-lab5`).
    3.  Alternativamente, agregar la etiqueta faltante al runner en la consola de GitHub (Settings -> Actions -> Runners -> click en el runner -> Icono de engranaje -> "Edit" en etiquetas).

### 2. Runner Offline (Runner Desconectado)
*   **Síntoma:** Los Jobs se quedan en cola o fallan inmediatamente con errores de pérdida de conectividad, y en la interfaz de GitHub el runner aparece con estado gris de "Offline".
*   **Diagnóstico:** El proceso del runner (`run.sh` o el servicio de systemd) se ha detenido en el servidor anfitrión, o este ha perdido acceso a Internet/APIs de GitHub.
*   **Solución:**
    1.  Acceder al servidor host del runner.
    2.  Verificar si el proceso está activo: `ps aux | grep Runner.Listener`.
    3.  Comprobar el estado del servicio si fue instalado como systemd:
        ```bash
        sudo systemctl status actions-runner.service
        ```
    4.  Iniciar o reiniciar el servicio:
        ```bash
        sudo ./run.sh   # En modo interactivo
        # O como servicio:
        sudo systemctl start actions-runner.service
        ```
    5.  Comprobar la conectividad de red saliente hacia los endpoints de GitHub (`github.com`, `api.github.com`, `pipelines.actions.githubusercontent.com`).

### 3. Dependencia Inexistente (Falta de Herramientas en el Host)
*   **Síntoma:** El Job comienza a ejecutarse pero falla en algún paso con errores como *"command not found"* (ej. `node: command not found` o `npm: command not found`).
*   **Diagnóstico:** A diferencia de los runners de GitHub (hosted), que vienen con cientos de herramientas preinstaladas, los runners self-hosted están completamente limpios. Si el workflow asume que `node`, `npm`, `docker` o `git` están instalados sin haberlos instalado previamente en la máquina anfitriona, el paso fallará.
*   **Solución:**
    1.  Instalar la herramienta correspondiente de forma global en el sistema operativo del runner (ej. `sudo apt install nodejs npm`).
    2.  O bien, asegurar el uso de la acción `actions/setup-node` (u homólogos) en el workflow, aunque en entornos self-hosted esto requiere que el runner tenga acceso a descargar binarios o utilizar el cache local.
    3.  Asegurar que el PATH del usuario del runner contenga las rutas de las herramientas instaladas.

### 4. Path Inválido (Rutas Inexistentes u Erróneas)
*   **Síntoma:** Errores del tipo *"No such file or directory"* o fallos al leer/escribir archivos durante la ejecución de los comandos `run`.
*   **Diagnóstico:** Diferencias de estructura de directorios entre los entornos de compilación y despliegue. Por ejemplo, intentar escribir en `/var/www/html` en el runner self-hosted cuando dicha carpeta no existe, o asumir rutas absolutas fijas de contenedores hosted (como `/home/runner/work/...`).
*   **Solución:**
    1.  Utilizar siempre variables de entorno predefinidas para referenciar rutas:
        *   `${{ github.workspace }}` o `$GITHUB_WORKSPACE` para la raíz del repositorio clonado.
        *   `${{ runner.temp }}` para directorios temporales que se limpian automáticamente.
    2.  Evitar rutas absolutas dependientes de la máquina de desarrollo o de los hosted runners de GitHub.
    3.  Crear directorios de forma dinámica usando `mkdir -p <ruta>` antes de intentar copiar o guardar archivos.

### 5. Error de Permisos (Falta de Privilegios de Escritura/Ejecución)
*   **Síntoma:** Errores de *"Permission denied"* (EACCES) al intentar escribir en directorios locales, arrancar un script (ej. `./scripts/deploy.sh`) o levantar un contenedor Docker.
*   **Diagnóstico:** El proceso del runner se ejecuta bajo un usuario de Linux específico (ej. `jchrisso`). Si este usuario no tiene permisos de lectura/escritura sobre el directorio de destino de despliegue, o no pertenece al grupo `docker` para invocar comandos Docker, o los scripts descargados no tienen permisos de ejecución (`+x`), el job fallará.
*   **Solución:**
    1.  Asignar permisos de ejecución a los scripts del repositorio antes de correrlos: `chmod +x ./scripts/deploy.sh` (o subir el cambio de permisos trackeado en Git: `git update-index --chmod=+x scripts/deploy.sh`).
    2.  Asegurar que el usuario que ejecuta el runner sea el propietario o tenga permisos de escritura en la carpeta destino (ej. `sudo chown -R $USER:$USER /var/www/html`).
    3.  Agregar el usuario al grupo Docker si se requiere interactuar con el socket de Docker: `sudo usermod -aG docker $USER` y reiniciar el servicio del runner.

---

## Parte 4 — Logging: Diagnósticos y Trazabilidad Detallada

Para realizar un análisis forense de fallos en GitHub Actions, es crucial activar y consumir el logging avanzado.

### Activación del Logging Detallado
Podemos forzar logs de depuración detallados configurando secretos o variables a nivel de repositorio o mediante las variables de entorno del workflow:
*   `ACTIONS_RUNNER_DEBUG: 'true'` -> Habilita el log detallado de las actividades del agente/runner.
*   `ACTIONS_STEP_DEBUG: 'true'` -> Habilita el log detallado de cada comando ejecutado en los steps (equivalente a `set -x` en bash).

### Dónde Buscar Información
1.  **Logs de Ejecución en GitHub UI:** Al habilitar las variables anteriores, aparecerán líneas grises extras en el visor de GitHub que detallan la inyección de variables, rutas y llamadas internas del sistema de Actions.
2.  **Logs Locales del Runner (Carpeta `_diag`):**
    *   Dentro de la carpeta del runner (ej. `/home/jchrisso/actions-runner/_diag/`), existen archivos de log críticos:
        *   `Runner_*.log`: Registra el ciclo de vida del runner, la comunicación WebSockets con GitHub, y la asignación/recepción de trabajos.
        *   `Worker_*.log`: Contiene la salida detallada de la ejecución de los trabajos individuales, incluyendo el flujo de comunicación y el paso de datos en el host local.

---

## Parte 5 — Seguridad: Análisis de Riesgos en Runners Persistentes

Los runners autohospedados ofrecen un alto rendimiento y acceso directo a infraestructura privada, pero introducen vectores de ataque críticos que deben ser mitigados.

### 1. Riesgos de Runners Persistentes
*   **Riesgo (Estado Persistente y Envenenamiento de Caché):** A diferencia de los runners de GitHub que se destruyen después de cada job, un runner self-hosted mantiene el disco y el estado del sistema intacto entre ejecuciones. Si un job malicioso modifica archivos del sistema o deja artefactos infectados en directorios compartidos, el siguiente job (que podría ser de otra rama o proyecto) se ejecutará bajo un entorno comprometido.
*   **Mitigación:** 
    *   Utilizar la opción de "Ephemeral Runners" (Runners efímeros) donde el runner se desregistra y se destruye automáticamente tras procesar un único trabajo (usando la bandera `--ephemeral` al configurarlo).
    *   Limpiar explícitamente el workspace al inicio y fin de cada ejecución mediante acciones de limpieza o comandos de limpieza manuales.

### 2. Riesgos de Acceso a Red (Pivoteo a Red Interna)
*   **Riesgo:** El runner reside físicamente o lógicamente dentro de la red corporativa/privada. Si un atacante logra inyectar código en el repositorio (por ejemplo, a través de una Pull Request maliciosa de un fork externo si el workflow se ejecuta en `pull_request` sin aprobación), el código del atacante se ejecutará dentro de tu red privada. Esto permite realizar escaneo de puertos internos, acceder a bases de datos corporativas o extraer secretos de la nube interna utilizando el rol del host del runner.
*   **Mitigación:**
    *   **NUNCA** habilitar ejecuciones automáticas de Pull Requests de repositorios externos (forks) en runners self-hosted sin una revisión y aprobación manual explícita (`Require approval for all outside collaborators`).
    *   Ubicar los runners en una DMZ o VPC aislada con reglas de firewall de salida muy restrictivas (permitiendo solo conexiones salientes hacia GitHub y bloqueando el acceso a IPs de la intranet).

### 3. Riesgos de Aislamiento Insuficiente (Ataques al Host)
*   **Riesgo (Acceso Root/Host Compromise):** Si el runner corre directamente sobre el sistema operativo (bare metal) y bajo un usuario con privilegios de administrador (`sudo` sin contraseña), cualquier comando de un workflow puede comprometer todo el servidor. El atacante podría instalar malware persistente, capturar contraseñas del sistema, o leer llaves SSH privadas del usuario host.
*   **Mitigación:**
    *   Ejecutar el runner bajo un usuario sin privilegios administrativos dedicados exclusivamente a esta tarea.
    *   Habilitar el aislamiento mediante contenedores de Docker (usando la clave `container` en el job) o desplegar el runner dentro de máquinas virtuales de usar y tirar (ej. microVMs de AWS Firecracker, instancias de Kubernetes efímeras) que se destruyan inmediatamente después de cada ejecución.
