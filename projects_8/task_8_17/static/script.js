// =============================================================
//   КОНСТАНТЫ
// =============================================================
const resultArea = document.getElementById("result-area");

// =============================================================
//   ОБРАБОТЧИК КЛИКОВ (делегирование событий)
// =============================================================
document.querySelector(".controls").addEventListener("click", (event) => {
  const btn = event.target.closest(".action-btn");
  if (!btn) return;

  const action = btn.dataset.action;
  const metric = btn.dataset.metric;
  const kind = btn.dataset.kind;

  // Кнопка "Очистить"
  if (btn.id === "clear-btn") {
    resultArea.innerHTML = `
      <p class="placeholder">
        ← Нажмите кнопку слева, чтобы увидеть результат
      </p>
    `;
    return;
  }

  // Статистика
  if (action === "stat" && metric) {
    loadStat(metric);
  }

  // Графики
  if (action === "chart" && kind) {
    loadChart(kind);
  }
});

// =============================================================
//   ЗАГРУЗКА СТАТИСТИКИ
// =============================================================
async function loadStat(metric) {
  // Показываем "Загрузка..."
  resultArea.innerHTML = `<p class="loading">⏳ Загрузка...</p>`;

  try {
    const response = await fetch(`/api/stat/${metric}`);

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || "Ошибка сервера");
    }

    const data = await response.json();

    // Вставляем результат
    resultArea.innerHTML = `
      <div class="stat-card">
        <div class="label">${data.label}</div>
        <div class="value">${data.value}</div>
      </div>
    `;

  } catch (error) {
    resultArea.innerHTML = `
      <div class="error">
        <strong>Ошибка:</strong> ${error.message}
      </div>
    `;
  }
}

// =============================================================
//   ЗАГРУЗКА ГРАФИКОВ
// =============================================================
async function loadChart(kind) {
  // Показываем "Загрузка..."
  resultArea.innerHTML = `<p class="loading">⏳ Построение графика...</p>`;

  try {
    // Добавляем timestamp, чтобы браузер не кэшировал
    const timestamp = new Date().getTime();
    const imageUrl = `/api/chart/${kind}?t=${timestamp}`;

    // Вставляем картинку
    resultArea.innerHTML = `
      <div class="chart-container">
        <img src="${imageUrl}" alt="График" />
      </div>
    `;

  } catch (error) {
    resultArea.innerHTML = `
      <div class="error">
        <strong>Ошибка:</strong> ${error.message}
      </div>
    `;
  }
}