document.addEventListener('DOMContentLoaded', () => {

    // ============================================================
    // Tab Switching
    // ============================================================
    const tabs = document.querySelectorAll('.tab');
    const panels = document.querySelectorAll('.tab-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById('panel' + capitalize(tab.dataset.tab)).classList.add('active');
        });
    });

    function capitalize(s) {
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    // ============================================================
    // TAB 1: Drug Lookup
    // ============================================================
    const drugInput = document.getElementById('drugInput');
    const searchBtn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const errorBox = document.getElementById('errorBox');
    const results = document.getElementById('results');

    const resName = document.getElementById('resName');
    const resRxCui = document.getElementById('resRxCui');
    const resGenericPills = document.getElementById('resGenericPills');
    const labelCards = document.getElementById('labelCards');
    const detailSections = document.getElementById('detailSections');

    // Hint chips
    document.querySelectorAll('.hint').forEach(hint => {
        hint.addEventListener('click', () => {
            drugInput.value = hint.dataset.drug;
            performSearch();
        });
    });

    searchBtn.addEventListener('click', performSearch);
    drugInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    async function performSearch() {
        const query = drugInput.value.trim();
        if (!query) return;

        errorBox.classList.add('hidden');
        results.classList.add('hidden');
        loading.classList.remove('hidden');

        try {
            const response = await fetch(`/api/drugs/${encodeURIComponent(query)}`);
            let data;
            const ct = response.headers.get('content-type');
            if (ct && ct.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                throw new Error(text || 'Internal Server Error');
            }

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to fetch drug information.');
            }

            renderResults(data);
            loading.classList.add('hidden');
            results.classList.remove('hidden');
        } catch (err) {
            loading.classList.add('hidden');
            errorBox.textContent = err.message;
            errorBox.classList.remove('hidden');
        }
    }

    function renderResults(data) {
        resName.textContent = data.name;

        if (data.rxcui) {
            resRxCui.textContent = `RxCUI ${data.rxcui}`;
            resRxCui.style.display = 'inline-block';
        } else {
            resRxCui.style.display = 'none';
        }

        const allGenerics = new Set();
        data.labels.forEach(l => l.generic_names.forEach(n => allGenerics.add(n)));
        resGenericPills.innerHTML = '';
        allGenerics.forEach(name => {
            const el = document.createElement('span');
            el.className = 'meta-pill';
            el.textContent = name;
            resGenericPills.appendChild(el);
        });

        labelCards.innerHTML = '';
        data.labels.forEach((label, idx) => {
            const card = document.createElement('div');
            card.className = 'label-card' + (idx === 0 ? ' active' : '');
            card.innerHTML = `
                <div class="lc-brand">${label.brand_names[0] || label.generic_names[0] || 'Unknown'}</div>
                <div class="lc-manufacturer">${label.manufacturer[0] || 'Unknown manufacturer'}</div>
                ${label.route[0] ? `<span class="lc-route">${label.route[0]}</span>` : ''}
            `;
            card.addEventListener('click', () => {
                document.querySelectorAll('.label-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                renderDetail(label);
            });
            labelCards.appendChild(card);
        });

        if (data.labels.length > 0) {
            renderDetail(data.labels[0]);
        }
    }

    function renderDetail(label) {
        const sections = buildSections(label);
        detailSections.innerHTML = '';

        // Quick info row
        const quickRow = document.createElement('div');
        quickRow.className = 'quick-row';
        if (label.brand_names.length) {
            label.brand_names.forEach(b => {
                quickRow.innerHTML += `<span class="quick-chip chip-brand">${b}</span>`;
            });
        }
        if (label.substance_name.length) {
            label.substance_name.forEach(s => {
                quickRow.innerHTML += `<span class="quick-chip chip-substance">${s}</span>`;
            });
        }
        if (label.product_type) {
            quickRow.innerHTML += `<span class="quick-chip chip-type">${label.product_type}</span>`;
        }
        detailSections.appendChild(quickRow);

        // Accordion sections
        sections.forEach((section, idx) => {
            const el = document.createElement('div');
            el.className = 'detail-section' + (idx === 0 ? ' open' : '');

            const chevronSvg = `<svg class="detail-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>`;

            el.innerHTML = `
                <div class="detail-header">
                    <div class="detail-header-left">
                        <span class="detail-dot dot-${section.dot}"></span>
                        <span class="detail-header-title">${section.title}</span>
                    </div>
                    ${chevronSvg}
                </div>
                <div class="detail-body">
                    <div class="detail-content${section.text ? '' : ' empty'}">
                        ${section.text || 'Not available for this label.'}
                    </div>
                </div>
            `;

            el.querySelector('.detail-header').addEventListener('click', () => {
                el.classList.toggle('open');
            });

            detailSections.appendChild(el);
        });
    }

    function buildSections(label) {
        return [
            { title: 'Active Ingredient', text: label.active_ingredient, dot: 'success' },
            { title: 'Indications & Usage', text: label.indications_and_usage, dot: 'info' },
            { title: 'Dosage & Administration', text: label.dosage_and_administration, dot: 'info' },
            { title: 'Adverse Reactions', text: label.adverse_reactions, dot: 'danger' },
            { title: 'Contraindications', text: label.contraindications, dot: 'danger' },
            { title: 'Warnings', text: label.warnings, dot: 'warning' },
            { title: 'Stop Use', text: label.stop_use, dot: 'warning' },
            { title: 'Ask Doctor / Pharmacist', text: label.ask_doctor, dot: 'warning' },
            { title: 'Pregnancy / Breast-Feeding', text: label.pregnancy_or_breast_feeding, dot: 'warning' },
            { title: 'Description', text: label.description, dot: 'neutral' },
        ].filter(s => s.text);
    }

    // ============================================================
    // TAB 2: Interaction Checker
    // ============================================================
    const ixDrugList = document.getElementById('ixDrugList');
    const ixAddBtn = document.getElementById('ixAddBtn');
    const ixCheckBtn = document.getElementById('ixCheckBtn');
    const ixLoading = document.getElementById('ixLoading');
    const ixError = document.getElementById('ixError');
    const ixResults = document.getElementById('ixResults');
    const ixSummary = document.getElementById('ixSummary');
    const ixFlags = document.getElementById('ixFlags');
    const ixDrugDetails = document.getElementById('ixDrugDetails');

    let drugRowCount = 2;

    // Add drug row
    ixAddBtn.addEventListener('click', () => {
        if (drugRowCount >= 6) return;
        drugRowCount++;
        const row = document.createElement('div');
        row.className = 'ix-drug-row';
        row.innerHTML = `
            <input type="text" class="ix-input" placeholder="Drug ${drugRowCount}" autocomplete="off" spellcheck="false" />
            <button class="ix-remove-btn" aria-label="Remove">×</button>
        `;
        row.querySelector('.ix-remove-btn').addEventListener('click', () => {
            row.remove();
            drugRowCount--;
            updateRemoveButtons();
        });
        ixDrugList.appendChild(row);
        updateRemoveButtons();
        row.querySelector('.ix-input').focus();
    });

    function updateRemoveButtons() {
        const rows = ixDrugList.querySelectorAll('.ix-drug-row');
        rows.forEach(r => {
            const btn = r.querySelector('.ix-remove-btn');
            if (rows.length > 2) {
                btn.classList.remove('hidden');
            } else {
                btn.classList.add('hidden');
            }
        });
    }

    // Check interactions
    ixCheckBtn.addEventListener('click', performInteractionCheck);

    // Allow Enter key in any interaction input
    ixDrugList.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.classList.contains('ix-input')) {
            performInteractionCheck();
        }
    });

    async function performInteractionCheck() {
        const inputs = ixDrugList.querySelectorAll('.ix-input');
        const drugNames = [];
        inputs.forEach(input => {
            const val = input.value.trim();
            if (val) drugNames.push(val);
        });

        if (drugNames.length < 2) {
            ixError.textContent = 'Please enter at least 2 drug names.';
            ixError.classList.remove('hidden');
            return;
        }

        ixError.classList.add('hidden');
        ixResults.classList.add('hidden');
        ixLoading.classList.remove('hidden');

        try {
            const response = await fetch(`/api/interactions?drugs=${encodeURIComponent(drugNames.join(','))}`);
            let data;
            const ct = response.headers.get('content-type');
            if (ct && ct.includes('application/json')) {
                data = await response.json();
            } else {
                throw new Error(await response.text() || 'Server error');
            }

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to check interactions.');
            }

            renderInteractionResults(data);
            ixLoading.classList.add('hidden');
            ixResults.classList.remove('hidden');
        } catch (err) {
            ixLoading.classList.add('hidden');
            ixError.textContent = err.message;
            ixError.classList.remove('hidden');
        }
    }

    function renderInteractionResults(data) {
        // Summary banner
        const hasWarnings = data.flags.some(f => f.severity === 'warning');
        const hasFlags = data.flags.length > 0;

        let summaryClass = 'safe';
        let summaryIcon = '✓';
        if (hasWarnings) {
            summaryClass = 'danger';
            summaryIcon = '⚠';
        } else if (hasFlags) {
            summaryClass = 'warning';
            summaryIcon = '⚡';
        }

        ixSummary.className = `ix-summary ${summaryClass}`;
        ixSummary.innerHTML = `<span>${summaryIcon}</span> ${data.summary}`;

        // Interaction flags
        ixFlags.innerHTML = '';
        if (data.flags.length > 0) {
            data.flags.forEach(flag => {
                const card = document.createElement('div');
                card.className = `ix-flag-card${flag.severity === 'warning' ? ' severity-warning' : ''}`;
                card.innerHTML = `
                    <div class="ix-flag-pair">
                        <span class="ix-flag-drug">${flag.drug_a}</span>
                        <span class="ix-flag-arrow">↔</span>
                        <span class="ix-flag-drug">${flag.drug_b}</span>
                        <span class="ix-flag-severity ${flag.severity}">${flag.severity}</span>
                    </div>
                    <div class="ix-flag-detail">${flag.detail}</div>
                `;
                ixFlags.appendChild(card);
            });
        }

        // Per-drug full interaction text (collapsible)
        ixDrugDetails.innerHTML = '';
        const drugsWithText = data.drugs.filter(d => d.interaction_text);

        if (drugsWithText.length > 0) {
            const header = document.createElement('h3');
            header.className = 'section-label';
            header.style.marginTop = '0.5rem';
            header.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                Full Interaction Details
            `;
            ixDrugDetails.appendChild(header);

            drugsWithText.forEach(drug => {
                const detail = document.createElement('div');
                detail.className = 'ix-drug-detail';

                const chevronSvg = `<svg class="detail-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>`;

                detail.innerHTML = `
                    <div class="ix-drug-detail-header">
                        <span class="ix-drug-detail-name">${drug.drug_name}</span>
                        ${chevronSvg}
                    </div>
                    <div class="ix-drug-detail-body">
                        <div class="ix-drug-detail-content">${drug.interaction_text}</div>
                    </div>
                `;

                detail.querySelector('.ix-drug-detail-header').addEventListener('click', () => {
                    detail.classList.toggle('open');
                });

                ixDrugDetails.appendChild(detail);
            });
        }
    }
});
