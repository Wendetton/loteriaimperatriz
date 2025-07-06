// Variáveis globais
let caixaAtual = 1;
let tipoMovimentacaoAtual = '';
let movimentacaoEditando = null;

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    inicializarApp();
});

function inicializarApp() {
    // Definir data atual
    const hoje = new Date().toISOString().split('T')[0];
    document.getElementById('dataAtual').textContent = formatarDataBR(hoje);
    
    // Definir datas nos campos
    const camposData = ['dataCaixa', 'dataCentral', 'dataInicioHistorico', 'dataFimHistorico'];
    camposData.forEach(campo => {
        const elemento = document.getElementById(campo);
        if (elemento) elemento.value = hoje;
    });
    
    // Carregar dashboard inicial
    mostrarPagina('dashboard');
    carregarDashboard();
    
    // Event listeners
    document.getElementById('dataCaixa')?.addEventListener('change', carregarDadosCaixa);
    document.getElementById('valorMaquina')?.addEventListener('input', calcularDiferenca);
}

// Navegação entre páginas
function mostrarPagina(pagina) {
    // Esconder todas as páginas
    document.querySelectorAll('.pagina').forEach(p => p.style.display = 'none');
    
    // Mostrar página selecionada
    document.getElementById(`pagina-${pagina}`).style.display = 'block';
    
    // Atualizar navbar
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    document.querySelector(`[href="#${pagina}"]`)?.classList.add('active');
    
    // Carregar dados específicos da página
    switch(pagina) {
        case 'dashboard':
            carregarDashboard();
            break;
        case 'central':
            carregarDadosCentral();
            break;
        case 'historico':
            carregarHistorico();
            break;
    }
}

function mostrarCaixa(numeroCaixa) {
    caixaAtual = numeroCaixa;
    document.getElementById('tituloCaixa').textContent = `Caixa ${numeroCaixa}`;
    mostrarPagina('caixa');
    carregarDadosCaixa();
}

// Funções de API
async function fazerRequisicao(url, opcoes = {}) {
    try {
        const resposta = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...opcoes.headers
            },
            ...opcoes
        });
        
        const dados = await resposta.json();
        
        if (!dados.success) {
            throw new Error(dados.error || 'Erro na requisição');
        }
        
        return dados.data;
    } catch (erro) {
        console.error('Erro na requisição:', erro);
        mostrarAlerta('Erro: ' + erro.message, 'danger');
        throw erro;
    }
}

// Dashboard
async function carregarDashboard() {
    try {
        const dados = await fazerRequisicao('/api/loteria/dashboard');
        
        // Atualizar cards de resumo
        document.getElementById('totalSuprimentos').textContent = formatarMoeda(dados.totais.suprimentos);
        document.getElementById('totalSangrias').textContent = formatarMoeda(dados.totais.sangrias);
        document.getElementById('saldoTotal').textContent = formatarMoeda(dados.totais.saldo_total);
        document.getElementById('caixasProblema').textContent = dados.totais.caixas_com_problema;
        
        // Atualizar grid de caixas
        const gridCaixas = document.getElementById('gridCaixas');
        gridCaixas.innerHTML = '';
        
        dados.caixas.forEach(caixa => {
            const cardCaixa = criarCardCaixa(caixa);
            gridCaixas.appendChild(cardCaixa);
        });
        
    } catch (erro) {
        console.error('Erro ao carregar dashboard:', erro);
    }
}

function criarCardCaixa(caixa) {
    const div = document.createElement('div');
    div.className = 'col-md-4 col-lg-2 mb-3';
    
    const statusClass = caixa.status === 'OK' ? 'status-ok' : 
                       caixa.status === 'VERIFICAR' ? 'status-verificar' : 'status-pendente';
    
    const statusBadge = caixa.status === 'OK' ? 'success' : 
                       caixa.status === 'VERIFICAR' ? 'danger' : 'warning';
    
    div.innerHTML = `
        <div class="card card-caixa-dashboard ${statusClass}" onclick="mostrarCaixa(${caixa.caixa})">
            <div class="card-body text-center">
                <h5 class="card-title">Caixa ${caixa.caixa}</h5>
                <p class="card-text">
                    <small class="text-muted">Saldo:</small><br>
                    <strong>${formatarMoeda(caixa.saldo_calculado)}</strong>
                </p>
                <span class="badge bg-${statusBadge}">${caixa.status}</span>
            </div>
        </div>
    `;
    
    return div;
}

// Caixa Individual
async function carregarDadosCaixa() {
    try {
        const data = document.getElementById('dataCaixa').value;
        const dados = await fazerRequisicao(`/api/loteria/caixa/${caixaAtual}?data=${data}`);
        
        // Atualizar saldo inicial
        document.getElementById('saldoInicial').value = dados.saldo_inicial.toFixed(2);
        
        // Carregar movimentações
        carregarMovimentacoes(dados.suprimentos, 'suprimento');
        carregarMovimentacoes(dados.sangrias, 'sangria');
        
        // Carregar fechamento
        if (dados.fechamento) {
            document.getElementById('valorMaquina').value = dados.fechamento.valor_maquina.toFixed(2);
            document.getElementById('observacoes').value = dados.fechamento.observacoes || '';
        } else {
            document.getElementById('valorMaquina').value = '';
            document.getElementById('observacoes').value = '';
        }
        
        // Calcular totais e diferença
        calcularTotais();
        calcularDiferenca();
        
    } catch (erro) {
        console.error('Erro ao carregar dados do caixa:', erro);
    }
}

function carregarMovimentacoes(movimentacoes, tipo) {
    const lista = document.getElementById(tipo === 'suprimento' ? 'listaSuprimentos' : 'listaSangrias');
    lista.innerHTML = '';
    
    movimentacoes.forEach(mov => {
        const item = criarItemMovimentacao(mov, tipo);
        lista.appendChild(item);
    });
    
    calcularTotais();
}

function criarItemMovimentacao(movimentacao, tipo) {
    const div = document.createElement('div');
    div.className = `movimentacao-item movimentacao-${tipo}`;
    div.dataset.id = movimentacao.id;
    
    div.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div class="flex-grow-1">
                <strong>${movimentacao.descricao}</strong><br>
                <span class="text-muted">${formatarMoeda(movimentacao.valor)}</span>
            </div>
            <div>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editarMovimentacao(${movimentacao.id}, '${tipo}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="removerMovimentacao(${movimentacao.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
    
    return div;
}

function calcularTotais() {
    // Calcular total de suprimentos
    const suprimentos = document.querySelectorAll('#listaSuprimentos .movimentacao-item');
    let totalSuprimentos = 0;
    suprimentos.forEach(item => {
        const textoValor = item.querySelector('.text-muted').textContent;
        const valor = parseFloat(textoValor.replace('R$ ', '').replace('.', '').replace(',', '.'));
        totalSuprimentos += valor || 0;
    });
    
    // Calcular total de sangrias
    const sangrias = document.querySelectorAll('#listaSangrias .movimentacao-item');
    let totalSangrias = 0;
    sangrias.forEach(item => {
        const textoValor = item.querySelector('.text-muted').textContent;
        const valor = parseFloat(textoValor.replace('R$ ', '').replace('.', '').replace(',', '.'));
        totalSangrias += valor || 0;
    });
    
    // Atualizar displays
    document.getElementById('totalSuprimentosCaixa').textContent = totalSuprimentos.toFixed(2).replace('.', ',');
    document.getElementById('totalSangriasCaixa').textContent = totalSangrias.toFixed(2).replace('.', ',');
    
    // Calcular saldo calculado
    const saldoInicial = parseFloat(document.getElementById('saldoInicial').value) || 0;
    const saldoCalculado = saldoInicial + totalSuprimentos - totalSangrias;
    document.getElementById('saldoCalculado').value = saldoCalculado.toFixed(2);
}

function calcularDiferenca() {
    const valorMaquina = parseFloat(document.getElementById('valorMaquina').value) || 0;
    const saldoCalculado = parseFloat(document.getElementById('saldoCalculado').value) || 0;
    const diferenca = valorMaquina - saldoCalculado;
    
    document.getElementById('diferenca').value = diferenca.toFixed(2);
    
    // Atualizar status
    const statusElement = document.getElementById('statusCaixa');
    if (Math.abs(diferenca) <= 10) {
        statusElement.innerHTML = '<span class="badge bg-success">OK</span>';
    } else {
        statusElement.innerHTML = '<span class="badge bg-danger">VERIFICAR</span>';
    }
}

// Movimentações
function adicionarMovimentacao(tipo) {
    tipoMovimentacaoAtual = tipo;
    movimentacaoEditando = null;
    
    document.getElementById('tituloModalMovimentacao').textContent = 
        `Adicionar ${tipo === 'suprimento' ? 'Suprimento' : 'Sangria'}`;
    document.getElementById('descricaoMovimentacao').value = '';
    document.getElementById('valorMovimentacao').value = '';
    
    new bootstrap.Modal(document.getElementById('modalMovimentacao')).show();
}

function editarMovimentacao(id, tipo) {
    // Implementar edição de movimentação
    console.log('Editar movimentação:', id, tipo);
}

async function removerMovimentacao(id) {
    if (!confirm('Tem certeza que deseja remover esta movimentação?')) return;
    
    try {
        await fazerRequisicao(`/api/loteria/caixa/${caixaAtual}/movimentacao/${id}`, {
            method: 'DELETE'
        });
        
        carregarDadosCaixa();
        mostrarAlerta('Movimentação removida com sucesso!', 'success');
    } catch (erro) {
        console.error('Erro ao remover movimentação:', erro);
    }
}

async function salvarMovimentacao() {
    const descricao = document.getElementById('descricaoMovimentacao').value;
    const valor = parseFloat(document.getElementById('valorMovimentacao').value);
    const data = document.getElementById('dataCaixa').value;
    
    if (!descricao || !valor) {
        mostrarAlerta('Preencha todos os campos!', 'warning');
        return;
    }
    
    try {
        await fazerRequisicao(`/api/loteria/caixa/${caixaAtual}/movimentacao`, {
            method: 'POST',
            body: JSON.stringify({
                tipo: tipoMovimentacaoAtual,
                descricao: descricao,
                valor: valor,
                data: data
            })
        });
        
        bootstrap.Modal.getInstance(document.getElementById('modalMovimentacao')).hide();
        carregarDadosCaixa();
        mostrarAlerta('Movimentação adicionada com sucesso!', 'success');
    } catch (erro) {
        console.error('Erro ao salvar movimentação:', erro);
    }
}

// Fechamento
async function salvarFechamento() {
    const data = document.getElementById('dataCaixa').value;
    const saldoInicial = parseFloat(document.getElementById('saldoInicial').value) || 0;
    const valorMaquina = parseFloat(document.getElementById('valorMaquina').value) || 0;
    const observacoes = document.getElementById('observacoes').value;
    
    if (!valorMaquina) {
        mostrarAlerta('Informe o valor da máquina!', 'warning');
        return;
    }
    
    try {
        await fazerRequisicao(`/api/loteria/caixa/${caixaAtual}/fechamento`, {
            method: 'POST',
            body: JSON.stringify({
                data: data,
                saldo_inicial: saldoInicial,
                valor_maquina: valorMaquina,
                observacoes: observacoes
            })
        });
        
        mostrarAlerta('Fechamento salvo com sucesso!', 'success');
    } catch (erro) {
        console.error('Erro ao salvar fechamento:', erro);
    }
}

function limparFormulario() {
    if (confirm('Tem certeza que deseja limpar todos os dados?')) {
        document.getElementById('valorMaquina').value = '';
        document.getElementById('observacoes').value = '';
        document.getElementById('listaSuprimentos').innerHTML = '';
        document.getElementById('listaSangrias').innerHTML = '';
        calcularTotais();
        calcularDiferenca();
    }
}

// Caixa Central
async function carregarDadosCentral() {
    try {
        const data = document.getElementById('dataCentral').value;
        const dados = await fazerRequisicao(`/api/loteria/central?data=${data}`);
        
        // Atualizar consolidação
        document.getElementById('totalSuprimentosCentral').textContent = formatarMoeda(dados.consolidacao.total_suprimentos);
        document.getElementById('totalSangriasCentral').textContent = formatarMoeda(dados.consolidacao.total_sangrias);
        document.getElementById('saldoTotalCentral').textContent = formatarMoeda(dados.consolidacao.saldo_total);
        document.getElementById('caixasProblemaCentral').textContent = dados.consolidacao.caixas_com_problema;
        
        // Atualizar tabela
        const tabela = document.getElementById('tabelaCentral');
        tabela.innerHTML = '';
        
        dados.caixas.forEach(caixa => {
            const linha = criarLinhaTabelaCentral(caixa);
            tabela.appendChild(linha);
        });
        
    } catch (erro) {
        console.error('Erro ao carregar dados centrais:', erro);
    }
}

function criarLinhaTabelaCentral(caixa) {
    const tr = document.createElement('tr');
    
    const statusClass = caixa.status === 'OK' ? 'success' : 
                       caixa.status === 'VERIFICAR' ? 'danger' : 'warning';
    
    tr.innerHTML = `
        <td><strong>Caixa ${caixa.caixa}</strong></td>
        <td>${formatarMoeda(caixa.saldo_inicial)}</td>
        <td class="valor-positivo">${formatarMoeda(caixa.total_suprimentos)}</td>
        <td class="valor-negativo">${formatarMoeda(caixa.total_sangrias)}</td>
        <td>${formatarMoeda(caixa.saldo_calculado)}</td>
        <td>${formatarMoeda(caixa.valor_maquina)}</td>
        <td class="${caixa.diferenca === 0 ? 'valor-neutro' : caixa.diferenca > 0 ? 'valor-positivo' : 'valor-negativo'}">
            ${formatarMoeda(caixa.diferenca)}
        </td>
        <td>
            <span class="badge bg-${statusClass}">${caixa.status}</span>
        </td>
        <td>
            <button class="btn btn-sm btn-outline-primary" onclick="mostrarCaixa(${caixa.caixa})">
                <i class="fas fa-eye"></i>
            </button>
        </td>
    `;
    
    return tr;
}

// Histórico
async function carregarHistorico() {
    try {
        const dataInicio = document.getElementById('dataInicioHistorico').value;
        const dataFim = document.getElementById('dataFimHistorico').value;
        const caixa = document.getElementById('caixaHistorico').value;
        
        let url = '/api/loteria/historico?';
        if (dataInicio) url += `data_inicio=${dataInicio}&`;
        if (dataFim) url += `data_fim=${dataFim}&`;
        if (caixa) url += `caixa=${caixa}&`;
        
        const dados = await fazerRequisicao(url);
        
        const tabela = document.getElementById('tabelaHistorico');
        tabela.innerHTML = '';
        
        dados.forEach(fechamento => {
            const linha = criarLinhaHistorico(fechamento);
            tabela.appendChild(linha);
        });
        
    } catch (erro) {
        console.error('Erro ao carregar histórico:', erro);
    }
}

function criarLinhaHistorico(fechamento) {
    const tr = document.createElement('tr');
    
    const status = Math.abs(fechamento.diferenca) <= 10 ? 'OK' : 'VERIFICAR';
    const statusClass = status === 'OK' ? 'success' : 'danger';
    
    tr.innerHTML = `
        <td>${formatarDataBR(fechamento.data)}</td>
        <td>Caixa ${fechamento.caixa}</td>
        <td>${formatarMoeda(fechamento.saldo_inicial)}</td>
        <td class="valor-positivo">${formatarMoeda(fechamento.total_suprimentos)}</td>
        <td class="valor-negativo">${formatarMoeda(fechamento.total_sangrias)}</td>
        <td>${formatarMoeda(fechamento.valor_maquina)}</td>
        <td class="${fechamento.diferenca === 0 ? 'valor-neutro' : fechamento.diferenca > 0 ? 'valor-positivo' : 'valor-negativo'}">
            ${formatarMoeda(fechamento.diferenca)}
        </td>
        <td>
            <span class="badge bg-${statusClass}">${status}</span>
        </td>
    `;
    
    return tr;
}

// Utilitários
function alterarData(dias) {
    const campoData = document.getElementById('dataCaixa');
    const dataAtual = new Date(campoData.value);
    dataAtual.setDate(dataAtual.getDate() + dias);
    campoData.value = dataAtual.toISOString().split('T')[0];
    carregarDadosCaixa();
}

function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

function formatarDataBR(data) {
    return new Date(data + 'T00:00:00').toLocaleDateString('pt-BR');
}

function mostrarAlerta(mensagem, tipo) {
    // Criar elemento de alerta
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo} alert-dismissible fade show position-fixed`;
    alerta.style.cssText = 'top: 100px; right: 20px; z-index: 9999; min-width: 300px;';
    alerta.innerHTML = `
        ${mensagem}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alerta);
    
    // Remover automaticamente após 5 segundos
    setTimeout(() => {
        if (alerta.parentNode) {
            alerta.remove();
        }
    }, 5000);
}

function exportarHistorico() {
    // Implementar exportação de histórico
    mostrarAlerta('Funcionalidade de exportação em desenvolvimento', 'info');
}

