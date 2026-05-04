/**
 * Motor AFD — Frontend Logic
 * Handles real-time validation, text extraction, and the dynamic form builder.
 */
document.addEventListener('DOMContentLoaded', () => {

    // ========================================
    // PAGE 1: Motor (Validación + Extracción)
    // ========================================
    const valText = document.getElementById('valText');
    const valResult = document.getElementById('valResult');
    const extractForm = document.getElementById('extractForm');
    const extResult = document.getElementById('extResult');

    // -- Real-time validation with debounce --
    if (valText && valResult) {
        let timeout = null;
        valText.addEventListener('input', () => {
            clearTimeout(timeout);
            const text = valText.value;

            if (!text) {
                valResult.className = 'result';
                valResult.textContent = 'Esperando entrada…';
                return;
            }

            timeout = setTimeout(async () => {
                const formData = new FormData();
                formData.append('text', text);

                try {
                    const res = await fetch('/validate', { method: 'POST', body: formData });
                    const data = await res.json();

                    if (data.valid) {
                        valResult.className = 'result valid';
                        valResult.textContent = `✅ Entrada Aceptada — ${data.type}`;
                    } else {
                        valResult.className = 'result invalid';
                        valResult.textContent = '❌ Entrada Rechazada — Ningún patrón coincide';
                    }
                } catch (err) {
                    console.error('Error de red:', err);
                }
            }, 200);
        });
    }

    // -- Extraction --
    if (extractForm && extResult) {
        // Color mapping for match types
        const typeClass = {
            'Placa Colombiana': 'match-placa',
            'Correo Electrónico': 'match-email',
            'Teléfono': 'match-telefono',
            'Documento de Identidad': 'match-documento',
            'Dirección URL': 'match-url',
            'Fecha': 'match-fecha',
            'Contraseña Segura': 'match-password',
        };

        extractForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = document.getElementById('extText').value;
            if (!text.trim()) return;

            const formData = new FormData();
            formData.append('text', text);

            extResult.style.display = 'block';
            extResult.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:1rem;"><span class="spinner"></span> Procesando texto con Motores AFD…</div>';

            try {
                const res = await fetch('/extract', { method: 'POST', body: formData });
                const data = await res.json();

                if (data.count === 0) {
                    extResult.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:1rem;">No se encontraron subcadenas válidas en el texto.</p>';
                } else {
                    let html = `<div class="result-header">Se detectaron <strong>${data.count}</strong> coincidencias clasificadas:</div><div>`;
                    data.matches.forEach((match, i) => {
                        const cls = typeClass[match.type] || 'match-placa';
                        html += `<span class="match-item ${cls}" style="animation-delay:${i * 0.05}s">
                            <span class="match-text">${escapeHtml(match.text)}</span>
                            <span class="match-type">${match.type}</span>
                        </span>`;
                    });
                    html += '</div>';
                    extResult.innerHTML = html;
                }
            } catch (err) {
                extResult.innerHTML = '<p style="color:var(--accent-rose);text-align:center;">Error al procesar la extracción.</p>';
                console.error('Error:', err);
            }
        });
    }


    // ========================================
    // PAGE 2: Formulario Dinámico
    // ========================================
    const patternSelect = document.getElementById('patternSelect');
    const addFieldBtn = document.getElementById('addFieldBtn');
    const dynamicFields = document.getElementById('dynamicFields');
    const emptyState = document.getElementById('emptyState');
    const submitArea = document.getElementById('submitArea');
    const submitFormBtn = document.getElementById('submitFormBtn');
    const formSummary = document.getElementById('formSummary');

    if (patternSelect && addFieldBtn && dynamicFields) {
        let patterns = [];
        let fieldCounter = 0;
        let fieldStates = {}; // { fieldId: { pattern, valid, value } }

        // Load available patterns from API
        fetch('/api/patterns')
            .then(r => r.json())
            .then(data => {
                patterns = data.patterns;
                patterns.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.name;
                    opt.textContent = p.name;
                    patternSelect.appendChild(opt);
                });
            });

        // Add field button
        addFieldBtn.addEventListener('click', () => {
            const selectedPattern = patternSelect.value;
            if (!selectedPattern) return;

            const patternInfo = patterns.find(p => p.name === selectedPattern);
            if (!patternInfo) return;

            fieldCounter++;
            const fieldId = `field_${fieldCounter}`;

            // Hide empty state, show submit area
            if (emptyState) emptyState.style.display = 'none';
            submitArea.style.display = 'flex';

            // Track field state
            fieldStates[fieldId] = { pattern: selectedPattern, valid: false, value: '' };

            // Create field element
            const fieldDiv = document.createElement('div');
            fieldDiv.className = 'dynamic-field';
            fieldDiv.id = fieldId;
            fieldDiv.innerHTML = `
                <div class="field-content">
                    <div class="field-label">
                        <span>${getPatternIcon(selectedPattern)}</span>
                        ${escapeHtml(selectedPattern)}
                    </div>
                    <div class="field-hint">${escapeHtml(patternInfo.hint)}</div>
                    <input type="${selectedPattern === 'Contraseña Segura' ? 'password' : 'text'}"
                           placeholder="Ingresa el valor…"
                           data-field-id="${fieldId}"
                           data-pattern="${escapeHtml(selectedPattern)}"
                           autocomplete="off"
                           class="field-input">
                    ${selectedPattern === 'Contraseña Segura' ? '<div class="password-strength"><div class="password-strength-bar" id="str_' + fieldId + '"></div></div>' : ''}
                    <div class="field-feedback" id="fb_${fieldId}"></div>
                </div>
                <button type="button" class="btn btn-danger btn-sm field-remove" data-remove="${fieldId}" title="Eliminar campo">✕</button>
            `;

            dynamicFields.appendChild(fieldDiv);

            // Attach real-time validation
            const input = fieldDiv.querySelector('.field-input');
            let debounce = null;
            input.addEventListener('input', () => {
                clearTimeout(debounce);
                const val = input.value;
                fieldStates[fieldId].value = val;

                if (!val) {
                    input.className = 'field-input';
                    fieldDiv.className = 'dynamic-field';
                    document.getElementById(`fb_${fieldId}`).textContent = '';
                    document.getElementById(`fb_${fieldId}`).className = 'field-feedback';
                    fieldStates[fieldId].valid = false;
                    updateSubmitButton();
                    // Reset password bar
                    const strBar = document.getElementById(`str_${fieldId}`);
                    if (strBar) strBar.className = 'password-strength-bar';
                    return;
                }

                debounce = setTimeout(async () => {
                    const formData = new FormData();
                    formData.append('value', val);
                    formData.append('pattern', fieldStates[fieldId].pattern);

                    try {
                        const res = await fetch('/validate-field', { method: 'POST', body: formData });
                        const data = await res.json();
                        const fb = document.getElementById(`fb_${fieldId}`);

                        if (data.valid) {
                            input.className = 'field-input field-valid';
                            fieldDiv.className = 'dynamic-field field-row-valid';
                            fb.textContent = '✅ Válido';
                            fb.className = 'field-feedback valid';
                            fieldStates[fieldId].valid = true;
                        } else {
                            input.className = 'field-input field-invalid';
                            fieldDiv.className = 'dynamic-field field-row-invalid';
                            fb.textContent = '❌ Formato inválido';
                            fb.className = 'field-feedback invalid';
                            fieldStates[fieldId].valid = false;
                        }

                        // Password strength
                        if (fieldStates[fieldId].pattern === 'Contraseña Segura') {
                            updatePasswordStrength(fieldId, val);
                        }

                        updateSubmitButton();
                    } catch (err) {
                        console.error('Validation error:', err);
                    }
                }, 250);
            });

            // Remove button
            fieldDiv.querySelector('.field-remove').addEventListener('click', () => {
                fieldDiv.remove();
                delete fieldStates[fieldId];

                if (Object.keys(fieldStates).length === 0) {
                    if (emptyState) emptyState.style.display = 'block';
                    submitArea.style.display = 'none';
                    formSummary.style.display = 'none';
                }
                updateSubmitButton();
            });

            // Reset select
            patternSelect.value = '';
            updateSubmitButton();
        });

        // Submit button
        if (submitFormBtn) {
            submitFormBtn.addEventListener('click', () => {
                // Show summary
                let html = '<div class="form-summary"><h3>📋 Datos del Formulario — Todos Válidos</h3>';
                Object.entries(fieldStates).forEach(([id, state]) => {
                    const displayValue = state.pattern === 'Contraseña Segura'
                        ? '•'.repeat(state.value.length)
                        : escapeHtml(state.value);
                    html += `<div class="summary-row">
                        <span class="summary-label">${getPatternIcon(state.pattern)} ${escapeHtml(state.pattern)}</span>
                        <span class="summary-value">${displayValue}</span>
                    </div>`;
                });
                html += '</div>';
                formSummary.innerHTML = html;
                formSummary.style.display = 'block';
            });
        }

        function updateSubmitButton() {
            const allIds = Object.keys(fieldStates);
            const allValid = allIds.length > 0 && allIds.every(id => fieldStates[id].valid);
            submitFormBtn.disabled = !allValid;
        }

        function updatePasswordStrength(fieldId, value) {
            const bar = document.getElementById(`str_${fieldId}`);
            if (!bar) return;

            let score = 0;
            if (value.length >= 8) score++;
            if (/[A-Z]/.test(value)) score++;
            if (/[a-z]/.test(value)) score++;
            if (/[0-9]/.test(value)) score++;
            // Note: we use a basic check here only for the visual bar, actual validation is done by the AFD
            const levels = ['', 'strength-weak', 'strength-fair', 'strength-good', 'strength-strong'];
            bar.className = 'password-strength-bar ' + (levels[score] || '');
        }
    }


    // ========================================
    // UTILITIES
    // ========================================
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function getPatternIcon(pattern) {
        const icons = {
            'Placa Colombiana': '🚗',
            'Correo Electrónico': '📧',
            'Teléfono': '📞',
            'Documento de Identidad': '🪪',
            'Dirección URL': '🌐',
            'Fecha': '📅',
            'Contraseña Segura': '🔒',
        };
        return icons[pattern] || '📝';
    }
});
