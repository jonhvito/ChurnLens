/**
 * dashboard.js
 * Script principal para renderizar gráficos e tabelas do Dashboard ChurnLens.
 */

// ==========================================
// Constantes e Globais
// ==========================================

// Cores para segmentos de risco
const RISK_COLORS = {
    'Risco baixo': '#22c55e',          // Green-500
    'Risco médio': '#eab308',          // Yellow-500
    'Risco alto': '#f97316',           // Orange-500
    'Risco alto (prioritário)': '#ea580c', // Orange-600
    'Churn': '#ef4444',                // Red-500
    'Churn (prioritário)': '#dc2626',  // Red-600
    'Risco muito alto': '#7f1d1d'      // Red-900
};

const RISK_ORDER = [
    'Risco baixo',
    'Risco médio',
    'Risco alto',
    'Risco alto (prioritário)',
    'Churn',
    'Churn (prioritário)',
    'Risco muito alto'
];

// Variável global para armazenar a instância do gráfico expandido
let expandedChartInstance = null;
// Objeto global para armazenar as instâncias dos gráficos do dashboard
window.dashboardCharts = {};

// ==========================================
// Inicialização
// ==========================================

document.addEventListener('DOMContentLoaded', async function () {
    // 1. Renderizar Gráfico de Churn por RFM
    renderRFMChart();

    // 2. Renderizar Histograma de Recência
    renderRecencyChart();

    // 3. Renderizar Análise de Risco (Novos Gráficos)
    renderRiskAnalysis();

    // 4. Carregar Tabela de Top 50 Clientes em Risco
    loadTopRiskTable();

    // Event listener para fechar modal com ESC
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            closeChartModal();
            // Também fecha o modal de ajuda se existir
            const helpModal = document.getElementById('helpModal');
            if (helpModal && !helpModal.classList.contains('hidden')) {
                toggleHelpModal();
            }
        }
    });

    // Event listener para mudança de tema
    window.addEventListener('themeChanged', () => {
        const isDark = document.documentElement.classList.contains('dark');
        const textColor = isDark ? '#9ca3af' : '#111827';
        const legendColor = isDark ? '#e5e7eb' : '#111827';
        const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
        const borderColor = isDark ? '#1f2937' : '#ffffff';

        const updateChart = (chart) => {
            if (!chart) return;

            // Atualizar Scales (Eixos)
            if (chart.options.scales) {
                Object.keys(chart.options.scales).forEach(scaleKey => {
                    const scale = chart.options.scales[scaleKey];
                    if (scale.ticks) {
                        scale.ticks.color = textColor;
                    }
                    if (scale.grid) {
                        scale.grid.color = gridColor;
                    }
                    if (scale.title) {
                        // Se houver título no eixo, atualizar também (geralmente não tem cor definida explícita, herda ou é configurada)
                        // Se quisermos forçar: scale.title.color = textColor; 
                    }
                });
            }

            // Atualizar Legendas
            if (chart.options.plugins && chart.options.plugins.legend && chart.options.plugins.legend.labels) {
                chart.options.plugins.legend.labels.color = legendColor;
            }

            // Especial: Doughnut border
            if (chart.config.type === 'doughnut') {
                chart.data.datasets.forEach(dataset => {
                    dataset.borderColor = borderColor;
                });
            }

            chart.update();
        };

        // Atualizar todos os gráficos do dashboard
        Object.values(window.dashboardCharts).forEach(updateChart);

        // Atualizar gráfico expandido, se houver
        if (expandedChartInstance) {
            updateChart(expandedChartInstance);
        }
    });
});

// ==========================================
// Funções de Renderização (Dashboard Principal)
// ==========================================

async function renderRiskAnalysis() {
    try {
        const response = await fetch('/api/risk_summary');
        if (!response.ok) throw new Error('Falha ao buscar dados de risco');

        let data = await response.json();

        // Ordenar dados pela severidade
        data.sort((a, b) => {
            const idxA = RISK_ORDER.indexOf(a.risk_segment);
            const idxB = RISK_ORDER.indexOf(b.risk_segment);
            return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
        });

        renderRiskCards(data);
        renderRiskDistributionChart(data);
        renderRiskChurnRateChart(data);
        renderRiskMonetaryChart(data);
        renderRiskFunnelChart(data);

    } catch (error) {
        console.error("Erro ao carregar Análise de Risco:", error);
    }
}

function renderRiskCards(data) {
    const container = document.getElementById('riskSummaryCards');
    if (!container) return;

    container.innerHTML = '';
    const totalCount = data.reduce((acc, curr) => acc + curr.count, 0);

    data.forEach(item => {
        const color = RISK_COLORS[item.risk_segment] || '#6b7280';
        const percent = ((item.count / totalCount) * 100).toFixed(1);

        const card = document.createElement('div');
        card.className = "bg-white dark:bg-gray-800 rounded-lg shadow p-4 border-l-4 hover:shadow-md transition-shadow dark:text-gray-200";
        card.style.borderLeftColor = color;

        card.innerHTML = `
            <div class="flex justify-between items-start mb-2">
                <h4 class="font-bold text-gray-700 dark:text-gray-200 text-sm" title="${item.risk_segment}">${item.risk_segment}</h4>
                <span class="text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                    ${percent}%
                </span>
            </div>
            <div class="space-y-1">
                <div class="flex justify-between text-sm">
                    <span class="text-gray-500 dark:text-gray-400">Clientes:</span>
                    <span class="font-bold">${item.count}</span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-500 dark:text-gray-400">Churn Rate:</span>
                    <span class="font-medium ${item.churn_rate > 50 ? 'text-red-500' : 'text-green-500'}">
                        ${item.churn_rate.toFixed(1)}%
                    </span>
                </div>
                <div class="flex justify-between text-sm">
                    <span class="text-gray-500 dark:text-gray-400">Em Risco:</span>
                    <span class="font-medium">
                        R$ ${(item.monetary_sum / 1000).toFixed(1)}k
                    </span>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}



function renderRiskDistributionChart(data) {
    const ctx = document.getElementById('riskDistributionChart');
    if (!ctx) return;

    if (window.dashboardCharts.riskDistribution) {
        window.dashboardCharts.riskDistribution.destroy();
    }

    window.dashboardCharts.riskDistribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.risk_segment),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: data.map(d => RISK_COLORS[d.risk_segment] || '#6b7280'),
                borderWidth: 2,
                borderColor: document.documentElement.classList.contains('dark') ? '#1f2937' : '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        font: { size: 10 },
                        color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#111827'
                    }
                }
            }
        }
    });
}

function renderRiskChurnRateChart(data) {
    const ctx = document.getElementById('riskChurnRateChart');
    if (!ctx) return;

    if (window.dashboardCharts.riskChurnRate) {
        window.dashboardCharts.riskChurnRate.destroy();
    }

    window.dashboardCharts.riskChurnRate = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.risk_segment),
            datasets: [{
                label: 'Churn Rate (%)',
                data: data.map(d => d.churn_rate),
                backgroundColor: data.map(d => RISK_COLORS[d.risk_segment] || '#6b7280'),
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: v => v + '%',
                        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827'
                    },
                    grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
                },
                x: {
                    ticks: { display: false },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderRiskMonetaryChart(data) {
    const ctx = document.getElementById('riskMonetaryChart');
    if (!ctx) return;

    if (window.dashboardCharts.riskMonetary) {
        window.dashboardCharts.riskMonetary.destroy();
    }

    window.dashboardCharts.riskMonetary = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.risk_segment),
            datasets: [{
                label: 'Valor Monetário',
                data: data.map(d => d.monetary_sum),
                backgroundColor: data.map(d => RISK_COLORS[d.risk_segment] || '#6b7280'),
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: v => 'R$ ' + (v / 1000).toFixed(0) + 'k',
                        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827'
                    },
                    grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
                },
                x: {
                    ticks: { display: false },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderRiskFunnelChart(data) {
    const ctx = document.getElementById('riskFunnelChart');
    if (!ctx) return;

    if (window.dashboardCharts.riskFunnel) {
        window.dashboardCharts.riskFunnel.destroy();
    }

    window.dashboardCharts.riskFunnel = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.risk_segment),
            datasets: [{
                label: 'Clientes',
                data: data.map(d => d.count),
                backgroundColor: data.map(d => RISK_COLORS[d.risk_segment] || '#6b7280'),
                borderRadius: 4,
                barPercentage: 0.6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827' },
                    grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
                },
                y: {
                    ticks: {
                        color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827',
                        font: { size: 11 }
                    },
                    grid: { display: false }
                }
            }
        }
    });
}



async function renderRFMChart() {
    const canvas = document.getElementById('churnRfmChart');
    if (!canvas) return;

    try {
        const response = await fetch('/api/churn_by_rfm');
        if (!response.ok) throw new Error('Falha na API RFM');
        const data = await response.json();

        data.sort((a, b) => a.RFM_score - b.RFM_score);

        const backgroundColors = data.map(d => {
            const rfmScore = d.RFM_score;
            if (rfmScore <= 2.0) return 'rgba(220, 38, 38, 0.8)';
            else if (rfmScore <= 2.7) return 'rgba(251, 146, 60, 0.8)';
            else if (rfmScore <= 3.3) return 'rgba(250, 204, 21, 0.8)';
            else if (rfmScore <= 4.0) return 'rgba(132, 204, 22, 0.8)';
            else return 'rgba(34, 197, 94, 0.8)';
        });

        if (window.dashboardCharts.rfm) {
            window.dashboardCharts.rfm.destroy();
        }

        window.dashboardCharts.rfm = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.map(d => `RFM ${d.RFM_score}`),
                datasets: [{
                    label: 'Taxa de Churn (%)',
                    data: data.map(d => d.churn_rate),
                    backgroundColor: backgroundColors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        padding: 12,
                        callbacks: {
                            label: function (context) {
                                const index = context.dataIndex;
                                const dataPoint = data[index];
                                const count = dataPoint.count !== undefined ? dataPoint.count : dataPoint.total_customers;
                                const churnCount = Math.round(count * (dataPoint.churn_rate / 100));

                                return [
                                    `Taxa de Churn: ${dataPoint.churn_rate.toFixed(1)}%`,
                                    `Total: ${count} clientes`,
                                    `Em Churn (est): ${churnCount}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: value => value + '%',
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827'
                        },
                        grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
                    },
                    x: {
                        ticks: { color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827' },
                        grid: { display: false }
                    }
                }
            }
        });
    } catch (error) {
        console.error("Erro ao carregar gráfico RFM:", error);
    }
}

async function renderRecencyChart() {
    const canvas = document.getElementById('recencyHistChart');
    if (!canvas) return;

    try {
        const response = await fetch('/api/recency_hist');
        if (!response.ok) throw new Error('Falha na API Recência');
        const data = await response.json();

        let labels = [], values = [];
        if (Array.isArray(data)) {
            labels = data.map(d => d.bin_label);
            values = data.map(d => d.count);
        } else {
            labels = data.bins;
            values = data.counts;
        }

        if (window.dashboardCharts.recency) {
            window.dashboardCharts.recency.destroy();
        }

        window.dashboardCharts.recency = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Clientes',
                    data: values,
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1,
                    borderRadius: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: context => `Clientes: ${context.parsed.y.toLocaleString('pt-BR')}`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Qtd Clientes' },
                        ticks: { color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827' },
                        grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
                    },
                    x: {
                        title: { display: true, text: 'Recência (dias)' },
                        ticks: {
                            maxRotation: 45, minRotation: 0,
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827'
                        },
                        grid: { display: false }
                    }
                }
            }
        });
    } catch (error) {
        console.error("Erro ao carregar gráfico de Recência:", error);
    }
}


async function loadTopRiskTable() {
    const tableBody = document.getElementById('topRiskBody');
    if (!tableBody) return;

    try {
        const response = await fetch('/api/top_risk');
        const data = await response.json();

        tableBody.innerHTML = '';
        if (!data.length) {
            tableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500">Nenhum dado encontrado.</td></tr>';
            return;
        }

        data.forEach(customer => {
            const row = document.createElement('tr');
            row.className = "hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors";
            const isChurn = customer.churn === 1;
            const churnBadge = isChurn
                ? `<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">Sim</span>`
                : `<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">Não</span>`;

            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200 font-mono" title="${customer.customer_unique_id}">
                    ${customer.customer_unique_id.substring(0, 8)}...
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">${churnBadge}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    <span class="inline-flex px-2 text-xs font-semibold rounded-sm text-white shadow-sm" style="background-color: ${RISK_COLORS[customer.risk_segment] || '#9ca3af'}">
                        ${customer.risk_segment}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${customer.recency_days}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${customer.frequency}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">R$ ${customer.monetary.toFixed(2)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900 dark:text-white">${customer.RFM_score.toFixed(1)}</td>
            `;
            tableBody.appendChild(row);
        });

    } catch (error) {
        console.error("Erro ao carregar Tabela Top Risk:", error);
    }
}

// ==========================================
// Funções de Expansão (Modal)
// ==========================================

// Helper para abrir modal e setar título
async function prepareModal(titleText) {
    const modal = document.getElementById('chartModal');
    const title = document.getElementById('chartModalTitle');
    const canvas = document.getElementById('expandedChart');

    if (!modal || !title || !canvas) return null;

    title.textContent = titleText;
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    if (expandedChartInstance) {
        expandedChartInstance.destroy();
    }

    // Pequeno delay para garantir renderização do DOM
    await new Promise(resolve => setTimeout(resolve, 50));
    return canvas;
}

// 1. Expandir RFM
window.expandChartRFM = async function () {
    const canvas = await prepareModal('📊 Churn por RFM Score (Expandido)');
    if (!canvas) return;

    try {
        const response = await fetch('/api/churn_by_rfm');
        const data = await response.json();
        data.sort((a, b) => a.RFM_score - b.RFM_score);

        const backgroundColors = data.map(d => {
            const rfmScore = d.RFM_score;
            if (rfmScore <= 2.0) return 'rgba(220, 38, 38, 0.8)';
            else if (rfmScore <= 2.7) return 'rgba(251, 146, 60, 0.8)';
            else if (rfmScore <= 3.3) return 'rgba(250, 204, 21, 0.8)';
            else if (rfmScore <= 4.0) return 'rgba(132, 204, 22, 0.8)';
            else return 'rgba(34, 197, 94, 0.8)';
        });

        expandedChartInstance = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.map(d => `RFM ${d.RFM_score}`),
                datasets: [{
                    label: 'Taxa de Churn (%)',
                    data: data.map(d => d.churn_rate),
                    backgroundColor: backgroundColors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        padding: 16,
                        titleFont: { size: 18, weight: 'bold' },
                        bodyFont: { size: 15 },
                        callbacks: {
                            label: function (context) {
                                const index = context.dataIndex;
                                const dataPoint = data[index];
                                const count = dataPoint.count !== undefined ? dataPoint.count : dataPoint.total_customers;
                                const churnCount = Math.round(count * (dataPoint.churn_rate / 100));
                                return [
                                    `Taxa de Churn: ${dataPoint.churn_rate.toFixed(1)}%`,
                                    `Total: ${count} clientes`,
                                    `Em Churn: ${churnCount}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: v => v + '%',
                            font: { size: 14 }
                        }
                    },
                    x: { ticks: { font: { size: 14 } } }
                }
            }
        });
    } catch (e) { console.error(e); }
};

// 2. Expandir Recência
window.expandChartRecency = async function () {
    const canvas = await prepareModal('📈 Distribuição de Recência (Expandido)');
    if (!canvas) return;

    try {
        const response = await fetch('/api/recency_hist');
        const data = await response.json();

        let labels = [], values = [];
        if (Array.isArray(data)) {
            labels = data.map(d => d.bin_label);
            values = data.map(d => d.count);
        } else {
            labels = data.bins;
            values = data.counts;
        }

        expandedChartInstance = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Clientes',
                    data: values,
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Qtd Clientes', font: { size: 14 } },
                        ticks: { font: { size: 14 } }
                    },
                    x: {
                        title: { display: true, text: 'Recência (dias)', font: { size: 14 } },
                        ticks: { font: { size: 12 }, maxRotation: 45, minRotation: 0 }
                    }
                }
            }
        });
    } catch (e) { console.error(e); }
};


// 3. Expandir Distribuição de Risco
window.expandRiskDistribution = async function () {
    const canvas = await prepareModal('👥 Distribuição de Clientes por Segmento (Expandido)');
    if (!canvas) return;

    try {
        const response = await fetch('/api/risk_summary');
        let data = await response.json();
        data.sort((a, b) => {
            const idxA = RISK_ORDER.indexOf(a.risk_segment);
            const idxB = RISK_ORDER.indexOf(b.risk_segment);
            return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
        });

        expandedChartInstance = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.risk_segment),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: data.map(d => RISK_COLORS[d.risk_segment] || '#6b7280'),
                    borderWidth: 2,
                    borderColor: document.documentElement.classList.contains('dark') ? '#1f2937' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 20,
                            font: { size: 16 },
                            color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#111827'
                        }
                    },
                    tooltip: {
                        bodyFont: { size: 16 },
                        titleFont: { size: 18 }
                    }
                }
            }
        });
    } catch (e) {
        console.error(e);
    }
};

// 4. Expandir Churn Rate
window.expandRiskChurnRate = async function () {
    const canvas = await prepareModal('📉 Taxa de Churn por Segmento (Expandido)');
    if (!canvas) return;

    try {
        const response = await fetch('/api/risk_summary');
        let data = await response.json();
        data.sort((a, b) => {
            const idxA = RISK_ORDER.indexOf(a.risk_segment);
            const idxB = RISK_ORDER.indexOf(b.risk_segment);
            return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
        });

        expandedChartInstance = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.map(d => d.risk_segment),
                datasets: [{
                    label: 'Churn Rate (%)',
                    data: data.map(d => d.churn_rate),
                    backgroundColor: data.map(d => RISK_COLORS[d.risk_segment] || '#6b7280'),
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: v => v + '%',
                            font: { size: 16 },
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827'
                        },
                        grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
                    },
                    x: {
                        ticks: {
                            font: { size: 14, weight: 'bold' },
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827'
                        },
                        grid: { display: false }
                    }
                }
            }
        });
    } catch (e) {
        console.error(e);
    }
};

// 5. Expandir Monetary
window.expandRiskMonetary = async function () {
    const canvas = await prepareModal('💰 Valor Monetário em Risco (Expandido)');
    if (!canvas) return;

    try {
        const response = await fetch('/api/risk_summary');
        let data = await response.json();
        data.sort((a, b) => {
            const idxA = RISK_ORDER.indexOf(a.risk_segment);
            const idxB = RISK_ORDER.indexOf(b.risk_segment);
            return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
        });

        expandedChartInstance = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.map(d => d.risk_segment),
                datasets: [{
                    label: 'Valor Monetário (R$)',
                    data: data.map(d => d.monetary_sum),
                    backgroundColor: data.map(d => RISK_COLORS[d.risk_segment] || '#6b7280'),
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: v => 'R$ ' + (v / 1000).toFixed(0) + 'k',
                            font: { size: 16 },
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827'
                        },
                        grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
                    },
                    x: {
                        ticks: {
                            font: { size: 14, weight: 'bold' },
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827'
                        },
                        grid: { display: false }
                    }
                }
            }
        });
    } catch (e) {
        console.error(e);
    }
};

// 6. Expandir Funnel
window.expandRiskFunnel = async function () {
    const canvas = await prepareModal('🔻 Funil de Risco (Expandido)');
    if (!canvas) return;

    try {
        const response = await fetch('/api/risk_summary');
        let data = await response.json();
        data.sort((a, b) => {
            const idxA = RISK_ORDER.indexOf(a.risk_segment);
            const idxB = RISK_ORDER.indexOf(b.risk_segment);
            return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
        });

        expandedChartInstance = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.map(d => d.risk_segment),
                datasets: [{
                    label: 'Clientes',
                    data: data.map(d => d.count),
                    backgroundColor: data.map(d => RISK_COLORS[d.risk_segment] || '#6b7280'),
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            font: { size: 14 },
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827'
                        },
                        grid: { color: document.documentElement.classList.contains('dark') ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }
                    },
                    y: {
                        ticks: {
                            font: { size: 14, weight: 'bold' },
                            color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#111827'
                        },
                        grid: { display: false }
                    }
                }
            }
        });
    } catch (e) {
        console.error(e);
    }
};


// Fechar Modal Global
window.closeChartModal = function () {
    const modal = document.getElementById('chartModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    if (expandedChartInstance) {
        expandedChartInstance.destroy();
        expandedChartInstance = null;
    }
};

