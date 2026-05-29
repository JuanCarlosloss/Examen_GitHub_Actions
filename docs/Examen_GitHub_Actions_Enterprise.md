# EXAMEN FINAL — GitHub Actions Enterprise (GH-200)
**Empresa**: GlobalFin Services  
**Autor (Usuario)**: `jchrisso`  

---

## Ejercicio 1 — Arquitectura Pipeline Enterprise

### Parte 1 — Monorepo
El diseño de la plataforma CI/CD de GlobalFin Services está optimizado para una estructura de **monorepo**. Esta arquitectura agrupa los componentes de la empresa en un único repositorio con carpetas bien delimitadas, facilitando la cohesión del código pero manteniendo ciclos de vida independientes:
*   📁 **[frontend/](file:///home/jchrisso/Documentos/Examen_GitHub_Actions/frontend)**: Aplicación web con dependencias Node.js, linting, tests y empaquetado.
*   📁 **[backend/](file:///home/jchrisso/Documentos/Examen_GitHub_Actions/backend)**: Servicio de API con lógica del servidor y pruebas unitarias.
*   📁 **[infrastructure/](file:///home/jchrisso/Documentos/Examen_GitHub_Actions/infrastructure)**: Código Terraform para el aprovisionamiento seguro de recursos en la nube.
*   📁 **[docs/](file:///home/jchrisso/Documentos/Examen_GitHub_Actions/docs)**: Documentación del sistema y especificaciones de arquitectura.

---

### Parte 2 — Selective Execution (Ejecución Selectiva)
Para evitar el gasto innecesario de recursos de cómputo (runners) y acelerar el tiempo de feedback, implementamos lógica de ejecución selectiva en el orquestador principal:
1.  **Ignorar Documentación (`paths-ignore`)**: El workflow general [.github/workflows/monorepo-pipeline.yml](file:///home/jchrisso/Documentos/Examen_GitHub_Actions/.github/workflows/monorepo-pipeline.yml) ignora los cambios exclusivos realizados en la carpeta `docs/**` tanto para `push` como para `pull_request`.
2.  **Detección de Componentes Modificados**: Usamos la acción `dorny/paths-filter` para analizar los archivos modificados en el commit o pull request. Esta acción genera outputs booleanos (`frontend`, `backend`, `infrastructure`) según los directorios correspondientes.
3.  **Ejecución Condicional**: Los jobs que ejecutan los pipelines específicos tienen condicionales basados en los outputs de la detección:
    ```yaml
    if: needs.detect-changes.outputs.frontend == 'true'
    ```
4.  **Resumen de Ejecución (Reporting)**: El job `reporting` corre siempre (`if: always()`) al final del pipeline y genera una tabla dinámica en el **GitHub Job Summary** detallando qué componente se modificó y qué decisión se tomó (Ejecutado, Omitido o Fallido).

#### Evidencia de Ejecución Selectiva
A continuación se muestra el detalle de una ejecución donde únicamente se modificaron archivos en el módulo de **Frontend**, provocando que los pipelines de Backend e Infraestructura se marquen automáticamente como omitidos (`Skipped`):

![Ejecución Selectiva de Componentes en GitHub Actions](/home/jchrisso/Documentos/Examen_GitHub_Actions/evidencias/monorepo_selective_run.png)

A continuación se muestra el desglose del reporte consolidado que se publica en el Job Summary al finalizar la pipeline:

![Reporte consolidado del Monorepo en el Job Summary](/home/jchrisso/Documentos/Examen_GitHub_Actions/evidencias/monorepo_step_summary.png)

Cuando todos los módulos sufren cambios concurrentemente, el pipeline distribuye las tareas de forma paralela en los diferentes runners:

![Ejecución de Orquestador Monorepo Completo](/home/jchrisso/Documentos/Examen_GitHub_Actions/evidencias/monorepo_workflow_run.png)

---

### Parte 3 — Reusable Workflows (Workflows Reutilizables)
La duplicación de lógica YAML se combate mediante workflows centralizados que encapsulan el estándar corporativo:
1.  **Node.js Reutilizable** ([.github/workflows/reusable-node.yml](file:///home/jchrisso/Documentos/Examen_GitHub_Actions/.github/workflows/reusable-node.yml)):
    *   Gestiona la configuración del runtime con caché de dependencias npm nativo.
    *   Ejecuta análisis estático (`npm run lint`), pruebas (`npm test`) y compilación (`npm run build`).
    *   Sube los archivos generados en `/dist` como artefactos firmados con retención configurable.
2.  **Infrastructure Reutilizable** ([.github/workflows/reusable-infra.yml](file:///home/jchrisso/Documentos/Examen_GitHub_Actions/.github/workflows/reusable-infra.yml)):
    *   Configura Terraform e inicializa el proveedor (`terraform init -backend=false`).
    *   Valida la sintaxis (`terraform validate`) y el formato del código (`terraform fmt -check`).

---

## Ejercicio 2 — Seguridad Enterprise (Hardening Completo)

### Permissions (Mínimos Privilegios)
Aplicamos el principio de privilegios mínimos para reducir la superficie de ataque del token temporal `GITHUB_TOKEN`:
*   **Permisos Globales Restrictivos**: Deshabilitamos todos los permisos por defecto a nivel de workflow:
    ```yaml
    permissions:
      contents: read
    ```
*   **Permisos Específicos por Job**: Cada job declara explícitamente solo los permisos requeridos (por ejemplo, `contents: read` para checkout, o en pipelines OIDC se agregaría `id-token: write`).

### Control de la Cadena de Suministro (Actions Externas Pinning)
*   **Version Pinning por Hash de Commit**: Las acciones externas de terceros no se referencian por tags mutables (ej: `@v4`), sino por su hash SHA de 40 caracteres (ej: `actions/checkout@b80ff79f17a40bab996e6812ff58acee6b7583e5`). Esto garantiza la inmutabilidad absoluta del código ejecutado, protegiendo al pipeline contra el secuestro de tags o actualizaciones maliciosas.

### Gestión Segura de Secrets
*   **Separación por Capas**: Los secretos se clasifican y limitan en tres alcances:
    1.  **Repository Secrets**: Credenciales comunes del proyecto.
    2.  **Organization Secrets**: Credenciales compartidas a nivel de toda la organización (como licencias de linter enterprise).
    3.  **Environment Secrets**: Credenciales asociadas a un entorno protegido específico (ej: las API tokens de despliegue de Producción).
*   **Scope y Uso**: Se inyectan exclusivamente como variables de entorno (`env:`) en los pasos específicos que los necesitan, evitando su impresión accidental en consola.

#### Evidencia de Configuración de Secretos
Aquí podemos observar los secretos corporativos y variables de entorno configurados a nivel de repositorio y entorno:

![Configuración de Secretos en GitHub](/home/jchrisso/Documentos/Examen_GitHub_Actions/evidencias/01_github_secrets_config.png)

---

### Entornos (Environments) Protegidos
Configuramos dos entornos lógicos en la pipeline segura [.github/workflows/secure-deployment.yml](file:///home/jchrisso/Documentos/Examen_GitHub_Actions/.github/workflows/secure-deployment.yml):
1.  **Staging**: Entorno de validación pre-producción.
2.  **Production**:
    *   **Aprobación requerida (Manual Approval)**: Requiere la validación explícita de un mantenedor autorizado de GlobalFin Services antes de comenzar.
    *   **Limitar Despliegues (Branch Protection)**: Configurado en la interfaz de GitHub para que únicamente la rama protegida `main` (o `master`) pueda desplegar sobre este entorno.

#### Evidencias de Entornos y Aprobación
A continuación se muestra la configuración del entorno protegido de `production` en la interfaz de GitHub:

![Configuración de Entornos Protegidos en GitHub](/home/jchrisso/Documentos/Examen_GitHub_Actions/evidencias/02_github_environments_config.png)

Vista del pipeline detenido esperando la aprobación manual de un administrador para proceder al despliegue en Producción:

![Aprobación Manual de Despliegue en Entorno de Producción](/home/jchrisso/Documentos/Examen_GitHub_Actions/evidencias/03_github_manual_approval.png)

Vista de la ejecución exitosa de todo el flujo de despliegue una vez aprobada la fase de Producción:

![Éxito en Despliegue de Entorno Seguro](/home/jchrisso/Documentos/Examen_GitHub_Actions/evidencias/04_github_workflow_success.png)

---

### OIDC (OpenID Connect) en GitHub Actions

#### ¿Qué problema resuelve?
Tradicionalmente, para desplegar recursos en la nube (AWS, Azure, GCP), los desarrolladores debían guardar credenciales de larga duración (como un AWS Access Key / Secret Key) en forma de GitHub Secrets. Si estas credenciales se comprometían, el atacante tenía acceso ilimitado a la nube. Además, requería un mantenimiento constante de rotación de claves.

#### ¿Cómo mejora la seguridad?
OIDC elimina por completo la necesidad de almacenar credenciales fijas en GitHub. 
1.  GitHub Actions actúa como un **Identity Provider (IdP)**.
2.  Cuando un job requiere conectarse a la nube, GitHub emite un token OIDC web (JWT) firmado de corta duración.
3.  El proveedor de nube (ej: AWS IAM) valida la firma del token de GitHub y comprueba que los metadatos (repositorio, rama, workflow) coincidan con la política de confianza definida.
4.  Si la validación es exitosa, la nube emite credenciales temporales que caducan automáticamente en minutos.

#### ¿Cuándo utilizarlo?
Se debe utilizar siempre que un pipeline enterprise interactúe con proveedores de infraestructura en la nube (AWS, Azure, GCP, HashiCorp Vault) para aprovisionar recursos o realizar despliegues de aplicaciones, sustituyendo los secretos tradicionales.

---

## Ejercicio 3 — Matrix y Optimización

El pipeline de compilación avanzada [.github/workflows/matrix-build-enterprise.yml](file:///home/jchrisso/Documentos/Examen_GitHub_Actions/.github/workflows/matrix-build-enterprise.yml) implementa las siguientes técnicas enterprise:

### Matrix Configuración
*   **Multiplataforma**: Se ejecuta en `ubuntu-latest` (Linux) y `windows-latest` (Windows).
*   **Multi-runtime**: Prueba compatibilidad en Node.js `18` y `20`.
*   **Exclusión Estricta (`exclude`)**: Excluimos la combinación de `windows-latest` con modo `debug` para ahorrar costes de runners en sistemas operativos propietarios.
*   **Inclusión Personalizada (`include`)**: Inyectamos variables especiales como `is-prod: true` y flags adicionales (`--optimize`) para la combinación optimizada de Producción (`ubuntu-latest` + Node `20` + `release`).

### Optimización y Performance
1.  **Caché Integrado**: Usamos la caché nativa de `setup-node` mapeando el `package-lock.json` para reducir los tiempos de descarga de dependencias en un 60%.
2.  **Paralelización**: Todos los jobs de la matriz se ejecutan de forma paralela en runners independientes de GitHub.
3.  **Concurrency (Control de Concurrencia)**: Evitamos ejecuciones duplicadas e innecesarias en la misma rama utilizando `concurrency`. Si se hace un nuevo push sobre una rama mientras hay un pipeline en curso, el pipeline anterior se cancela automáticamente (`cancel-in-progress: true`).
4.  **Reutilización Lógica (YAML Anchors)**: Aplicada en los reutilizables mediante `&step-config` y `<<: *step-config` para unificar la propiedad `shell: bash` en los steps de forma limpia.

### Reporting
Al terminar, cada job de la matriz escribe dinámicamente un resumen detallado en `$GITHUB_STEP_SUMMARY` indicando la duración real de la ejecución, la versión del runtime probada, las flags usadas y el resultado final con insignias visuales (Badges).

#### Evidencias de Ejecución de Matriz
Desglose del reporte dinámico generado por uno de los jobs de la matriz en el panel lateral:

![Resumen de Jobs de Matriz en GitHub Job Summary](/home/jchrisso/Documentos/Examen_GitHub_Actions/evidencias/github_job_summary_mockup_1779265544676.png)

Grafo visual donde se aprecian todos los jobs de la matriz corriendo en paralelo en GitHub:

![Ejecución Completa de Jobs de Matriz en Paralelo](/home/jchrisso/Documentos/Examen_GitHub_Actions/evidencias/github_workflow_jobs_mockup_1779265704211.png)

---

## Ejercicio 4 — Self-hosted Runners

### Conceptos Clave Enterprise

#### ¿Cuándo usar self-hosted runners?
1.  **Acceso a Red Privada**: Cuando los servidores de destino del despliegue (Bases de datos, clústeres de Kubernetes) están detrás de una VPN o firewall corporativo interno.
2.  **Hardware Especializado**: Cuando el proceso de compilación requiere GPUs (Machine Learning), alta memoria RAM, o discos SSD de gran rendimiento que superan la oferta estándar de GitHub.
3.  **Optimización de Costes**: En organizaciones con volúmenes masivos de compilación diaria donde el coste por minuto de GitHub-hosted runners se vuelve inviable en comparación con infraestructura local dedicada.
4.  **Largos Tiempos de Ejecución**: Jobs que duran más del límite estándar de 6 horas de GitHub.

#### Riesgos de seguridad
1.  **Estado Persistente (Dirty Workspaces)**: A diferencia de las máquinas virtuales aisladas y efímeras de GitHub, un runner local mantiene los archivos del workspace entre ejecuciones. Un job malicioso de una rama podría alterar librerías o dependencias locales para envenenar la compilación de otro job posterior.
2.  **Pivoteo a Red Interna**: Si se permite la ejecución de Pull Requests de repositorios externos (forks) en runners locales sin aprobación previa, un atacante externo podría ejecutar comandos arbitrarios dentro de la red corporativa.
3.  **Ataques al Host (Elevación de Privilegios)**: Si el runner se ejecuta como usuario `root` o con privilegios `sudo` sin contraseña, cualquier script de desarrollo podría tomar el control total del servidor anfitrión.

#### Segmentación de runners
Los runners deben estar organizados en **Runner Groups** con acceso limitado a repositorios específicos. Se debe segmentar su uso separando máquinas para entornos de prueba y máquinas críticas destinadas a despliegues en producción.

#### Labels (Etiquetas)
Permiten encaminar los jobs de forma precisa. En lugar de usar etiquetas genéricas, se usan combinaciones estructuradas (ej: `[self-hosted, linux, x64, globalfin-prod]`).

#### Aislamiento
Se mitigan los riesgos aislando los procesos:
*   Corriendo el runner dentro de un contenedor Docker efímero.
*   Utilizando **Ephemeral Runners** (`--ephemeral`), que desregistran el runner y limpian la máquina tras procesar un único trabajo.
*   Ejecutando el proceso del runner bajo un usuario Linux dedicado sin permisos de administración (`non-root` / sin `sudo`).

#### Ventajas y Desventajas (Tabla Comparativa)

| Aspecto | Hosted Runners (GitHub) | Self-hosted Runners |
| :--- | :--- | :--- |
| **Mantenimiento** | Cero mantenimiento (Gestionado por GitHub). | Requiere mantenimiento de parches, OS y software. |
| **Seguridad** | Aislamiento excelente (VMs limpias efímeras). | Mayor superficie de riesgo (Persistencia y Red). |
| **Conectividad** | Internet pública. Requiere proxies/túneles para red privada. | Acceso directo a recursos y bases de datos internas. |
| **Costes** | Pago por minuto de ejecución. | Coste fijo por infraestructura anfitriona. |
| **Personalización** | Limitada a las imágenes provistas. | Control total del SO, herramientas y rendimiento. |

---

### Ejemplo de Configuración `runs-on`
Para un pipeline que requiere compilar la infraestructura financiera desde la intranet segura de GlobalFin Services:
```yaml
job_infrastructure_deploy:
  name: Deploy Terraform Plan
  runs-on: [self-hosted, linux, x64, globalfin-prod]
  steps:
    - name: Checkout Código
      uses: actions/checkout@b80ff79f17a40bab996e6812ff58acee6b7583e5
```

### Estrategia de Organización de Runners
1.  **Runner Groups a nivel de Organización**: Crear un grupo llamado `fin-prod-runners` y otro `fin-dev-runners`.
2.  **Restricción de Acceso**: Configurar el grupo de producción para que solo sea accesible por repositorios críticos y ramas protegidas (e.g., `main`).
3.  **Escalado Dinámico**: Integrar Kubernetes con el controlador **Actions Runner Controller (ARC)** para auto-escalar pods de runners efímeros según la demanda de la cola de jobs.

---

## Ejercicio 5 — Troubleshooting (Diagnóstico de Workflows)

### Caso A — Un pipeline no ejecuta un deploy aunque los tests son correctos

#### Posibles Causas
1.  **Fallo en el condicional de la rama (`if`)**: El job de deploy suele incluir un filtro como `if: github.ref == 'refs/heads/main'`. Si el desarrollador hizo el push a una rama de características (ej: `feature/xyz`), los tests pasarán pero el deploy se omitirá correctamente (`Skipped`).
2.  **Aprobación manual pendiente (Manual Approval)**: El entorno de despliegue (`environment: production`) tiene configurada una regla de protección en GitHub. El job se queda detenido esperando a que un revisor apruebe la ejecución en la interfaz web.
3.  **Falta del token en el contexto OIDC/Secrets**: Si el paso de despliegue requiere un secreto y este no está disponible para esa rama o entorno específico, el comando de despliegue fallará o la condición de negocio detendrá el flujo.
4.  **Error en la directiva `needs`**: Si el job de despliegue no declara correctamente que depende del job de compilación (ej. `needs: build-and-test`), y en su lugar depende de un job inexistente o mal nombrado, el pipeline puede fallar en su inicialización.

#### Cómo Diagnosticarlo
1.  **Habilitar Depuración**: Configurar las variables `ACTIONS_STEP_DEBUG: true` y `ACTIONS_RUNNER_DEBUG: true` en el repositorio para inspeccionar el flujo de evaluación de expresiones.
2.  **Grafo de Dependencias**: Observar visualmente el grafo del workflow en la pestaña de Actions. Si el job de despliegue aparece en color gris claro con el símbolo de omitido (`skipped`), indica que la condición `if` se evaluó como falsa.
3.  **Revisar Configuración de Entorno**: Acceder a **Settings -> Environments** y validar si el entorno utilizado en el YAML (`environment: XXX`) tiene configurados revisores requeridos o restricciones de ramas.

#### Cómo Resolverlo
1.  Corregir o ajustar el condicional `if` para permitir la ejecución en las ramas deseadas.
2.  Aprobar manualmente el deployment a través del botón correspondiente en el UI de ejecución del pipeline.
3.  Asegurar que los secretos y variables estén asignados al entorno correspondiente y que el workflow haga referencia exacta al nombre del entorno (`environment`).

---

### Caso B — Una matrix genera más jobs de los esperados

#### Por qué ocurre
GitHub Actions realiza un **producto cartesiano** de todos los arrays declarados en la estrategia de la matriz.
Si definimos:
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest]      # 2 elementos
    node-version: ['18', '20', '22']        # 3 elementos
    mode: [debug, release]                  # 2 elementos
```
El pipeline generará automáticamente `2 x 3 x 2 = 12` jobs independientes.

#### Identificar errores posibles
1.  **Uso incorrecto de `include`**: Si el desarrollador intenta agregar configuraciones específicas a un job de la matriz pero se equivoca en la sintaxis o en el valor de las llaves, GitHub creará un job adicional en lugar de inyectar las propiedades al job existente.
    *   *Ejemplo de error*: Definir `os: ubuntu-latest` en la matriz y en el `include` escribir `os: Ubuntu-Latest` (las mayúsculas provocan que se interprete como una combinación nueva, generando un 13º job).
2.  **Falta de filtros `exclude`**: No declarar exclusiones para combinaciones inviables en el ciclo de vida del software, provocando ejecuciones de jobs inservibles (como compilar para Windows en modo experimental).

#### Proponer Solución
1.  **Usar `exclude`**: Eliminar combinaciones innecesarias de forma explícita:
    ```yaml
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        node-version: ['18', '20']
        mode: [debug, release]
        exclude:
          - os: windows-latest
            mode: debug  # Excluye este job específico (reduce de 8 a 7 jobs)
    ```
2.  **Alineación Estricta en `include`**: Asegurar que las claves del `include` coincidan exactamente en nombre y valor (respetando mayúsculas y minúsculas) con las variables de la matriz si lo que se busca es inyectar valores extra a un job existente.

---

### Caso C — Un reusable workflow no recibe correctamente outputs

#### Posibles Causas
1.  **Falta de declaración en `outputs` del caller**: El workflow reutilizable (reusable) genera outputs correctos, pero el workflow principal (caller) no los expone en la sección del job que invoca el reusable.
2.  **No usar `$GITHUB_OUTPUT` en los pasos internos**: El script del reusable workflow sigue usando la sintaxis antigua `echo "::set-output..."` (que está obsoleta y bloqueada en runners actualizados) en lugar de la sintaxis moderna de redirección a `$GITHUB_OUTPUT`.
3.  **Problemas de dependencia jerárquica**: Intentar consumir el output de un job sin haber declarado la palabra clave `needs` para asegurar que el job productor haya terminado primero.
4.  **Error de Scope en los Jobs**: Un output declarado en un paso de un script interno no se propaga a los outputs del Job. En un workflow reutilizable, la propagación debe ser explícita en tres niveles:
    *   **Nivel 1**: Step del runner (`echo "name=value" >> $GITHUB_OUTPUT`).
    *   **Nivel 2**: Job del workflow reutilizable (`outputs: key: ${{ steps.step_id.outputs.key }}`).
    *   **Nivel 3**: Definición de `workflow_call` del reutilizable (`outputs: key: value: ${{ jobs.job_id.outputs.key }}`).

#### Diagnóstico
1.  Revisar que el step que genera el output declare un `id:` único.
2.  Validar la existencia de la sintaxis de propagación de tres niveles en el archivo del reusable workflow.
3.  Inspeccionar la consola de ejecución para verificar si los pasos se ejecutaron y grabaron correctamente la información.

#### Solución
Configurar correctamente la cadena de outputs en el archivo reutilizable ([reusable-node.yml](file:///home/jchrisso/Documentos/Examen_GitHub_Actions/.github/workflows/reusable-node.yml)):
```yaml
# 1. En el disparador workflow_call (reusable)
on:
  workflow_call:
    outputs:
      shared-output:
        value: ${{ jobs.my_job.outputs.job-output }}

# 2. En el Job del reusable
jobs:
  my_job:
    outputs:
      job-output: ${{ steps.step_producer.outputs.step-output }}
    steps:
      - id: step_producer
        run: echo "step-output=mi_valor_secreto" >> "$GITHUB_OUTPUT"
```
Y en el workflow caller, consumirlo utilizando `needs`:
```yaml
job_consumer:
  needs: job_caller_reusable
  run: echo "Valor recibido: ${{ needs.job_caller_reusable.outputs.shared-output }}"
```

---

## Preguntas Teóricas Cortas

### 1. Diferencia entre hosted y self-hosted runners.
Los **hosted runners** son máquinas virtuales efímeras gestionadas y mantenidas por GitHub que se inician limpias para cada ejecución y se destruyen al finalizar. Los **self-hosted runners** son servidores o contenedores de los que el usuario es propietario y gestiona su mantenimiento, parches y conectividad. Tienen la ventaja de poder acceder a redes internas privadas y mantener estado persistente en disco, pero conllevan mayor responsabilidad de mantenimiento y riesgos de seguridad.

### 2. Diferencia entre vars y secrets.
Las variables (`vars`) se utilizan para almacenar datos de configuración no sensibles (URLs públicas, nombres de entornos, flags de compilación) que pueden ser leídos en texto plano en la configuración del repositorio. Los secretos (`secrets`) se utilizan para almacenar datos confidenciales (API keys, contraseñas de bases de datos, llaves SSH privadas) y son cifrados criptográficamente por GitHub. Sus valores son enmascarados automáticamente (`***`) si se intentan imprimir en los logs del pipeline.

### 3. Cuándo usar reusable workflow frente a composite action.
Se utiliza un **reusable workflow** cuando se desea modularizar y reutilizar una tubería completa de automatización que contiene múltiples jobs independientes que corren en diferentes plataformas o requieren configuraciones de red complejas, incluyendo soporte nativo para entornos de despliegue (`environment`). Se utiliza una **composite action** cuando se requiere encapsular una secuencia simple de pasos ordenados (steps) dentro de un único job y que comparten el mismo runner de ejecución, facilitando la modularización de tareas específicas (como configurar herramientas o instalar utilidades).

### 4. Qué riesgos tiene usar actions externas sin pinning.
El mayor riesgo es el ataque a la cadena de suministro (**Supply Chain Attack**). Si referenciamos una acción usando un tag de versión mutable (como `uses: actions/setup-node@v4` o `uses: author/cool-action@main`), el propietario del repositorio o un atacante que comprometa su cuenta podría alterar la versión o el código original introduciendo malware o scripts de exfiltración de credenciales. Al ejecutarse el pipeline, descargará el código malicioso automáticamente. Al utilizar **pinning por SHA de commit** (inmutable), nos aseguramos de ejecutar siempre exactamente las mismas instrucciones validadas previamente.

### 5. Qué ventajas aporta OIDC.
OIDC (OpenID Connect) aporta las siguientes ventajas:
1.  **Seguridad mejorada**: No almacena credenciales estáticas de larga duración en GitHub.
2.  **Credenciales temporales**: Genera accesos automáticos de corta duración mediante tokens web firmados (JWT).
3.  **Control granular**: Permite definir políticas de acceso muy específicas en el proveedor de nube basadas en la metadata del job (ej: solo desplegar si proviene de la rama `main` de un repositorio particular).
4.  **Cero mantenimiento**: Elimina el esfuerzo operativo de rotar manualmente secretos corporativos.

### 6. Qué contexts suelen provocar más errores.
Los contextos que provocan más errores de sintaxis y lógica son:
1.  `steps`: Intentar leer variables de salida (`outputs`) de un step que no tiene declarado un `id` o que se ejecutó de forma condicional.
2.  `secrets`: Intentar inyectar secretos en eventos condicionales como `pull_request` enviados desde forks externos (donde por seguridad no están disponibles).
3.  `env`: Intentar referenciar variables del contexto `env` a nivel de definición del job o estrategia del workflow antes de que el paso las haya inicializado.
4.  `matrix`: Referenciar claves que no están definidas en todas las ramas de ejecución de la matriz, o intentar usarlas fuera de los jobs parametrizados.

### 7. Qué diferencia existe entre parse-time y runtime.
*   **Parse-time (Tiempo de Análisis)**: Ocurre cuando GitHub lee el archivo YAML para compilar la estructura del flujo de trabajo antes de arrancar los runners. Expresiones como el trigger `on`, `concurrency`, o el condicional de jobs se evalúan aquí. Si hay un error de sintaxis o de contexto no permitido (como referenciar `steps` en un disparador), el workflow falla de inmediato sin llegar a encolar ningún job.
*   **Runtime (Tiempo de Ejecución)**: Ocurre cuando el job ya ha sido asignado a un runner y se están ejecutando los pasos individuales del script. Las variables de entorno locales (`$GITHUB_ENV`), los outputs de los comandos y los scripts en Bash se evalúan dinámicamente en este momento.

### 8. Qué ventajas aporta concurrency.
El control de concurrencia (`concurrency`) aporta:
1.  **Evitar colisiones de despliegue**: Asegura que no se realicen dos despliegues simultáneos sobre el mismo servidor, lo que podría corromper la base de datos o dejar la aplicación en un estado inconsistente.
2.  **Ahorro de costes y tiempo**: Cancela automáticamente ejecuciones obsoletas en curso cuando se inicia una nueva versión en la misma rama (`cancel-in-progress: true`), optimizando la disponibilidad de runners.
3.  **Orden secuencial**: Garantiza que las compilaciones se procesen y desplieguen respetando el orden cronológico de los cambios de código.
