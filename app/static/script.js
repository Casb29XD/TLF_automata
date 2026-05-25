/**
 * Motor AFD — Frontend Logic
 * Handles real-time validation, text extraction, the dynamic form builder,
 * and the form CRUD system (create, respond, view responses).
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
                        window.currentTraceData = data.trace;
                        window.currentTraceText = data.text;
                        window.currentEvaluations = data.evaluations; // store evaluations
                        window.currentGraphSyntax = data.graph_syntax;
                        valResult.className = 'result valid';
                        valResult.innerHTML = `Entrada Aceptada — ${data.type} <button type="button" class="btn btn-secondary btn-sm" style="margin-left: 1rem; padding: 0.2rem 0.6rem; font-size: 0.8rem;" onclick="openTrace('${data.type}', '${data.text}')">▶ Ver Funcionamiento</button>`;
                    } else {
                        valResult.className = 'result invalid';
                        valResult.textContent = 'Entrada Rechazada — Ningún patrón coincide';
                    }
                } catch (err) {
                    console.error('Error de red:', err);
                }
            }, 200);
        });
    }

    // -- Extraction --
    if (extractForm && extResult) {
        const typeClass = {
            'Placa Colombiana': 'match-placa',
            'Correo Electrónico': 'match-email',
            'Teléfono': 'match-telefono',
            'Documento de Identidad': 'match-documento',
            'Dirección URL': 'match-url',
            'Fecha': 'match-fecha',
            'Contraseña Segura': 'match-password',
            'Monto de Dinero': 'match-dinero',
            'Dirección Física': 'match-direccion',
        };

        const extFile = document.getElementById('extFile');
        if (extFile) {
            extFile.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = function(evt) {
                    document.getElementById('extText').value = evt.target.result;
                };
                reader.readAsText(file);
            });
        }

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
                        html += `<span class="match-item ${cls}" style="animation-delay:${i * 0.05}s; cursor:pointer;" onclick="fetchAndOpenTrace('${match.type}', '${escapeHtml(match.text)}')" title="Clic para ver paso a paso">
                            <span class="match-text">${escapeHtml(match.text)}</span>
                            <span class="match-type">${match.type}</span>
                        </span>`;
                    });
                    html += `</div><p style="margin-top: 1.5rem; font-size: 0.85rem; color: var(--text-muted); text-align: center;">💡 Haz clic en cualquier etiqueta extraída para ver cómo el autómata la reconoció paso a paso.</p>`;
                    extResult.innerHTML = html;
                }
            } catch (err) {
                extResult.innerHTML = '<p style="color:var(--accent-rose);text-align:center;">Error al procesar la extracción.</p>';
                console.error('Error:', err);
            }
        });
    }


    // ========================================
    // PAGE 2: FORMULARIOS (Tabs)
    // ========================================
    const tabButtons = document.querySelectorAll('.tab[data-tab]');
    const tabPanels = document.querySelectorAll('.tab-content');

    if (tabButtons.length > 0) {
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const target = btn.dataset.tab;

                tabButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                tabPanels.forEach(p => p.classList.remove('active'));

                const panelId = {
                    'crear': 'panelCrear',
                    'responder': 'panelResponder',
                    'resultados': 'panelResultados',
                }[target];

                if (panelId) {
                    document.getElementById(panelId).classList.add('active');
                }
            });
        });
    }


    // ========================================
    // TAB 1: CREAR FORMULARIO
    // ========================================
    const patternSelect = document.getElementById('patternSelect');
    const addFieldBtn = document.getElementById('addFieldBtn');
    const dynamicFields = document.getElementById('dynamicFields');
    const emptyState = document.getElementById('emptyState');
    const createArea = document.getElementById('createArea');
    const createFormBtn = document.getElementById('createFormBtn');
    const fieldLabelInput = document.getElementById('fieldLabel');
    const formContrasenaInput = document.getElementById('formContrasena');

    if (formContrasenaInput) {
        formContrasenaInput.addEventListener('input', (e) => {
            updatePasswordStrength('formContrasena', e.target.value);
        });
    }

    if (patternSelect && addFieldBtn && dynamicFields) {
        let patterns = [];
        let fieldCounter = 0;
        let builderFields = []; // [{id, etiqueta, patron}]

        // Load available patterns from API
        fetch('/api/patterns')
            .then(r => r.json())
            .then(data => {
                patterns = data.patterns;
                patterns.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.name;
                    opt.textContent = `${p.name}`;
                    patternSelect.appendChild(opt);
                });
            });

        // Add field button
        addFieldBtn.addEventListener('click', () => {
            const selectedPattern = patternSelect.value;
            if (!selectedPattern) return;

            const patternInfo = patterns.find(p => p.name === selectedPattern);
            if (!patternInfo) return;

            const etiqueta = (fieldLabelInput.value || '').trim() || selectedPattern;

            fieldCounter++;
            const fieldId = `build_${fieldCounter}`;

            // Hide empty state, show create area
            if (emptyState) emptyState.style.display = 'none';
            if (createArea) createArea.style.display = 'flex';

            // Track field
            builderFields.push({ id: fieldId, etiqueta: etiqueta, patron: selectedPattern });

            // Create field element
            const fieldDiv = document.createElement('div');
            fieldDiv.className = 'dynamic-field';
            fieldDiv.id = fieldId;
            fieldDiv.innerHTML = `
                <div class="field-content">
                    <div class="field-label">
                        ${escapeHtml(etiqueta)}
                    </div>
                    <div class="field-hint">${escapeHtml(patternInfo.hint)}</div>
                    <div class="builder-badge">${escapeHtml(selectedPattern)}</div>
                </div>
                <button type="button" class="btn btn-danger btn-sm field-remove" data-remove="${fieldId}" title="Eliminar campo">✕</button>
            `;

            dynamicFields.appendChild(fieldDiv);

            // Remove button
            fieldDiv.querySelector('.field-remove').addEventListener('click', () => {
                fieldDiv.remove();
                builderFields = builderFields.filter(f => f.id !== fieldId);

                if (builderFields.length === 0) {
                    if (emptyState) emptyState.style.display = 'block';
                    if (createArea) createArea.style.display = 'none';
                }
            });

            // Reset inputs
            patternSelect.value = '';
            if (fieldLabelInput) fieldLabelInput.value = '';
        });

        // Create form button
        if (createFormBtn) {
            createFormBtn.addEventListener('click', async () => {
                const titulo = document.getElementById('formTitulo').value.trim();
                const descripcion = document.getElementById('formDescripcion').value.trim();
                const contrasena = document.getElementById('formContrasena').value.trim();

                if (!titulo) {
                    showToast('El título es obligatorio.', 'error');
                    document.getElementById('formTitulo').focus();
                    return;
                }
                if (!contrasena) {
                    showToast('La contraseña es obligatoria.', 'error');
                    document.getElementById('formContrasena').focus();
                    return;
                }
                if (builderFields.length === 0) {
                    showToast('Agrega al menos un campo.', 'error');
                    return;
                }

                createFormBtn.disabled = true;
                createFormBtn.textContent = 'Creando…';

                try {
                    const res = await fetch('/api/formularios', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            titulo,
                            descripcion,
                            contrasena,
                            preguntas: builderFields.map(f => ({
                                etiqueta: f.etiqueta,
                                patron: f.patron,
                            })),
                        }),
                    });

                    const data = await res.json();

                    if (res.ok) {
                        // Show success
                        document.getElementById('createSuccess').style.display = 'block';
                        document.getElementById('createdCode').textContent = data.codigo;
                        document.getElementById('createdTitle').textContent = data.titulo;
                        showToast('¡Formulario creado exitosamente!', 'success');
                    } else {
                        showToast(data.error || 'Error al crear el formulario.', 'error');
                    }
                } catch (err) {
                    showToast('Error de conexión con el servidor.', 'error');
                    console.error(err);
                } finally {
                    createFormBtn.disabled = false;
                    createFormBtn.textContent = 'Crear Formulario y Obtener Código';
                }
            });
        }

        // Copy code button
        const copyCodeBtn = document.getElementById('copyCodeBtn');
        if (copyCodeBtn) {
            copyCodeBtn.addEventListener('click', () => {
                const code = document.getElementById('createdCode').textContent;
                navigator.clipboard.writeText(code).then(() => {
                    copyCodeBtn.textContent = 'Copiado!';
                    setTimeout(() => { copyCodeBtn.textContent = 'Copiar'; }, 2000);
                });
            });
        }
    }


    // ========================================
    // TAB 2: RESPONDER FORMULARIO
    // ========================================
    const cargarFormBtn = document.getElementById('cargarFormBtn');
    const responderCodigo = document.getElementById('responderCodigo');
    const responderFormCard = document.getElementById('responderFormCard');
    const responderFields = document.getElementById('responderFields');
    const enviarRespuestaBtn = document.getElementById('enviarRespuestaBtn');
    const responderError = document.getElementById('responderError');

    let responderState = { codigo: '', preguntas: [], fieldStates: {} };

    if (cargarFormBtn && responderCodigo) {
        cargarFormBtn.addEventListener('click', async () => {
            const codigo = responderCodigo.value.trim().toUpperCase();
            if (!codigo) return;

            responderError.style.display = 'none';
            cargarFormBtn.disabled = true;
            cargarFormBtn.textContent = 'Cargando…';

            try {
                const res = await fetch(`/api/formularios/${codigo}`);
                const data = await res.json();

                if (res.ok) {
                    responderState.codigo = data.codigo;
                    responderState.preguntas = data.preguntas;
                    responderState.fieldStates = {};

                    // Render form
                    document.getElementById('responderTitulo').textContent = data.titulo;
                    document.getElementById('responderDesc').textContent = data.descripcion || '';
                    responderFields.innerHTML = '';

                    data.preguntas.forEach((p, i) => {
                        responderState.fieldStates[p.id] = { valid: false, value: '' };

                        const fieldDiv = document.createElement('div');
                        fieldDiv.className = 'dynamic-field';
                        fieldDiv.id = `resp_${p.id}`;
                        fieldDiv.innerHTML = `
                            <div class="field-content">
                                <div class="field-label">
                                    ${escapeHtml(p.etiqueta)}
                                </div>
                                <div class="field-hint">${escapeHtml(p.hint)}</div>
                                <input type="${p.patron === 'Contraseña Segura' ? 'password' : 'text'}"
                                       placeholder="Ingresa el valor…"
                                       data-pregunta-id="${p.id}"
                                       data-pattern="${escapeHtml(p.patron)}"
                                       autocomplete="off"
                                       class="field-input">
                                ${p.patron === 'Contraseña Segura' ? '<div class="password-strength"><div class="password-strength-bar" id="str_resp_' + p.id + '"></div></div>' : ''}
                                <div class="field-feedback" id="fb_resp_${p.id}"></div>
                            </div>
                        `;

                        responderFields.appendChild(fieldDiv);

                        // Attach validation
                        const input = fieldDiv.querySelector('.field-input');
                        let debounce = null;
                        input.addEventListener('input', () => {
                            clearTimeout(debounce);
                            const val = input.value;
                            responderState.fieldStates[p.id].value = val;

                            if (!val) {
                                input.className = 'field-input';
                                fieldDiv.className = 'dynamic-field';
                                document.getElementById(`fb_resp_${p.id}`).textContent = '';
                                document.getElementById(`fb_resp_${p.id}`).className = 'field-feedback';
                                responderState.fieldStates[p.id].valid = false;
                                updateResponderSubmit();
                                const strBar = document.getElementById(`str_resp_${p.id}`);
                                if (strBar) strBar.className = 'password-strength-bar';
                                return;
                            }

                            debounce = setTimeout(async () => {
                                const formData = new FormData();
                                formData.append('value', val);
                                formData.append('pattern', p.patron);

                                try {
                                    const res2 = await fetch('/validate-field', { method: 'POST', body: formData });
                                    const data2 = await res2.json();
                                    const fb = document.getElementById(`fb_resp_${p.id}`);

                                    if (data2.valid) {
                                        input.className = 'field-input field-valid';
                                        fieldDiv.className = 'dynamic-field field-row-valid';
                                        fb.textContent = 'Válido';
                                        fb.className = 'field-feedback valid';
                                        responderState.fieldStates[p.id].valid = true;
                                    } else {
                                        input.className = 'field-input field-invalid';
                                        fieldDiv.className = 'dynamic-field field-row-invalid';
                                        fb.textContent = 'Formato inválido';
                                        fb.className = 'field-feedback invalid';
                                        responderState.fieldStates[p.id].valid = false;
                                    }

                                    if (p.patron === 'Contraseña Segura') {
                                        updatePasswordStrength(`resp_${p.id}`, val);
                                    }

                                    updateResponderSubmit();
                                } catch (err) {
                                    console.error('Validation error:', err);
                                }
                            }, 250);
                        });
                    });

                    responderFormCard.style.display = 'block';
                    document.getElementById('respuestaResult').style.display = 'none';
                    updateResponderSubmit();
                } else {
                    responderError.textContent = data.error || 'Formulario no encontrado.';
                    responderError.style.display = 'block';
                    responderFormCard.style.display = 'none';
                }
            } catch (err) {
                responderError.textContent = 'Error de conexión con el servidor.';
                responderError.style.display = 'block';
                console.error(err);
            } finally {
                cargarFormBtn.disabled = false;
                cargarFormBtn.textContent = 'Cargar Formulario';
            }
        });
    }

    function updateResponderSubmit() {
        if (!enviarRespuestaBtn) return;
        const ids = Object.keys(responderState.fieldStates);
        const allValid = ids.length > 0 && ids.every(id => responderState.fieldStates[id].valid);
        enviarRespuestaBtn.disabled = !allValid;
    }

    if (enviarRespuestaBtn) {
        enviarRespuestaBtn.addEventListener('click', async () => {
            const datos = Object.entries(responderState.fieldStates).map(([preguntaId, state]) => ({
                pregunta_id: preguntaId,
                valor: state.value,
            }));

            enviarRespuestaBtn.disabled = true;
            enviarRespuestaBtn.textContent = 'Enviando…';

            try {
                const res = await fetch(`/api/formularios/${responderState.codigo}/respuestas`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ datos }),
                });

                const data = await res.json();
                const resultDiv = document.getElementById('respuestaResult');

                if (res.ok) {
                    resultDiv.innerHTML = `
                        <div class="form-summary">
                            <h3>Respuesta Enviada Exitosamente</h3>
                            <p>Se guardaron ${data.campos} campos correctamente. ¡Gracias por responder!</p>
                        </div>
                    `;
                    resultDiv.style.display = 'block';
                    showToast('¡Respuesta enviada!', 'success');
                } else {
                    resultDiv.innerHTML = `
                        <div class="form-summary" style="background:var(--accent-rose-glow);border-color:rgba(244,63,94,0.3);">
                            <h3 style="color:var(--accent-rose);">Error al Enviar</h3>
                            <p style="color:var(--text-secondary);">${escapeHtml(data.error || 'Error desconocido.')}</p>
                        </div>
                    `;
                    resultDiv.style.display = 'block';
                }
            } catch (err) {
                showToast('Error de conexión.', 'error');
                console.error(err);
            } finally {
                enviarRespuestaBtn.disabled = false;
                enviarRespuestaBtn.textContent = 'Enviar Respuesta';
            }
        });
    }


    // ========================================
    // TAB 3: VER RESPUESTAS
    // ========================================
    const verRespuestasBtn = document.getElementById('verRespuestasBtn');
    const resultadosCodigo = document.getElementById('resultadosCodigo');
    const resultadosContrasena = document.getElementById('resultadosContrasena');
    const resultadosError = document.getElementById('resultadosError');
    const resultadosPanel = document.getElementById('resultadosPanel');

    if (verRespuestasBtn && resultadosCodigo) {
        verRespuestasBtn.addEventListener('click', async () => {
            const codigo = resultadosCodigo.value.trim().toUpperCase();
            const contrasena = resultadosContrasena.value;

            if (!codigo) {
                resultadosError.textContent = 'Ingresa el código del formulario.';
                resultadosError.style.display = 'block';
                return;
            }
            if (!contrasena) {
                resultadosError.textContent = 'Ingresa la contraseña.';
                resultadosError.style.display = 'block';
                return;
            }

            resultadosError.style.display = 'none';
            verRespuestasBtn.disabled = true;
            verRespuestasBtn.textContent = 'Cargando…';

            try {
                const res = await fetch(`/api/formularios/${codigo}/respuestas/ver`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ contrasena }),
                });

                const data = await res.json();

                if (res.ok) {
                    document.getElementById('resultadosTitulo').textContent = `${data.titulo}`;
                    document.getElementById('resultadosCount').textContent = `${data.total_respuestas} respuesta(s)`;

                    const tablaDiv = document.getElementById('resultadosTabla');
                    const sinRespuestas = document.getElementById('sinRespuestas');

                    if (data.total_respuestas === 0) {
                        tablaDiv.innerHTML = '';
                        sinRespuestas.style.display = 'block';
                    } else {
                        sinRespuestas.style.display = 'none';

                        // Build table
                        let html = '<div class="responses-table-wrapper"><table class="responses-table">';
                        html += '<thead><tr><th>#</th>';
                        data.preguntas.forEach(p => {
                            html += `<th>${escapeHtml(p.etiqueta)}</th>`;
                        });
                        html += '<th>Fecha</th></tr></thead><tbody>';

                        data.respuestas.forEach((r, idx) => {
                            html += `<tr style="animation: fadeInUp 0.3s ease ${idx * 0.05}s backwards">`;
                            html += `<td class="row-number">${idx + 1}</td>`;

                            // Map datos by etiqueta for alignment
                            data.preguntas.forEach(p => {
                                const dato = r.datos.find(d => d.etiqueta === p.etiqueta);
                                html += `<td>${dato ? escapeHtml(dato.valor) : '<span class="text-muted">—</span>'}</td>`;
                            });

                            // Date
                            const fecha = r.respondido_en ? new Date(r.respondido_en).toLocaleString('es-CO') : '—';
                            html += `<td class="text-muted">${fecha}</td>`;
                            html += '</tr>';
                        });

                        html += '</tbody></table></div>';
                        tablaDiv.innerHTML = html;
                    }

                    resultadosPanel.style.display = 'block';
                } else {
                    resultadosError.textContent = data.error || 'Error al obtener respuestas.';
                    resultadosError.style.display = 'block';
                    resultadosPanel.style.display = 'none';
                }
            } catch (err) {
                resultadosError.textContent = 'Error de conexión con el servidor.';
                resultadosError.style.display = 'block';
                console.error(err);
            } finally {
                verRespuestasBtn.disabled = false;
                verRespuestasBtn.textContent = 'Ver Respuestas';
            }
        });
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
        return '';
    }

    function updatePasswordStrength(fieldId, value) {
        const bar = document.getElementById(`str_${fieldId}`);
        if (!bar) return;

        let score = 0;
        if (value.length >= 8) score++;
        if (/[A-Z]/.test(value)) score++;
        if (/[a-z]/.test(value)) score++;
        if (/[0-9]/.test(value)) score++;
        const levels = ['', 'strength-weak', 'strength-fair', 'strength-good', 'strength-strong'];
        bar.className = 'password-strength-bar ' + (levels[score] || '');
    }

    // Toast notification system
    function showToast(message, type = 'info') {
        // Remove existing toasts
        document.querySelectorAll('.toast').forEach(t => t.remove());

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('toast-visible');
        });

        setTimeout(() => {
            toast.classList.remove('toast-visible');
            setTimeout(() => toast.remove(), 350);
        }, 3000);
    }

    // ========================================
    // TRACE VISUALIZER LOGIC
    // ========================================
    let currentTraceSteps = [];
    let currentStepIdx = 0;
    let traceInterval = null;

    window.openTrace = function(type, text, traceData = null) {
        if (traceData) {
            setupTrace(type, text, traceData, null, null);
        } else if (window.currentTraceData && window.currentTraceText === text) {
            setupTrace(type, text, window.currentTraceData, window.currentEvaluations, window.currentGraphSyntax);
        }
    };

    window.fetchAndOpenTrace = async function(type, text) {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('type', type);
        try {
            const res = await fetch('/trace', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.trace) {
                setupTrace(type, text, data.trace, data.evaluations, data.graph_syntax);
            }
        } catch (e) { console.error(e); }
    };

    async function renderMermaidGraph(graphStr) {
        const container = document.getElementById('mermaidContainer');
        if (!container || !graphStr) return;
        try {
            // Save pan/zoom state
            let currentPan = null;
            let currentZoom = null;
            if (window.panZoomInstance) {
                currentPan = window.panZoomInstance.getPan();
                currentZoom = window.panZoomInstance.getZoom();
                window.panZoomInstance.destroy();
                window.panZoomInstance = null;
            }

            const id = 'mermaid-svg-' + Date.now();
            const { svg } = await mermaid.render(id, graphStr);
            container.innerHTML = svg;
            
            const svgElement = container.querySelector('svg');
            if (svgElement && window.svgPanZoom) {
                window.panZoomInstance = svgPanZoom(svgElement, {
                    zoomEnabled: true,
                    controlIconsEnabled: true,
                    fit: true,
                    center: true,
                    minZoom: 0.5,
                    maxZoom: 10
                });
                
                // Restore pan/zoom state
                if (currentPan !== null && currentZoom !== null) {
                    window.panZoomInstance.zoom(currentZoom);
                    window.panZoomInstance.pan(currentPan);
                }
            }
        } catch (e) {
            console.error('Mermaid render error', e);
        }
    }

    function setupTrace(type, text, traceData, evaluations = null, graphSyntax = null) {
        document.getElementById('traceModal').style.display = 'flex';
        
        // Mostrar cómo lo identificó
        let infoHtml = ``;
        if (evaluations && evaluations.length > 0) {
            infoHtml += `<div style="text-align:center; margin-bottom: 0.5rem;"><span class="badge">${type}</span></div>`;
            infoHtml += `<div class="decision-process">`;
            infoHtml += `<div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); margin-bottom: 0.5rem;">Proceso de Decisión:</div>`;
            
            evaluations.forEach(ev => {
                if (ev.status === 'rejected') {
                    const failChar = ev.failed_at === 'FIN_CADENA' ? 'Fin de cadena' : `'${ev.failed_at}'`;
                    infoHtml += `
                    <div class="decision-item">
                        <div class="decision-icon">❌</div>
                        <div class="decision-content">
                            <span class="decision-name">${ev.name}</span>
                            <span class="decision-reason">Rechazado al leer el carácter <span class="decision-char">${failChar}</span></span>
                        </div>
                    </div>`;
                } else if (ev.status === 'accepted') {
                    infoHtml += `
                    <div class="decision-item">
                        <div class="decision-icon">✅</div>
                        <div class="decision-content">
                            <span class="decision-name" style="color: #10B981;">${ev.name}</span>
                            <span class="decision-reason" style="color: #10B981;">¡Cadena aceptada exitosamente!</span>
                        </div>
                    </div>`;
                }
            });
            infoHtml += `</div>`;
        } else {
            infoHtml = `<div style="text-align:center;"><span class="badge">${type}</span></div>`;
        }
        document.querySelector('.trace-info').innerHTML = infoHtml;
        
        const textContainer = document.getElementById('traceTextDisplay');
        textContainer.innerHTML = '';
        for (let i = 0; i < text.length; i++) {
            const span = document.createElement('span');
            span.className = 'trace-char';
            span.textContent = text[i];
            textContainer.appendChild(span);
        }

        currentTraceSteps = traceData.steps || [];
        currentStepIdx = 0;
        window.currentBaseGraph = graphSyntax;
        clearInterval(traceInterval);
        
        document.getElementById('traceBtnPlay').textContent = 'Reproducir';
        updateTraceView();
    }

    function updateTraceView() {
        const chars = document.querySelectorAll('#traceTextDisplay .trace-char');
        chars.forEach((c, idx) => {
            if (idx === currentStepIdx && currentStepIdx < currentTraceSteps.length) {
                c.classList.add('highlight');
            } else {
                c.classList.remove('highlight');
            }
        });

        const btnPrev = document.getElementById('traceBtnPrev');
        const btnNext = document.getElementById('traceBtnNext');
        
        if (currentTraceSteps.length === 0) return;

        if (currentStepIdx >= currentTraceSteps.length) {
            const lastStep = currentTraceSteps[currentTraceSteps.length - 1];
            document.getElementById('traceCharRead').textContent = '✓ FIN';
            document.getElementById('traceStateFrom').textContent = lastStep.to;
            document.getElementById('traceStateTo').textContent = 'ACEPTADO';
            document.getElementById('traceStateTo').className = 'state-value success';
            btnNext.disabled = true;
            btnPrev.disabled = false;
            return;
        }

        const step = currentTraceSteps[currentStepIdx];
        document.getElementById('traceCharRead').textContent = step.char === ' ' ? 'ESPACIO' : step.char;
        document.getElementById('traceStateFrom').textContent = step.from;
        
        if (step.to === null) {
            document.getElementById('traceStateTo').textContent = 'RECHAZADO';
            document.getElementById('traceStateTo').className = 'state-value error';
            clearInterval(traceInterval);
            document.getElementById('traceBtnPlay').textContent = 'Reproducir';
            btnNext.disabled = true;
        } else {
            document.getElementById('traceStateTo').textContent = step.to;
            document.getElementById('traceStateTo').className = 'state-value';
            btnNext.disabled = false;
        }
        
        btnPrev.disabled = currentStepIdx === 0;
        
        btnPrev.disabled = currentStepIdx === 0;
        
        if (window.currentBaseGraph) {
            let activeState = null;
            let activeGraph = window.currentBaseGraph;
            
            if (currentStepIdx >= currentTraceSteps.length) {
                activeState = currentTraceSteps[currentTraceSteps.length - 1].to;
                activeGraph += `\n    class ${activeState} active;`;
            } else {
                activeState = currentTraceSteps[currentStepIdx].from;
                const nextState = currentTraceSteps[currentStepIdx].to;
                activeGraph += `\n    class ${activeState} active;`;
                
                if (nextState) {
                    const lines = window.currentBaseGraph.split('\n');
                    let linkIdx = 0;
                    for (let line of lines) {
                        if (line.includes('-->')) {
                            const parts = line.split('-->');
                            if (parts.length >= 2) {
                                const fromNode = parts[0].trim();
                                const toNodeMatch = parts[1].split('|');
                                const toNode = toNodeMatch[toNodeMatch.length - 1].trim();
                                if (fromNode === activeState && toNode === nextState) {
                                    activeGraph += `\n    linkStyle ${linkIdx} stroke:#F59E0B,stroke-width:4px;`;
                                    break;
                                }
                            }
                            linkIdx++;
                        }
                    }
                }
            }
            if (activeState) {
                renderMermaidGraph(activeGraph);
            }
        }
    }

    const closeTrace = document.getElementById('closeTrace');
    if (closeTrace) {
        closeTrace.addEventListener('click', () => {
            document.getElementById('traceModal').style.display = 'none';
            clearInterval(traceInterval);
        });
    }

    const btnNext = document.getElementById('traceBtnNext');
    if (btnNext) {
        btnNext.addEventListener('click', () => {
            if (currentStepIdx < currentTraceSteps.length) {
                currentStepIdx++;
                updateTraceView();
            }
        });
    }

    const btnPrev = document.getElementById('traceBtnPrev');
    if (btnPrev) {
        btnPrev.addEventListener('click', () => {
            if (currentStepIdx > 0) {
                currentStepIdx--;
                updateTraceView();
            }
        });
    }

    const btnPlay = document.getElementById('traceBtnPlay');
    if (btnPlay) {
        btnPlay.addEventListener('click', () => {
            if (traceInterval) {
                clearInterval(traceInterval);
                traceInterval = null;
                btnPlay.textContent = 'Reproducir';
            } else {
                if (currentStepIdx >= currentTraceSteps.length) {
                    currentStepIdx = 0;
                }
                btnPlay.textContent = 'Pausar';
                updateTraceView();
                traceInterval = setInterval(() => {
                    if (currentStepIdx < currentTraceSteps.length - 1) {
                        currentStepIdx++;
                        updateTraceView();
                    } else if (currentStepIdx === currentTraceSteps.length - 1) {
                        currentStepIdx++;
                        updateTraceView();
                        clearInterval(traceInterval);
                        traceInterval = null;
                        btnPlay.textContent = 'Reproducir';
                    } else {
                        clearInterval(traceInterval);
                        traceInterval = null;
                        btnPlay.textContent = 'Reproducir';
                    }
                }, 800);
            }
        });
    }

});
