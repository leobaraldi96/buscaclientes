import './style.css';

// Adaptable para acceder desde la Mac, iPad o red local usando la IP de esta PC
const API_BASE_URL = `http://${window.location.hostname}:8000/api/prospectos`;

// Elementos del DOM
const leadsBody = document.getElementById('leadsBody');
const leadCount = document.getElementById('leadCount');
const prospectForm = document.getElementById('prospectForm');

// Función para obtener y renderizar los leads
async function fetchLeads() {
    try {
        const response = await fetch(API_BASE_URL + '/');
        if (!response.ok) throw new Error('Error listando prospectos');
        const leads = await response.json();
        // Ordenar por fecha (más recientes primero)
        leads.sort((a, b) => new Date(b.creado_en) - new Date(a.creado_en));
        renderLeads(leads);
    } catch (error) {
        console.error("No se pudo conectar al orquestador:", error);
        leadsBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--neon-pink);">Error de conexión con el Backend. ¿Está encendido FastAPI?</td></tr>`;
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
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${lead.empresa}</strong></td>
            <td><a href="${lead.url || '#'}" target="_blank" style="color: var(--neon-blue); text-decoration: none;">${lead.url ? new URL(lead.url).hostname : 'N/A'}</a></td>
            <td>${lead.contacto_clave || 'Desconocido'}</td>
            <td>
                <div style="font-size: 0.8rem; color: var(--text-muted); max-width: 250px;">
                    <strong style="color: ${lead.falla_detectada && (lead.falla_detectada.includes('⚠️') || lead.falla_detectada.includes('📱') || lead.falla_detectada.includes('🐌')) ? 'var(--neon-pink)' : 'var(--neon-green)'};">${lead.falla_detectada || 'Pendiente'}</strong>
                </div>
            </td>
            <td><span class="state-tag state-${lead.estado}">${lead.estado.toUpperCase()}</span></td>
            <td>
                ${lead.estado === 'nuevo' && lead.url ? `<button onclick="iniciarAuditoria(${lead.id})" class="neon-btn secondary" style="padding: 4px 8px; font-size: 0.75rem; margin-right: 5px;">AUDITAR</button>` : ''}
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
        
        modalTitle.textContent = `Auditoría: ${lead.empresa}`;
        
        const inf = lead.informe_detallado || { pilares: {} };
        const pilares = inf.pilares || {};
        
        let pillarsHTML = '<div class="pillars-grid">';
        for (const [key, data] of Object.entries(pilares)) {
            pillarsHTML += `
                <div class="pillar-card">
                    <h3>${key}</h3>
                    <span class="pillar-status status-${data.estado}">${data.estado.toUpperCase()}</span>
                    <p class="pillar-desc">${data.detalle}</p>
                </div>
            `;
        }
        pillarsHTML += '</div>';

        modalBody.innerHTML = `
            ${pillarsHTML}
            <div class="sales-box">
                <h3>Resumen Estratégico de Venta (Puntos de Dolor)</h3>
                <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;">Edita este texto para personalizar tu propuesta comercial:</p>
                <textarea id="salesPitchText">${lead.puntos_de_dolor || ""}</textarea>
            </div>
        `;
        
        reportModal.classList.add('active');
    } catch (e) {
        alert("Error cargando el informe.");
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

// ... Resto de funciones (iniciarAuditoria, deleteLead, etc.) ya existentes abajo

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

// Función global para eliminar (mala práctica global pero rápido para Vite Vanilla prototipo)
window.deleteLead = async (id) => {
    if(!confirm('¿Eliminar prospecto?')) return;
    try {
        await fetch(`${API_BASE_URL}/${id}`, { method: 'DELETE' });
        fetchLeads();
    } catch(e) {
        alert("Error borrando lead.");
    }
};

window.iniciarAuditoria = async (id) => {
    try {
        const response = await fetch(`${API_BASE_URL}/${id}/iniciar-auditoria`, { method: 'POST' });
        if(response.ok) {
            fetchLeads(); // Refrescar para ver el cambio inmediato a "investigando"
            // Programar otro refresco en 6s para ver el regreso ("contactado" del Worker falso)
            setTimeout(fetchLeads, 6000);
        } else {
            const data = await response.json();
            alert("Error: " + data.detail);
        }
    } catch(e) {
        alert("Fallo la red al contactar al Orquestador.");
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
