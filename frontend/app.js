document.addEventListener('DOMContentLoaded', () => {
    const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
    const panels = Array.from(document.querySelectorAll('[role="tabpanel"]'));

    function activateTab(tab) {
        tabs.forEach((item) => {
            const selected = item === tab;
            item.classList.toggle('active', selected);
            item.setAttribute('aria-selected', String(selected));
            item.tabIndex = selected ? 0 : -1;
        });
        panels.forEach((panel) => {
            const selected = panel.id === tab.getAttribute('aria-controls');
            panel.classList.toggle('active', selected);
            panel.hidden = !selected;
        });
    }

    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => activateTab(tab));
        tab.addEventListener('keydown', (event) => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
            event.preventDefault();
            let nextIndex = index;
            if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
            if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
            if (event.key === 'Home') nextIndex = 0;
            if (event.key === 'End') nextIndex = tabs.length - 1;
            tabs[nextIndex].focus();
            activateTab(tabs[nextIndex]);
        });
    });

    const drugInput = document.getElementById('drugInput');
    const searchBtn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const errorBox = document.getElementById('errorBox');
    const results = document.getElementById('results');
    const lookupStatus = document.getElementById('lookupStatus');
    const resName = document.getElementById('resName');
    const resRxCui = document.getElementById('resRxCui');
    const resMeta = document.getElementById('resMeta');
    const labelSelect = document.getElementById('labelSelect');
    const labelProvenance = document.getElementById('labelProvenance');
    const sectionNav = document.getElementById('sectionNav');
    const detailSections = document.getElementById('detailSections');

    document.querySelectorAll('[data-drug]').forEach((button) => {
        button.addEventListener('click', () => {
            drugInput.value = button.dataset.drug || '';
            performSearch();
        });
    });

    searchBtn.addEventListener('click', performSearch);
    drugInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') performSearch();
    });

    function setLookupBusy(isBusy) {
        searchBtn.disabled = isBusy;
        drugInput.setAttribute('aria-busy', String(isBusy));
        loading.classList.toggle('hidden', !isBusy);
    }

    async function performSearch() {
        const query = drugInput.value.trim();
        if (!query) {
            drugInput.focus();
            return;
        }

        errorBox.classList.add('hidden');
        results.classList.add('hidden');
        setLookupBusy(true);
        lookupStatus.textContent = `Searching FDA labels for ${query}.`;

        try {
            const response = await fetch(`/api/drugs/${encodeURIComponent(query)}`);
            const data = await readJsonResponse(response);
            if (!response.ok) throw new Error(data.detail || 'Unable to retrieve medication information.');
            renderDrug(data);
            results.classList.remove('hidden');
            lookupStatus.textContent = `Loaded ${data.label_count} FDA label record${data.label_count === 1 ? '' : 's'} for ${data.name}.`;
            results.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' });
        } catch (error) {
            errorBox.textContent = error.message;
            errorBox.classList.remove('hidden');
            lookupStatus.textContent = 'Medication lookup failed.';
        } finally {
            setLookupBusy(false);
        }
    }

    function renderDrug(data) {
        resName.textContent = titleCase(data.name || drugInput.value.trim());
        if (data.rxcui) {
            resRxCui.textContent = `RxCUI ${data.rxcui}`;
            resRxCui.classList.remove('hidden');
        } else {
            resRxCui.textContent = '';
            resRxCui.classList.add('hidden');
        }
        resMeta.textContent = `${data.label_count} FDA label record${data.label_count === 1 ? '' : 's'} retrieved. DrugLens requests up to ${data.retrieval_limit || 5} records per search.`;

        labelSelect.replaceChildren();
        data.labels.forEach((label, index) => {
            const option = document.createElement('option');
            option.value = String(index);
            const brand = first(label.brand_names) || first(label.generic_names) || `Label ${index + 1}`;
            const manufacturer = first(label.manufacturer) || 'Unknown manufacturer';
            option.textContent = `${brand} - ${manufacturer}`;
            labelSelect.append(option);
        });

        const selectLabel = (index) => renderLabel(data.labels[index]);
        labelSelect.onchange = () => selectLabel(Number(labelSelect.value));
        if (data.labels.length) selectLabel(0);
    }

    function renderLabel(label) {
        renderProvenance(label);
        const sections = buildSections(label);
        sectionNav.replaceChildren();
        detailSections.replaceChildren();

        sections.forEach((section) => {
            const id = `label-${section.key}`;
            const navLink = document.createElement('a');
            navLink.href = `#${id}`;
            navLink.textContent = section.title;
            sectionNav.append(navLink);

            const article = document.createElement('section');
            article.className = section.emphasis ? `document-section ${section.emphasis}` : 'document-section';
            article.id = id;

            const heading = document.createElement('h3');
            heading.textContent = section.title;
            article.append(heading);

            String(section.text).split(/\n\s*\n/).filter(Boolean).forEach((paragraphText) => {
                const paragraph = document.createElement('p');
                paragraph.textContent = paragraphText.trim();
                article.append(paragraph);
            });
            detailSections.append(article);
        });
    }

    function renderProvenance(label) {
        labelProvenance.replaceChildren();
        const items = [
            ['Manufacturer', first(label.manufacturer) || 'Not listed'],
            ['Route', first(label.route) || 'Not listed'],
            ['Effective date', formatFdaDate(label.effective_date) || 'Not listed'],
            ['Application', first(label.application_number) || 'Not listed'],
            ['Set ID', label.set_id || 'Not listed'],
        ];
        items.forEach(([term, value]) => {
            const wrapper = document.createElement('div');
            const dt = document.createElement('dt');
            const dd = document.createElement('dd');
            dt.textContent = term;
            dd.textContent = value;
            wrapper.append(dt, dd);
            labelProvenance.append(wrapper);
        });
    }

    function buildSections(label) {
        return [
            { key: 'active-ingredient', title: 'Active ingredient', text: label.active_ingredient },
            { key: 'indications', title: 'Indications and usage', text: label.indications_and_usage },
            { key: 'dosage', title: 'Dosage and administration', text: label.dosage_and_administration },
            { key: 'warnings', title: 'Warnings', text: label.warnings, emphasis: 'document-warning' },
            { key: 'contraindications', title: 'Contraindications', text: label.contraindications, emphasis: 'document-alert' },
            { key: 'adverse-reactions', title: 'Adverse reactions', text: label.adverse_reactions },
            { key: 'ask-doctor', title: 'Ask a doctor or pharmacist', text: label.ask_doctor },
            { key: 'stop-use', title: 'Stop use', text: label.stop_use },
            { key: 'pregnancy', title: 'Pregnancy and breastfeeding', text: label.pregnancy_or_breast_feeding },
            { key: 'description', title: 'Description', text: label.description },
        ].filter((section) => section.text);
    }

    const ixDrugList = document.getElementById('ixDrugList');
    const ixAddBtn = document.getElementById('ixAddBtn');
    const ixCheckBtn = document.getElementById('ixCheckBtn');
    const ixStatus = document.getElementById('ixStatus');
    const ixError = document.getElementById('ixError');
    const ixLoading = document.getElementById('ixLoading');
    const ixResults = document.getElementById('ixResults');
    const ixSummary = document.getElementById('ixSummary');
    const ixLimitation = document.getElementById('ixLimitation');
    const ixFlags = document.getElementById('ixFlags');

    let nextDrugRowId = 1;
    addDrugRow('metformin');
    addDrugRow('warfarin');

    ixAddBtn.addEventListener('click', () => addDrugRow(''));
    ixCheckBtn.addEventListener('click', performInteractionCheck);
    ixDrugList.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && event.target.matches('input')) performInteractionCheck();
    });

    function addDrugRow(value) {
        const currentRows = ixDrugList.querySelectorAll('.medication-row');
        if (currentRows.length >= 6) return;
        const rowNumber = nextDrugRowId++;
        const row = document.createElement('div');
        row.className = 'medication-row';

        const field = document.createElement('div');
        field.className = 'medication-field';
        const label = document.createElement('label');
        label.htmlFor = `ixDrug${rowNumber}`;
        label.textContent = `Medication ${currentRows.length + 1}`;
        const input = document.createElement('input');
        input.id = `ixDrug${rowNumber}`;
        input.className = 'ix-input';
        input.type = 'text';
        input.autocomplete = 'off';
        input.spellcheck = false;
        input.value = value;
        input.placeholder = 'Enter a brand or generic name';
        field.append(label, input);

        const remove = document.createElement('button');
        remove.className = 'remove-button';
        remove.type = 'button';
        remove.textContent = 'Remove';
        remove.setAttribute('aria-label', `Remove medication ${currentRows.length + 1}`);
        remove.addEventListener('click', () => {
            row.remove();
            refreshMedicationRows();
        });

        row.append(field, remove);
        ixDrugList.append(row);
        refreshMedicationRows();
        if (!value) input.focus();
    }

    function refreshMedicationRows() {
        const rows = Array.from(ixDrugList.querySelectorAll('.medication-row'));
        rows.forEach((row, index) => {
            row.querySelector('label').textContent = `Medication ${index + 1}`;
            const remove = row.querySelector('.remove-button');
            remove.classList.toggle('hidden', rows.length <= 2);
            remove.setAttribute('aria-label', `Remove medication ${index + 1}`);
        });
        ixAddBtn.disabled = rows.length >= 6;
    }

    async function performInteractionCheck() {
        const rawNames = Array.from(ixDrugList.querySelectorAll('.ix-input')).map((input) => input.value.trim()).filter(Boolean);
        const seen = new Set();
        const names = rawNames.filter((name) => {
            const key = name.toLocaleLowerCase();
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });

        if (names.length < 2) {
            ixError.textContent = 'Enter at least two unique medications to scan.';
            ixError.classList.remove('hidden');
            return;
        }

        ixError.classList.add('hidden');
        ixResults.classList.add('hidden');
        ixLoading.classList.remove('hidden');
        ixCheckBtn.disabled = true;
        ixStatus.textContent = 'Scanning retrieved FDA labels for interaction-related language.';

        try {
            const response = await fetch(`/api/interactions?drugs=${encodeURIComponent(names.join(','))}`);
            const data = await readJsonResponse(response);
            if (!response.ok) throw new Error(data.detail || 'Unable to scan interaction language.');
            renderInteractionResults(data);
            ixResults.classList.remove('hidden');
            ixStatus.textContent = data.summary;
            ixResults.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' });
        } catch (error) {
            ixError.textContent = error.message;
            ixError.classList.remove('hidden');
            ixStatus.textContent = 'Interaction scan failed.';
        } finally {
            ixLoading.classList.add('hidden');
            ixCheckBtn.disabled = false;
        }
    }

    function renderInteractionResults(data) {
        ixSummary.textContent = data.summary;
        ixLimitation.textContent = data.limitation;
        ixFlags.replaceChildren();

        if (!data.evidence.length) {
            const empty = document.createElement('div');
            empty.className = 'no-evidence';
            const label = document.createElement('strong');
            label.textContent = 'No text match detected';
            const copy = document.createElement('p');
            copy.textContent = 'DrugLens did not find one medication named in the interaction-related sections retrieved for the other medication.';
            empty.append(label, copy);
            ixFlags.append(empty);
            return;
        }

        data.evidence.forEach((evidence) => {
            const card = document.createElement('article');
            card.className = `evidence-card ${evidence.evidence_type === 'caution_language' ? 'evidence-caution' : ''}`;

            const header = document.createElement('div');
            header.className = 'evidence-header';
            const pair = document.createElement('h4');
            pair.textContent = `${titleCase(evidence.drug_a)} + ${titleCase(evidence.drug_b)}`;
            const badge = document.createElement('span');
            badge.className = 'evidence-kind';
            badge.textContent = evidence.evidence_type === 'caution_language' ? 'Caution language detected' : 'Mention detected';
            header.append(pair, badge);

            const quote = document.createElement('blockquote');
            quote.textContent = evidence.excerpt;

            const source = document.createElement('p');
            source.className = 'evidence-source';
            const sourceBits = [`Source: ${titleCase(evidence.source_drug)} FDA label`];
            if (evidence.source_manufacturer) sourceBits.push(evidence.source_manufacturer);
            sourceBits.push(`matched "${evidence.matched_term}"`);
            source.textContent = sourceBits.join(' · ');

            card.append(header, quote, source);
            ixFlags.append(card);
        });
    }

    async function readJsonResponse(response) {
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) return response.json();
        const text = await response.text();
        return { detail: text || 'Unexpected server response.' };
    }

    function first(value) {
        return Array.isArray(value) && value.length ? value[0] : '';
    }

    function titleCase(value) {
        return String(value || '').toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
    }

    function formatFdaDate(value) {
        if (!value || !/^\d{8}$/.test(String(value))) return value || '';
        const text = String(value);
        return `${text.slice(0, 4)}-${text.slice(4, 6)}-${text.slice(6, 8)}`;
    }

    function prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
});
