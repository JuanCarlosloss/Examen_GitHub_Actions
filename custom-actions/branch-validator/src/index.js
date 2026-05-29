import * as core from '@actions/core';

async function run() {
  try {
    // 1. Obtener y sanitizar inputs
    let branchName = core.getInput('branch-name', { required: false }) || '';
    const allowedPrefixesInput = core.getInput('allowed-prefixes', { required: false }) || '';
    const minLengthInput = core.getInput('min-length', { required: false }) || '5';

    // Fallback robusto para detectar la rama actual del entorno si el input es vacío o es la cadena por defecto del YAML
    if (!branchName.trim() || branchName === '${{ github.head_ref || github.ref_name }}') {
      branchName = process.env.GITHUB_HEAD_REF || process.env.GITHUB_REF_NAME || '';
    }

    console.log(`Iniciando validación de la rama: "${branchName}"`);
    console.log(`Prefijos permitidos: [${allowedPrefixesInput}]`);
    console.log(`Longitud mínima requerida para el sufijo: ${minLengthInput}`);

    // Parte 5 — Robustez: Gestión de valores vacíos y nulos
    if (!branchName.trim()) {
      core.setOutput('is-valid', 'false');
      core.setOutput('branch-type', 'unknown');
      core.setOutput('branch-reason', 'El nombre de la rama está vacío o no fue provisto.');
      core.setFailed('Error de validación: El nombre de la rama está vacío.');
      return;
    }

    const minLength = parseInt(minLengthInput, 10);
    if (isNaN(minLength) || minLength < 0) {
      core.setOutput('is-valid', 'false');
      core.setOutput('branch-type', 'unknown');
      core.setOutput('branch-reason', 'El input min-length no es un número válido.');
      core.setFailed('Error de configuración: min-length debe ser un número entero válido.');
      return;
    }

    const allowedPrefixes = allowedPrefixesInput
      .split(',')
      .map(p => p.trim())
      .filter(p => p.length > 0);

    if (allowedPrefixes.length === 0) {
      core.setOutput('is-valid', 'false');
      core.setOutput('branch-type', 'unknown');
      core.setOutput('branch-reason', 'La lista de prefijos permitidos está vacía.');
      core.setFailed('Error de configuración: allowed-prefixes no contiene ningún prefijo válido.');
      return;
    }

    // 2. Ejecutar validaciones de nomenclatura
    // Formato esperado: prefijo/nombre-descriptivo (ej: feature/nueva-api)
    const parts = branchName.split('/');
    if (parts.length < 2) {
      const reason = `El nombre de la rama "${branchName}" no tiene barra inclinada (/). Formato requerido: prefijo/nombre-sufijo`;
      core.setOutput('is-valid', 'false');
      core.setOutput('branch-type', 'unknown');
      core.setOutput('branch-reason', reason);
      console.log(`❌ Validación fallida: ${reason}`);
      return;
    }

    const prefix = parts[0];
    const suffix = parts.slice(1).join('/'); // Por si hay múltiples "/"

    // Validar prefijo
    if (!allowedPrefixes.includes(prefix)) {
      const reason = `El prefijo "${prefix}" no está en la lista de permitidos [${allowedPrefixes.join(', ')}].`;
      core.setOutput('is-valid', 'false');
      core.setOutput('branch-type', 'unknown');
      core.setOutput('branch-reason', reason);
      console.log(`❌ Validación fallida: ${reason}`);
      return;
    }

    // Validar longitud del sufijo
    if (suffix.length < minLength) {
      const reason = `El sufijo "${suffix}" tiene longitud ${suffix.length}, pero se requiere al menos ${minLength} caracteres.`;
      core.setOutput('is-valid', 'false');
      core.setOutput('branch-type', prefix);
      core.setOutput('branch-reason', reason);
      console.log(`❌ Validación fallida: ${reason}`);
      return;
    }

    // Si todo pasa con éxito
    const successReason = 'Nomenclatura de la rama cumple correctamente con todos los requisitos de la política corporativa.';
    core.setOutput('is-valid', 'true');
    core.setOutput('branch-type', prefix);
    core.setOutput('branch-reason', successReason);
    console.log(`✅ Validación exitosa: ${successReason}`);

  } catch (error) {
    // Manejo robusto de excepciones no controladas
    core.setOutput('is-valid', 'false');
    core.setOutput('branch-type', 'unknown');
    core.setOutput('branch-reason', `Error crítico en tiempo de ejecución: ${error.message}`);
    core.setFailed(`Error en la ejecución de la custom action: ${error.message}`);
  }
}

run();
