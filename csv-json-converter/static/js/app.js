/**
 * CSV -> JSON Converter  |  Frontend Application
 */
(function () {
    'use strict';

    /* ------------------------------------------------------------------
       State
    ------------------------------------------------------------------ */
    const state = {
        fileId: null,
        fileName: null,
        columns: [],
        previewData: null,
        jsonOutput: null,
        outputFilename: null,
        processing: false,
    };

    /* ------------------------------------------------------------------
       DOM References
    ------------------------------------------------------------------ */
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const els = {
        dropZone: $('#drop-zone'),
        fileInput: $('#file-input'),
        fileInfo: $('#file-info'),
        fileName: $('#file-name'),
        fileMeta: $('#file-meta'),
        removeFile: $('#remove-file'),

        previewSection: $('#preview-section'),
        previewBadge: $('#preview-badge'),
        previewStats: $('#preview-stats'),
        previewThead: $('#preview-thead'),
        previewTbody: $('#preview-tbody'),

        optionsSection: $('#options-section'),
        optOrientation: $('#opt-orientation'),
        optKeyColumn: $('#opt-key-column'),
        keyColumnGroup: $('#key-column-group'),
        optIndent: $('#opt-indent'),
        optNull: $('#opt-null'),
        customNullGroup: $('#custom-null-group'),
        optCustomNull: $('#opt-custom-null'),
        optDuplicates: $('#opt-duplicates'),
        optTypeDetect: $('#opt-type-detect'),
        optTrim: $('#opt-trim'),
        optNormalize: $('#opt-normalize'),
        columnToggles: $('#column-toggles'),

        btnConvert: $('#btn-convert'),
        btnClear: $('#btn-clear'),
        loadingSection: $('#loading-section'),

        outputSection: $('#output-section'),
        outputBadge: $('#output-badge'),
        jsonCode: $('#json-code'),
        btnCopy: $('#btn-copy'),
        btnDownload: $('#btn-download'),
        btnNew: $('#btn-new'),

        statsSection: $('#stats-section'),
        statsGrid: $('#stats-grid'),

        errorSection: $('#error-section'),
        errorMessage: $('#error-message'),

        toastContainer: $('#toast-container'),
    };

    /* ------------------------------------------------------------------
       Toast Notifications
    ------------------------------------------------------------------ */
    function showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = 'toast ' + (type || 'info');
        toast.textContent = message;
        toast.setAttribute('role', 'status');
        els.toastContainer.appendChild(toast);
        setTimeout(() => {
            if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 3200);
    }

    /* ------------------------------------------------------------------
       Step Indicators
    ------------------------------------------------------------------ */
    function setStep(num) {
        for (let i = 1; i <= 4; i++) {
            const el = $('#step-' + i);
            if (!el) continue;
            el.className = 'step-indicator';
            if (i < num) el.classList.add('done');
            if (i === num) el.classList.add('active');
        }
    }

    /* ------------------------------------------------------------------
       File Upload — Drag & Drop + Click
    ------------------------------------------------------------------ */
    function initUpload() {
        els.dropZone.addEventListener('click', () => els.fileInput.click());
        els.dropZone.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                els.fileInput.click();
            }
        });

        els.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) handleFile(e.target.files[0]);
        });

        els.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            els.dropZone.classList.add('drag-over');
        });
        els.dropZone.addEventListener('dragleave', () => {
            els.dropZone.classList.remove('drag-over');
        });
        els.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            els.dropZone.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length) handleFile(files[0]);
        });

        els.removeFile.addEventListener('click', resetAll);
    }

    function handleFile(file) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            showToast('Please upload a CSV file.', 'error');
            return;
        }

        // Show file info immediately
        els.fileName.textContent = file.name;
        els.fileMeta.textContent = formatSize(file.size);
        els.fileInfo.classList.remove('hidden');
        state.fileName = file.name;

        uploadFile(file);
    }

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/preview', {
                method: 'POST',
                body: formData,
            });
            const data = await res.json();

            if (!data.success) {
                showError(data.error.message);
                return;
            }

            state.fileId = data.data.file_id;
            state.previewData = data.data;
            state.columns = data.data.columns;

            renderPreview(data.data);
            renderOptions(data.data);
            showToast('CSV uploaded successfully.', 'success');
            setStep(2);

        } catch (err) {
            showError('Failed to upload file. Please try again.');
        }
    }

    /* ------------------------------------------------------------------
       Preview Rendering
    ------------------------------------------------------------------ */
    function renderPreview(data) {
        els.previewSection.classList.remove('hidden');
        els.optionsSection.classList.remove('hidden');
        els.outputSection.classList.add('hidden');
        els.statsSection.classList.add('hidden');
        els.errorSection.classList.add('hidden');

        // Badge
        els.previewBadge.textContent = data.total_rows.toLocaleString() + ' rows';

        // Stats
        const stats = [
            { value: data.total_rows.toLocaleString(), label: 'Rows' },
            { value: data.total_columns, label: 'Columns' },
            { value: data.delimiter_display, label: 'Delimiter' },
            { value: data.encoding, label: 'Encoding' },
        ];
        if (data.null_values > 0) stats.push({ value: data.null_values, label: 'Null Values' });
        if (data.duplicate_rows > 0) stats.push({ value: data.duplicate_rows, label: 'Duplicates' });

        els.previewStats.innerHTML = stats.map(s => `
            <div class="stat-chip">
                <div class="stat-value">${escapeHtml(String(s.value))}</div>
                <div class="stat-label">${escapeHtml(s.label)}</div>
            </div>
        `).join('');

        // Table header
        els.previewThead.innerHTML = '<tr>' +
            data.columns.map(c => `<th>${escapeHtml(c)}</th>`).join('') +
            '</tr>';

        // Table body
        els.previewTbody.innerHTML = data.preview_rows.map(row =>
            '<tr>' + data.columns.map(col => {
                const val = row[col];
                const display = val === null || val === undefined
                    ? '<span class="text-gray-600 italic">null</span>'
                    : escapeHtml(String(val));
                return `<td title="${escapeHtml(String(val ?? ''))}">${display}</td>`;
            }).join('') + '</tr>'
        ).join('');
    }

    /* ------------------------------------------------------------------
       Options Rendering
    ------------------------------------------------------------------ */
    function renderOptions(data) {
        // Populate key column dropdown
        els.optKeyColumn.innerHTML = '<option value="">Select column...</option>' +
            data.columns.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('');

        // Column toggles
        els.columnToggles.innerHTML = data.columns.map(c => `
            <span class="col-chip" data-col="${escapeHtml(c)}" tabindex="0" role="checkbox" aria-checked="true">
                ${escapeHtml(c)}
            </span>
        `).join('');

        // Bind column toggles
        els.columnToggles.querySelectorAll('.col-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                chip.classList.toggle('excluded');
                const checked = !chip.classList.contains('excluded');
                chip.setAttribute('aria-checked', String(checked));
            });
            chip.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    chip.click();
                }
            });
        });
    }

    /* ------------------------------------------------------------------
       Options Listeners
    ------------------------------------------------------------------ */
    function initOptions() {
        els.optOrientation.addEventListener('change', () => {
            const isObject = els.optOrientation.value === 'object';
            els.keyColumnGroup.classList.toggle('hidden', !isObject);
        });

        els.optNull.addEventListener('change', () => {
            els.customNullGroup.classList.toggle(
                'hidden', els.optNull.value !== 'custom'
            );
        });

        els.btnConvert.addEventListener('click', doConvert);
        els.btnClear.addEventListener('click', resetAll);
        els.btnCopy.addEventListener('click', copyJson);
        els.btnDownload.addEventListener('click', downloadJson);
        els.btnNew.addEventListener('click', resetAll);
    }

    /* ------------------------------------------------------------------
       Conversion
    ------------------------------------------------------------------ */
    function gatherOptions() {
        const excludedCols = [];
        els.columnToggles.querySelectorAll('.col-chip.excluded').forEach(chip => {
            excludedCols.push(chip.dataset.col);
        });

        return {
            file_id: state.fileId,
            orientation: els.optOrientation.value,
            key_column: els.optOrientation.value === 'object' ? els.optKeyColumn.value : null,
            indent: parseInt(els.optIndent.value, 10),
            minified: els.optIndent.value === '0',
            null_handling: els.optNull.value,
            null_custom_value: els.optNull.value === 'custom' ? els.optCustomNull.value : null,
            type_detection: els.optTypeDetect.checked,
            duplicate_handling: els.optDuplicates.value,
            empty_row_handling: 'remove_empty',
            trim_whitespace: els.optTrim.checked,
            normalize_columns: els.optNormalize.checked,
            exclude_columns: excludedCols.length ? excludedCols : null,
        };
    }

    async function doConvert() {
        if (state.processing || !state.fileId) return;

        // Validate object mode
        if (els.optOrientation.value === 'object' && !els.optKeyColumn.value) {
            showToast('Please select a key column for object orientation.', 'error');
            return;
        }

        state.processing = true;
        els.btnConvert.disabled = true;
        els.loadingSection.classList.remove('hidden');
        els.outputSection.classList.add('hidden');
        els.statsSection.classList.add('hidden');
        els.errorSection.classList.add('hidden');
        setStep(3);

        try {
            const res = await fetch('/api/convert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(gatherOptions()),
            });
            const data = await res.json();

            if (!data.success) {
                showError(data.error.message);
                return;
            }

            state.jsonOutput = data.data.json_string;
            state.outputFilename = data.data.output_filename;

            renderOutput(data.data);
            renderStats(data.data);
            showToast('Conversion completed successfully.', 'success');
            setStep(4);

        } catch (err) {
            showError('Failed to convert CSV. Please try again.');
        } finally {
            state.processing = false;
            els.btnConvert.disabled = false;
            els.loadingSection.classList.add('hidden');
        }
    }

    /* ------------------------------------------------------------------
       JSON Output Rendering
    ------------------------------------------------------------------ */
    function renderOutput(data) {
        els.outputSection.classList.remove('hidden');
        els.outputBadge.textContent = data.record_count.toLocaleString() + ' records';

        // Syntax-highlighted JSON
        els.jsonCode.innerHTML = highlightJson(data.json_string);

        // Scroll to output
        els.outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function highlightJson(jsonStr) {
        // Escape HTML first
        let html = escapeHtml(jsonStr);

        // Apply syntax highlighting with regex (order matters)
        // Strings (keys and values)
        html = html.replace(
            /(&quot;)(.*?)(&quot;)(\s*:)/g,
            '<span class="hl-string">$1$2$3</span>$4'
        );
        html = html.replace(
            /(:\s*)(&quot;)(.*?)(&quot;)/g,
            '$1<span class="hl-string">$2$3$4</span>'
        );

        // Numbers
        html = html.replace(
            /(?<![:\w])(-?\d+\.?\d*)(?![\w])/g,
            '<span class="hl-number">$1</span>'
        );

        // Booleans
        html = html.replace(
            /\b(true|false)\b/g,
            '<span class="hl-boolean">$1</span>'
        );

        // Null
        html = html.replace(
            /\bnull\b/g,
            '<span class="hl-null">$1</span>'
        );

        return html;
    }

    /* ------------------------------------------------------------------
       Statistics Rendering
    ------------------------------------------------------------------ */
    function renderStats(data) {
        els.statsSection.classList.remove('hidden');

        const stats = [
            { value: state.previewData.total_rows.toLocaleString(), label: 'Input Rows' },
            { value: data.record_count.toLocaleString(), label: 'JSON Records' },
            { value: data.output_size, label: 'Output Size' },
            { value: data.processing_time_ms + ' ms', label: 'Processing Time' },
        ];
        if (state.previewData.null_values > 0) {
            stats.push({ value: state.previewData.null_values, label: 'Null Values' });
        }
        if (state.previewData.duplicate_rows > 0) {
            stats.push({ value: state.previewData.duplicate_rows, label: 'Duplicate Rows' });
        }

        els.statsGrid.innerHTML = stats.map(s => `
            <div class="stat-chip">
                <div class="stat-value">${escapeHtml(String(s.value))}</div>
                <div class="stat-label">${escapeHtml(s.label)}</div>
            </div>
        `).join('');
    }

    /* ------------------------------------------------------------------
       Copy & Download
    ------------------------------------------------------------------ */
    async function copyJson() {
        if (!state.jsonOutput) return;

        try {
            await navigator.clipboard.writeText(state.jsonOutput);
            showToast('JSON copied to clipboard.', 'success');
        } catch {
            // Fallback
            const ta = document.createElement('textarea');
            ta.value = state.jsonOutput;
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            try {
                document.execCommand('copy');
                showToast('JSON copied to clipboard.', 'success');
            } catch {
                showToast('Failed to copy. Please select and copy manually.', 'error');
            }
            document.body.removeChild(ta);
        }
    }

    function downloadJson() {
        if (!state.outputFilename) return;
        const url = '/api/download/' + encodeURIComponent(state.outputFilename);
        window.location.href = url;
        showToast('Downloading JSON file.', 'info');
    }

    /* ------------------------------------------------------------------
       Error Handling
    ------------------------------------------------------------------ */
    function showError(message) {
        els.errorSection.classList.remove('hidden');
        els.errorMessage.textContent = message;
        els.loadingSection.classList.add('hidden');
        showToast(message, 'error');
    }

    /* ------------------------------------------------------------------
       Reset
    ------------------------------------------------------------------ */
    function resetAll() {
        state.fileId = null;
        state.fileName = null;
        state.columns = [];
        state.previewData = null;
        state.jsonOutput = null;
        state.outputFilename = null;
        state.processing = false;

        // Reset UI
        els.fileInfo.classList.add('hidden');
        els.fileInput.value = '';
        els.previewSection.classList.add('hidden');
        els.optionsSection.classList.add('hidden');
        els.outputSection.classList.add('hidden');
        els.statsSection.classList.add('hidden');
        els.loadingSection.classList.add('hidden');
        els.errorSection.classList.add('hidden');

        // Reset options
        els.optOrientation.value = 'records';
        els.optIndent.value = '2';
        els.optNull.value = 'keep';
        els.optDuplicates.value = 'keep';
        els.optTypeDetect.checked = true;
        els.optTrim.checked = false;
        els.optNormalize.checked = false;
        els.keyColumnGroup.classList.add('hidden');
        els.customNullGroup.classList.add('hidden');
        els.optCustomNull.value = '';
        els.btnConvert.disabled = false;

        setStep(1);
        window.scrollTo({ top: 0, behavior: 'smooth' });
        showToast('Cleared. Ready for a new conversion.', 'info');
    }

    /* ------------------------------------------------------------------
       Utilities
    ------------------------------------------------------------------ */
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    }

    /* ------------------------------------------------------------------
       Initialize
    ------------------------------------------------------------------ */
    document.addEventListener('DOMContentLoaded', () => {
        initUpload();
        initOptions();
    });

})();
