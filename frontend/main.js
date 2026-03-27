import './style.css';

// Adaptable para acceder desde la Mac, iPad o red local usando la IP de esta PC
const API_BASE_URL = `http://${window.location.hostname}:8000/api/prospectos`;

// Elementos del DOM
const leadsBody = document.getElementById('leadsBody');
const leadCount = document.getElementById('leadCount');
const prospectForm = document.getElementById('prospectForm');

// Polling dinámico: Si hay algo "investigando", refrescamos más seguido
let pollingInterval = null;

function startPolling() {
    if (pollingInterval) return;
    console.log("[POLLING] Activado - Esperando resultados de auditoría...");
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(API_BASE_URL + '/');
            const leads = await response.json();
            
            // Ordenar consistentemente
            leads.sort((a, b) => new Date(b.creado_en) - new Date(a.creado_en));

            // Si ya no hay nadie investigando, paramos el polling
            const hayInvestigando = leads.some(l => l.estado === 'investigando');
            if (!hayInvestigando) {
                stopPolling();
            }
            
            renderLeads(leads);
        } catch (e) {
            console.error("Error en polling:", e);
        }
    }, 3000);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        console.log("[POLLING] Detenido - Estados sincronizados.");
    }
}

// Función para obtener y renderizar los leads
async function fetchLeads() {
    try {
        const response = await fetch(API_BASE_URL + '/');
        if (!response.ok) throw new Error('Error listando prospectos');
        const leads = await response.json();
        
        // Ordenar por fecha (más recientes primero)
        leads.sort((a, b) => new Date(b.creado_en) - new Date(a.creado_en));
        renderLeads(leads);

        // Si al cargar el Dashboard ya hay tareas pendientes, iniciar polling
        if (leads.some(l => l.estado === 'investigando')) {
            startPolling();
        }
    } catch (error) {
        console.error("No se pudo conectar al orquestador:", error);
        leadsBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--neon-pink);">Error de conexión con el Backend.</td></tr>`;
    }
}

// Renderizado de tabla
function renderLeads(leads) {
    leadCount.textContent = `${leads.length} prospectos`;
    leadsBody.innerHTML = '';

    if(leads.length === 0) {
        leadsBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Sin leads registrados. Empiece su prospección.</td></tr>`;
        return;
    }

    leads.forEach(lead => {
        // Determinar el teléfono a mostrar
        const telefonoDisplay = lead.telefono || lead.telefono_dueno || (lead.telefonos_hallados ? lead.telefonos_hallados.split(',')[0] : null);
        const contactoDisplay = lead.nombre_dueno || lead.contacto_clave || 'Desconocido';

        // Badge de contacto si tenemos teléfono o email
        const contactoBadge = (lead.telefono || lead.email) ?
            `<span style="color: var(--neon-green); font-size: 0.7rem;">✓ Datos de contacto</span>` : '';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <strong>${lead.empresa}</strong>
                ${telefonoDisplay ? `<div style="font-size: 0.75rem; color: var(--neon-blue);">📞 ${telefonoDisplay}</div>` : ''}
            </td>
            <td><a href="${lead.url || '#'}" target="_blank" style="color: var(--neon-blue); text-decoration: none;">${lead.url ? new URL(lead.url).hostname : 'N/A'}</a></td>
            <td>
                ${contactoDisplay}
                ${contactoBadge}
            </td>
            <td>
                <div style="font-size: 0.8rem; color: var(--text-muted); max-width: 250px;">
                    <strong style="color: ${lead.falla_detectada && (lead.falla_detectada.includes('⚠️') || lead.falla_detectada.includes('📱') || lead.falla_detectada.includes('🐌')) ? 'var(--neon-pink)' : 'var(--neon-green)'};">${lead.falla_detectada || 'Pendiente'}</strong>
                </div>
            </td>
            <td><span class="state-tag state-${lead.estado}">${lead.estado.toUpperCase()}</span></td>
            <td>
                ${(lead.estado === 'nuevo' || lead.estado === 'contactado' || lead.estado === 'perdido') && lead.url ? `
                    <button onclick="iniciarAuditoria(${lead.id})" class="neon-btn secondary" style="padding: 4px 8px; font-size: 0.75rem; margin-right: 5px;">
                        ${(lead.estado === 'contactado' || lead.estado === 'perdido') ? 'RE-AUDITAR' : 'AUDITAR'}
                    </button>` : ''}
                ${lead.estado === 'contactado' ? `<button onclick="openReport(${lead.id})" class="neon-btn" style="padding: 4px 8px; font-size: 0.75rem; margin-right: 5px; border-color: var(--neon-green); color: var(--neon-green);">INFORME</button>` : ''}
                <button onclick="deleteLead(${lead.id})" style="background: transparent; border: 1px solid rgba(255,255,255,0.2); color: var(--text-muted); padding: 4px 8px; border-radius: 4px; cursor: pointer; transition: 0.3s; font-size: 0.75rem;">X</button>
            </td>
        `;
        leadsBody.appendChild(tr);
    });
}

// LÓGICA DE MODAL E INFORME
const reportModal = document.getElementById('reportModal');
const modalBody = document.getElementById('modalBody');
const modalTitle = document.getElementById('modalTitle');
let currentLeadId = null;

window.openReport = async (id) => {
    currentLeadId = id;
    try {
        const response = await fetch(`${API_BASE_URL}/${id}`);
        const lead = await response.json();
        console.log("[INFORME] Datos del Lead:", lead);

        modalTitle.textContent = `Auditoría: ${lead.empresa || 'Prospecto'}`;

        // Parsear JSON si viene como string
        let informe = lead.informe_detallado;
        if (typeof informe === 'string') {
            try { informe = JSON.parse(informe); } catch(e) { console.error("Error parseando informe", e); }
        }
        informe = informe || {};

        // === SECCIÓN 1: FICHA DE EMPRESA ===
        let fichaHTML = '';
        const tieneDatosEnriquecidos = lead.nombre_dueno || lead.telefono || lead.direccion || (lead.redes_sociales && Object.keys(lead.redes_sociales).length > 0);

        if (tieneDatosEnriquecidos) {
            fichaHTML = `
                <div class="ficha-empresa">
                    <h3>🏢 Ficha de Empresa</h3>
                    <div class="ficha-grid">
                        ${lead.nombre_dueno ? `
                            <div class="ficha-item">
                                <span class="ficha-label">👤 Responsable</span>
                                <span class="ficha-value">${lead.nombre_dueno}${lead.cargo_dueno ? ` (${lead.cargo_dueno})` : ''}</span>
                            </div>
                        ` : ''}
                        ${lead.telefono ? `
                            <div class="ficha-item">
                                <span class="ficha-label">📞 Teléfono</span>
                                <span class="ficha-value">${lead.telefono}</span>
                                ${lead.telefono_dueno && lead.telefono_dueno !== lead.telefono ? `<small style="color: var(--text-muted)">Móvil: ${lead.telefono_dueno}</small>` : ''}
                            </div>
                        ` : ''}
                        ${lead.email ? `
                            <div class="ficha-item">
                                <span class="ficha-label">✉️ Email</span>
                                <span class="ficha-value">${lead.email}</span>
                            </div>
                        ` : ''}
                        ${lead.direccion ? `
                            <div class="ficha-item wide">
                                <span class="ficha-label">📍 Dirección</span>
                                <span class="ficha-value">${lead.direccion}${lead.ciudad ? `, ${lead.ciudad}` : ''}${lead.provincia ? `, ${lead.provincia}` : ''}</span>
                            </div>
                        ` : ''}
                        ${lead.redes_sociales && Object.keys(lead.redes_sociales).length > 0 ? `
                            <div class="ficha-item wide">
                                <span class="ficha-label">🌐 Redes Sociales</span>
                                <div class="social-links">
                                    ${Object.entries(lead.redes_sociales).map(([network, link]) => `
                                        <a href="${link.startsWith('http') ? link : 'https://' + link}" target="_blank" class="social-link ${network}">${network}</a>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        ${lead.antiguedad_dominio ? `
                            <div class="ficha-item">
                                <span class="ficha-label">📅 Antigüedad</span>
                                <span class="ficha-value">${lead.antiguedad_dominio} años</span>
                            </div>
                        ` : ''}
                    </div>
                    ${lead.paginas_auditadas > 0 ? `<p class="audit-meta">📊 ${lead.paginas_auditadas} páginas analizadas</p>` : ''}
                </div>
            `;
        }

        // === SECCIÓN 2: PILARES DE AUDITORÍA ===
        const pilares = informe.pilares || {};
        const pilarEntries = Object.entries(pilares);

        let pillarsHTML = '<div class="pillars-grid">';
        if (pilarEntries.length === 0) {
            pillarsHTML += '<p style="color: var(--neon-pink); grid-column: 1/-1;">⚠️ No hay datos de auditoría disponibles.</p>';
        } else {
            for (const [key, data] of pilarEntries) {
                pillarsHTML += `
                    <div class="pillar-card">
                        <h3>${key}</h3>
                        <span class="pillar-status status-${data.estado || 'alerta'}">${(data.estado || '???').toUpperCase()}</span>
                        <p class="pillar-desc">${data.detalle || 'Sin detalle disponible.'}</p>
                    </div>
                `;
            }
        }
        pillarsHTML += '</div>';

        // === SECCIÓN 3: DATOS TÉCNICOS ADICIONALES ===
        let techDetailsHTML = '';
        const performance = informe.performance;
        const seo = informe.seo;
        const techs = informe.tecnologias;

        if (performance || seo || (techs && techs.length > 0)) {
            techDetailsHTML = `
                <div class="tech-details">
                    <h3>🔧 Métricas Técnicas</h3>
                    <div class="tech-grid">
                        ${performance ? `
                            <div class="tech-section">
                                <h4>Performance</h4>
                                <ul>
                                    <li>Tiempo de carga: <strong>${performance.loadTime}ms</strong></li>
                                    <li>Tamaño total: <strong>${performance.totalSizeKB}KB</strong></li>
                                    <li>Recursos: <strong>${performance.resourcesCount}</strong></li>
                                </ul>
                            </div>
                        ` : ''}
                        ${seo ? `
                            <div class="tech-section">
                                <h4>SEO</h4>
                                <ul>
                                    <li>Título: ${seo.titleLength} chars</li>
                                    <li>H1: ${seo.h1Count}</li>
                                    <li>Imágenes sin alt: ${seo.imagesSinAlt}</li>
                                </ul>
                            </div>
                        ` : ''}
                        ${techs && techs.length > 0 ? `
                            <div class="tech-section wide">
                                <h4>Tecnologías Detectadas</h4>
                                <div class="tech-tags">
                                    ${techs.map(t => `<span class="tech-tag">${t}</span>`).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        // === SECCIÓN 4: CONTACTOS ADICIONALES ===
        let contactsHTML = '';
        const emails = lead.emails_hallados ? lead.emails_hallados.split(',').filter(e => e.trim()) : [];
        const telefonos = lead.telefonos_hallados ? lead.telefonos_hallados.split(',').filter(t => t.trim()) : [];

        if (emails.length > 0 || telefonos.length > 0) {
            contactsHTML = `
                <div class="contacts-found">
                    <h3>📧 Contactos Adicionales Detectados</h3>
                    ${emails.length > 0 ? `
                        <div class="contact-list">
                            <span class="contact-label">Emails:</span>
                            ${emails.slice(0, 5).map(e => `<span class="contact-item">${e.trim()}</span>`).join(', ')}
                        </div>
                    ` : ''}
                    ${telefonos.length > 0 ? `
                        <div class="contact-list">
                            <span class="contact-label">Teléfonos:</span>
                            ${telefonos.slice(0, 5).map(t => `<span class="contact-item">${t.trim()}</span>`).join(', ')}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // === SECCIÓN 5: PUNTOS DE DOLOR (PITCH) ===
        const pitchHTML = `
            <div class="sales-box">
                <h3>🎯 Argumentos de Venta (Puntos de Dolor)</h3>
                <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                    💡 Edita este texto para personalizar tu propuesta comercial:
                </p>
                <textarea id="salesPitchText" placeholder="Aquí aparecerán los argumentos de venta...">${lead.puntos_de_dolor || ""}</textarea>
            </div>
        `;

        // Armar modal completo
        modalBody.innerHTML = `
            ${fichaHTML}
            ${pillarsHTML}
            ${techDetailsHTML}
            ${contactsHTML}
            ${pitchHTML}
        `;

        reportModal.classList.add('active');
    } catch (e) {
        console.error(e);
        alert("Error cargando el informe. Revisa la consola.");
    }
};

document.getElementById('closeModal').onclick = () => reportModal.classList.remove('active');

document.getElementById('btnSaveReport').onclick = async () => {
    const newPitch = document.getElementById('salesPitchText').value;
    try {
        const response = await fetch(`${API_BASE_URL}/${currentLeadId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ puntos_de_dolor: newPitch })
        });
        
        if (response.ok) {
            alert("Informe actualizado correctamente.");
            reportModal.classList.remove('active');
            fetchLeads();
        }
    } catch (e) {
        alert("Error al guardar cambios.");
    }
};

window.iniciarAuditoria = async (id) => {
    try {
        const response = await fetch(`${API_BASE_URL}/${id}/iniciar-auditoria`, { method: 'POST' });
        if(response.ok) {
            fetchLeads(); // Refresco inmediato para mostrar "investigando"
            startPolling(); // Iniciar el seguimiento automático
        } else {
            const data = await response.json();
            alert("Error: " + data.detail);
        }
    } catch(e) {
        alert("Fallo la red al contactar al Orquestador.");
    }
};

// Formulario de creación
prospectForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = prospectForm.querySelector('button[type="submit"]');
    btn.textContent = "Agregando...";
    
    const nuevoLead = {
        empresa: document.getElementById('empresa').value,
        url: document.getElementById('url').value || null,
        contacto_clave: document.getElementById('contacto').value || null,
        estado: "nuevo"
    };

    try {
        const response = await fetch(API_BASE_URL + '/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nuevoLead)
        });
        
        if (response.ok) {
            prospectForm.reset();
            await fetchLeads();
        } else {
            alert("Error al agregar lead");
        }
    } catch (error) {
        console.error(error);
        alert("Fallo la red");
    } finally {
        btn.textContent = "Añadir Lead (Local)";
    }
});

// Función global para eliminar
window.deleteLead = async (id) => {
    if(!confirm('¿Eliminar prospecto?')) return;
    try {
        await fetch(`${API_BASE_URL}/${id}`, { method: 'DELETE' });
        fetchLeads();
    } catch(e) {
        alert("Error borrando lead.");
    }
};

document.getElementById('btnAutoStart').addEventListener('click', async () => {
    try {
        const response = await fetch(API_BASE_URL + '/');
        const leads = await response.json();
        const target = leads.find(l => l.estado === 'nuevo' && l.url); // Tomar el primero apto
        if(!target) return alert("No hay leads 'nuevos' que tengan URL web para auditar.");
        iniciarAuditoria(target.id);
    } catch (e) {
        alert("Error de conexión consultando leads.");
    }
});

// Cargar la vista inicialmente
fetchLeads();
