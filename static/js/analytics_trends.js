(function () {
  const charts = {};
  const palette = ["#22c55e", "#6366f1", "#f59e0b", "#f97316", "#ec4899", "#06b6d4"];
  const logoImage = new Image();
  logoImage.src = "/static/images/logo2.png?v=20260317";

  const centerLogoPlugin = {
    id: "centerLogo",
    afterDatasetsDraw: function (chart) {
      const meta = chart.getDatasetMeta(0);
      if (!meta || !meta.data || !meta.data.length) return;

      const arc = meta.data[0];
      const x = arc.x;
      const y = arc.y;
      const innerRadius = arc.innerRadius || 0;
      if (!innerRadius) return;

      const ctx = chart.ctx;
      const plateRadius = innerRadius * 0.9;

      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, plateRadius, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(255,255,255,0.96)";
      ctx.fill();
      ctx.restore();

      if (!logoImage.complete) return;

      const logoSize = innerRadius * 1.38;
      ctx.save();
      ctx.translate(x, y);
      ctx.drawImage(logoImage, -logoSize / 2, -logoSize / 2, logoSize, logoSize);
      ctx.restore();
    }
  };

  function endpoint(path) {
    return (window.__API_BASE__ || "") + path;
  }

  function totalOf(values) {
    return values.reduce(function (acc, value) { return acc + Number(value || 0); }, 0);
  }

  function safeText(text) {
    return String(text).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  async function fetchTrend(path) {
    const response = await fetch(endpoint(path), { cache: "no-store" });
    if (!response.ok) throw new Error("Failed API: " + path);
    const json = await response.json();
    if (!json || !Array.isArray(json.labels) || !Array.isArray(json.data)) {
      throw new Error("Invalid JSON shape: " + path);
    }
    return json;
  }

  function renderSummary(summaryId, labels, values) {
    const summary = document.getElementById(summaryId);
    if (!summary) return;

    const total = Math.max(totalOf(values), 1);
    const rows = labels.map(function (label, idx) {
      const value = Number(values[idx] || 0);
      const percent = ((value / total) * 100).toFixed(1);
      return safeText(label) + " — " + percent + "%";
    });
    rows.push("Total Jobs: " + totalOf(values));

    summary.innerHTML = rows.map(function (row) {
      return '<div class="summary-line">' + row + "</div>";
    }).join("");
  }

  function renderChart(canvasId, chartKey, labels, values) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;

    const total = Math.max(totalOf(values), 1);
    if (charts[chartKey]) charts[chartKey].destroy();

    charts[chartKey] = new Chart(canvas, {
      type: "doughnut",
      plugins: [centerLogoPlugin],
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: labels.map(function (_, i) { return palette[i % palette.length]; }),
          borderColor: "#ffffff",
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "60%",
        animation: { duration: 1200 },
        plugins: {
          legend: {
            position: "bottom",
            labels: { boxWidth: 14, boxHeight: 14, padding: 12, color: "#475569" }
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                const value = Number(ctx.parsed || 0);
                const percent = ((value / total) * 100).toFixed(1);
                return ctx.label + " — " + percent + "%";
              }
            }
          }
        }
      }
    });
  }

  async function loadCard(config) {
    const card = document.getElementById(config.cardId);
    if (!card) return;

    const loading = card.querySelector(".trend-loading");
    const content = card.querySelector(".trend-content");

    try {
      const payload = await fetchTrend(config.api);
      renderChart(config.canvasId, config.key, payload.labels, payload.data);
      renderSummary(config.summaryId, payload.labels, payload.data);

      if (loading) loading.classList.add("hidden");
      if (content) content.classList.remove("hidden");
    } catch (error) {
      console.error("Trend chart load failed:", config.api, error);
      if (loading) loading.textContent = "Unable to load chart data.";
    }
  }

  function init() {
    if (typeof Chart === "undefined") {
      console.error("Chart.js is not available.");
      return;
    }

    const cards = [
      {
        key: "location",
        cardId: "trend-card-location",
        canvasId: "locationTrendChart",
        summaryId: "locationTrendSummary",
        api: "/api/analytics/location-trends"
      },
      {
        key: "experience",
        cardId: "trend-card-experience",
        canvasId: "experienceTrendChart",
        summaryId: "experienceTrendSummary",
        api: "/api/analytics/experience-trends"
      },
      {
        key: "domain",
        cardId: "trend-card-domain",
        canvasId: "domainTrendChart",
        summaryId: "domainTrendSummary",
        api: "/api/analytics/domain-trends"
      }
    ];

    logoImage.onload = function () {
      Object.keys(charts).forEach(function (key) {
        if (charts[key]) charts[key].draw();
      });
    };

    Promise.all(cards.map(loadCard)).catch(function () {});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
