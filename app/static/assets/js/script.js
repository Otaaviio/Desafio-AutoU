document.addEventListener('DOMContentLoaded', () => {
    function switchTab(tab) {
        document.querySelectorAll('.tab-btn').forEach(t => {
            t.classList.remove('text-blue-600', 'border-blue-600');
            t.classList.add('text-slate-500', 'border-transparent');
        });
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        
        const activeTabBtn = document.querySelector(`[data-tab='${tab}']`);
        const activeTabContent = document.getElementById(`${tab}Tab`);

        if (activeTabBtn) {
            activeTabBtn.classList.add('text-blue-600', 'border-blue-600');
            activeTabBtn.classList.remove('text-slate-500', 'border-transparent');
        }
    
        if (activeTabContent) {
            activeTabContent.classList.remove('hidden');
        }
    }

    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', () => {
            switchTab(button.dataset.tab);
        });
    });

    const fileUpload = document.getElementById('fileUpload');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');

    if (fileUpload) {
        fileUpload.addEventListener('click', () => fileInput.click());

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUpload.addEventListener(eventName, e => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            fileUpload.addEventListener(eventName, () => fileUpload.classList.add('bg-blue-100', 'border-blue-600'));
        });

        ['dragleave', 'drop'].forEach(eventName => {
            fileUpload.addEventListener(eventName, () => fileUpload.classList.remove('bg-blue-100', 'border-blue-600'));
        });

        fileUpload.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                displayFileInfo(files[0]);
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                displayFileInfo(e.target.files[0]);
            }
        });
    }

    function displayFileInfo(file) {
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent = formatFileSize(file.size);
        fileInfo.classList.remove('hidden');
        fileInfo.classList.add('flex');
        switchTab('file');
    }

    function clearFile() {
        fileInput.value = '';
        fileInfo.classList.add('hidden');
        fileInfo.classList.remove('flex');
    }

    document.getElementById('clearFileBtn').addEventListener('click', clearFile);

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    document.getElementById('emailForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        const activeTabContent = document.querySelector('.tab-content:not(.hidden)');
        
        if (activeTabContent.id === 'textTab') {
            const text = document.getElementById('emailText').value.trim();
            if (!text) {
                showError('Por favor, insira o texto do email.');
                return;
            }
            formData.append('text', text);
        } else {
            const file = fileInput.files[0];
            if (!file) {
                showError('Por favor, selecione um arquivo.');
                return;
            }
            formData.append('file', file);
        }

        await analyzeEmail(formData);
    });

    async function analyzeEmail(formData) {
        const submitBtn = document.getElementById('submitBtn');
        const loader = document.getElementById('loader');
        const emptyState = document.getElementById('emptyState');
        const results = document.getElementById('results');
        const errorAlert = document.getElementById('errorAlert');

        errorAlert.classList.add('hidden');
        submitBtn.disabled = true;
        loader.classList.remove('hidden');
        if (emptyState) emptyState.style.display = 'none';
        if (results) results.classList.add('hidden');

        try {
            const response = await fetch('/classify', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Erro ao processar email');
            }

            displayResults(data);
        } catch (error) {
            showError(error.message);
            if (emptyState) emptyState.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            loader.classList.add('hidden');
        }
    }

    function displayResults(data) {
        const results = document.getElementById('results');
        const classification = document.getElementById('classification');
        const categoryText = document.getElementById('categoryText');
        const confidence = document.getElementById('confidence');
        const priority = document.getElementById('priority');
        const responseTime = document.getElementById('responseTime');
        const confidenceFill = document.getElementById('confidenceFill');
        const responseText = document.getElementById('responseText');
        const reasoning = document.getElementById('reasoning');

        if(results) {
            const isProdutivo = data.category.toLowerCase() === 'produtivo';
            classification.classList.remove('bg-green-100', 'text-green-800', 'bg-yellow-100', 'text-yellow-800');
            classification.classList.add(isProdutivo ? 'bg-green-100' : 'bg-yellow-100', isProdutivo ? 'text-green-800' : 'text-yellow-800');
            categoryText.textContent = data.category;

            const confidenceValue = Math.round(data.confidence * 100);
            confidence.textContent = confidenceValue + '%';
            if(confidenceFill) confidenceFill.style.width = confidenceValue + '%';
            
            priority.textContent = data.priority || (isProdutivo ? 'Alta' : 'Baixa');
            responseTime.textContent = data.response_time || (isProdutivo ? '< 24h' : '> 48h');

            responseText.textContent = data.suggested_response;
            reasoning.textContent = data.reasoning || 'Análise baseada no conteúdo e contexto do email.';

            results.classList.remove('hidden');
        }
    }

    function showError(message) {
        const errorAlert = document.getElementById('errorAlert');
        errorAlert.textContent = '❌ ' + message;
        errorAlert.classList.remove('hidden');
        setTimeout(() => errorAlert.classList.add('hidden'), 5000);
    }

    function copyResponse(event) {
        const responseText = document.getElementById('responseText').textContent;
        navigator.clipboard.writeText(responseText).then(() => {
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = '✓ Copiado!';
            btn.classList.add('bg-green-500');
            setTimeout(() => {
                btn.textContent = originalText;
                btn.classList.remove('bg-green-500');
            }, 2000);
        });
    }

    document.getElementById('copyResponseBtn').addEventListener('click', copyResponse);

    // Initialize the default tab
    switchTab('text');
});
