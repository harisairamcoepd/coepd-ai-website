(function () {
  let cityChart;
  let experienceChart;
  let domainChart;

  async function fetchJson(path) {
    const endpoint = (window.__API_BASE__ || '') + path;
    const response = await fetch(endpoint, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`Request failed: ${path}`);
    }
    const data = await response.json();
    if (!data || !Array.isArray(data.labels) || !Array.isArray(data.data)) {
      throw new Error(`Invalid response shape for ${path}`);
    }
    return data;
  }

  function destroyIfExists(chart) {
    if (chart) {
      chart.destroy();
    }
  }

  function renderCityChart(payload) {
    const canvas = document.getElementById('cityChart');
    if (!canvas || typeof Chart === 'undefined') return;
    destroyIfExists(cityChart);
    cityChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: payload.labels,
        datasets: [{
          label: 'Jobs',
          data: payload.data,
          backgroundColor: '#3b82f6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  function renderExperienceChart(payload) {
    const canvas = document.getElementById('experienceChart');
    if (!canvas || typeof Chart === 'undefined') return;
    destroyIfExists(experienceChart);
    experienceChart = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: payload.labels,
        datasets: [{
          data: payload.data,
          backgroundColor: ['#0f766e', '#6366f1', '#f59e0b', '#ef4444', '#3b82f6']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }

  function renderIndustryChart(payload) {
    const canvas = document.getElementById('domainChart');
    if (!canvas || typeof Chart === 'undefined') return;
    destroyIfExists(domainChart);
    domainChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: payload.labels,
        datasets: [{
          label: 'Demand',
          data: payload.data,
          backgroundColor: '#10b981'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  async function initCharts() {
    if (typeof Chart === 'undefined') {
      console.error('Chart.js not loaded.');
      return;
    }

    try {
      const [city, experience, industry] = await Promise.all([
        fetchJson('/api/analytics/city-distribution'),
        fetchJson('/api/analytics/experience-distribution'),
        fetchJson('/api/analytics/top-industries')
      ]);

      renderCityChart(city);
      renderExperienceChart(experience);
      renderIndustryChart(industry);
    } catch (error) {
      console.error('Analytics chart load failed:', error);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCharts);
  } else {
    initCharts();
  }
})();
