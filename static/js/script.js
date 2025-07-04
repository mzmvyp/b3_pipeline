// static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM totalmente carregado e analisado.");

    // --- Elementos da Página de Raspagem (index.html) ---
    const scrapeButton = document.getElementById('scrapeButton');
    const scrapeSpinner = document.getElementById('scrapeSpinner');
    const scrapeMessage = document.getElementById('scrapeMessage');

    // --- Elementos do Navegador S3 (s3_navigator.html) ---
    const s3BucketSelect = document.getElementById('bucketSelect');
    const goUpButton = document.getElementById('goUpButton');
    const s3ContentTableBody = document.getElementById('s3ContentTableBody');
    const currentPathSpan = document.getElementById('currentPath');

    // Variáveis de estado do navegador S3
    let currentS3Bucket = '';
    let currentS3Prefix = '';

    // --- Funções Auxiliares Gerais (reaproveitadas) ---
    function showSpinner(spinnerElement) {
        if (spinnerElement) spinnerElement.style.display = 'inline-block';
    }

    function hideSpinner(spinnerElement) {
        if (spinnerElement) spinnerElement.style.display = 'none';
    }

    function showMessage(element, text, type) {
        if (element) {
            element.textContent = text;
            element.className = 'message ' + type;
            element.style.display = 'block';
        }
    }

    function hideMessage(element) {
        if (element) {
            element.textContent = '';
            element.className = 'message';
            element.style.display = 'none';
        }
    }

    // --- Lógica da Página Inicial (Scraping) ---
    if (scrapeButton) { 
        scrapeButton.addEventListener('click', async function() {
            showSpinner(scrapeSpinner);
            scrapeButton.disabled = true;
            hideMessage(scrapeMessage);
            showMessage(scrapeMessage, 'Iniciando raspagem e upload... Isso pode levar alguns minutos.', 'info');

            try {
                const response = await fetch('/api/scrape_and_upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();

                if (response.ok) {
                    showMessage(scrapeMessage, data.message, 'success');
                } else {
                    showMessage(scrapeMessage, data.error || 'Erro desconhecido ao processar requisição.', 'error');
                }
            } catch (error) {
                console.error('Erro ao chamar a API de scraping:', error);
                showMessage(scrapeMessage, 'Erro ao conectar com o servidor: ' + error.message, 'error');
            } finally {
                hideSpinner(scrapeSpinner);
                scrapeButton.disabled = false;
            }
        });
    }

    // --- Lógica do Navegador S3 (s3_navigator.html) ---
    // Ativa a lógica S3 SOMENTE se os elementos existirem na página atual
    if (s3BucketSelect && s3ContentTableBody) { 
        // Função para popular o select de buckets
        async function populateBucketSelect() {
            s3BucketSelect.innerHTML = '<option value="">Carregando buckets...</option>';
            s3BucketSelect.disabled = true;

            try {
                const response = await fetch('/api/list_buckets');
                const data = await response.json();

                s3BucketSelect.innerHTML = '<option value="">-- Selecione um Bucket --</option>'; 
                if (response.ok && data.buckets && data.buckets.length > 0) {
                    data.buckets.forEach(bucket => {
                        const option = document.createElement('option');
                        option.value = bucket;
                        option.textContent = bucket;
                        s3BucketSelect.appendChild(option);
                    });
                } else {
                    s3BucketSelect.innerHTML = '<option value="">Nenhum bucket encontrado ou erro.</option>';
                    console.error('Erro ao listar buckets:', data.error || 'Erro desconhecido.');
                }
            } catch (error) {
                s3BucketSelect.innerHTML = '<option value="">Erro ao carregar buckets.</option>';
                console.error('Erro de conexão ao listar buckets:', error);
            } finally {
                s3BucketSelect.disabled = false;
                // Tenta pré-selecionar o bucket de scraping se ele estiver na lista
                // ou o primeiro bucket disponível
                const defaultScrapingBucket = '{{ SCRAPING_TARGET_S3_BUCKET }}'; // Acessa a variável injetada pelo Flask
                if (defaultScrapingBucket && Array.from(s3BucketSelect.options).some(opt => opt.value === defaultScrapingBucket)) {
                    s3BucketSelect.value = defaultScrapingBucket;
                    fetchS3Content(defaultScrapingBucket, '');
                } else if (s3BucketSelect.options.length > 1) { 
                    s3BucketSelect.value = s3BucketSelect.options[1].value; 
                    fetchS3Content(s3BucketSelect.value, '');
                } else {
                    // No buckets available, display default message
                    s3ContentTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">Nenhum bucket disponível.</td></tr>';
                }
            }
        }

        // Função principal para buscar e renderizar conteúdo S3
        async function fetchS3Content(bucket, prefix) {
            currentS3Bucket = bucket;
            currentS3Prefix = prefix;

            // Atualiza a exibição do caminho (breadcrumb)
            if (currentS3Bucket) {
                currentPathSpan.innerHTML = `<a href="#" data-path="">${currentS3Bucket}</a> / `;
                const pathParts = prefix.split('/').filter(Boolean); // Filtra vazios
                let accumulatedPath = '';
                pathParts.forEach((part, index) => {
                    accumulatedPath += part + '/';
                    const pathLink = document.createElement('a');
                    pathLink.href = '#';
                    pathLink.textContent = part;
                    pathLink.dataset.path = accumulatedPath; // Armazena o caminho completo
                    currentPathSpan.appendChild(pathLink);
                    if (index < pathParts.length - 1) {
                        currentPathSpan.appendChild(document.createTextNode(' / '));
                    }
                });
                goUpButton.disabled = !currentS3Prefix; // Habilita "Voltar" se não estiver na raiz do bucket
            } else {
                currentPathSpan.textContent = 'Nenhum bucket selecionado';
                goUpButton.disabled = true;
            }

            s3ContentTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">Carregando...</td></tr>';
            s3BucketSelect.disabled = true;
            goUpButton.disabled = true;

            try {
                const response = await fetch('/api/list_s3_path', { // Endpoint `/api/list_s3_path`
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ bucket_name: currentS3Bucket, prefix: currentS3Prefix })
                });
                const data = await response.json();

                if (response.ok && data.contents) {
                    renderS3ContentTable(data.contents);
                } else {
                    console.error('Erro ao listar S3:', data.error || 'Erro desconhecido.');
                    s3ContentTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: red;">Erro ao carregar S3: ${data.error || 'Erro desconhecido.'}</td></tr>`;
                }
            } catch (error) {
                console.error('Erro de conexão ao listar S3:', error);
                s3ContentTableBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: red;">Erro de conexão: ${error.message}</td></tr>`;
            } finally {
                s3BucketSelect.disabled = false;
                if (currentS3Bucket) { 
                    goUpButton.disabled = !currentS3Prefix;
                }
                // Re-attach event listeners for the path links after rendering
                currentPathSpan.querySelectorAll('a').forEach(link => {
                    link.addEventListener('click', (e) => {
                        e.preventDefault();
                        const targetPath = e.target.dataset.path || ''; // Get target path, empty string for root
                        fetchS3Content(currentS3Bucket, targetPath);
                    });
                });
            }
        }

        // Função para renderizar o conteúdo na tabela S3
        function renderS3ContentTable(content) {
            s3ContentTableBody.innerHTML = '';
            if (content && content.length > 0) {
                content.forEach(item => {
                    const row = s3ContentTableBody.insertRow();
                    row.insertCell(0).textContent = item.type === 'prefix' ? 'Pasta' : 'Arquivo';

                    const nameCell = row.insertCell(1);
                    const nameSpan = document.createElement('span');
                    nameSpan.textContent = item.name;
                    nameSpan.classList.add('item-name');
                    if (item.type === 'prefix') {
                        nameSpan.classList.add('is-prefix');
                    }
                    nameCell.appendChild(nameSpan);

                    row.insertCell(2).textContent = item.size !== null ? (item.size / 1024 / 1024).toFixed(2) + ' MB' : '';
                    row.insertCell(3).textContent = item.last_modified ? new Date(item.last_modified).toLocaleString() : '';
                });

                s3ContentTableBody.querySelectorAll('.item-name.is-prefix').forEach(prefixSpan => {
                    prefixSpan.addEventListener('click', function() {
                        const clickedFolderName = this.textContent;
                        let newPrefix = currentS3Prefix;
                        if (newPrefix && !newPrefix.endsWith('/')) { // Ensure current prefix ends with slash if not root
                            newPrefix += '/'; 
                        }
                        newPrefix += clickedFolderName + '/'; // Append clicked folder name with a slash
                        fetchS3Content(currentS3Bucket, newPrefix);
                    });
                });

            } else {
                const row = s3ContentTableBody.insertRow();
                const cell = row.insertCell(0);
                cell.colSpan = 4;
                cell.textContent = 'Nenhum conteúdo encontrado nesta pasta.';
                cell.style.textAlign = 'center';
            }
        }

        // --- Event Listeners para o Navegador S3 ---
        s3BucketSelect.addEventListener('change', function() {
            const selectedBucket = this.value;
            if (selectedBucket) {
                fetchS3Content(selectedBucket, ''); // Inicia na raiz do bucket selecionado
            } else {
                currentS3Bucket = '';
                currentS3Prefix = '';
                currentPathSpan.textContent = 'Nenhum bucket selecionado';
                goUpButton.disabled = true;
                s3ContentTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">Selecione um bucket para começar.</td></tr>';
            }
        });

        // Event listener para o botão "Voltar"
        goUpButton.addEventListener('click', function() {
            if (!currentS3Prefix) {
                // Já estamos na raiz do bucket, a ação "Voltar" deve ir para a seleção de buckets
                currentS3Bucket = '';
                currentS3Prefix = '';
                s3BucketSelect.value = ''; // Reseta o select de buckets
                currentPathSpan.textContent = 'Nenhum bucket selecionado';
                goUpButton.disabled = true;
                s3ContentTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">Selecione um bucket para começar.</td></tr>';
                return;
            }

            // Remove o último segmento do prefixo para subir um nível
            let pathSegments = currentS3Prefix.split('/').filter(Boolean); // Filtra strings vazias
            pathSegments.pop(); // Remove o último segmento (pasta atual)
            // Recria o prefixo, garantindo que termine com '/' se não for vazio
            const parentPrefix = pathSegments.length > 0 ? pathSegments.join('/') + '/' : '';
            
            fetchS3Content(currentS3Bucket, parentPrefix);
        });

        // Carrega a lista de buckets ao carregar a página
        populateBucketSelect();
    }
});