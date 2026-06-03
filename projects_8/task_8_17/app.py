import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from flask import Flask, render_template, jsonify, send_file
from sqlalchemy import create_engine

app = Flask(__name__)
matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# --- ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ student_task ---
# ЗАМЕНИТЕ пароль и порт на свои!
ENGINE = create_engine(
    "postgresql+psycopg2://postgres:student@localhost:5435/student_task"
)


# =============================================================
#   ГЛАВНАЯ СТРАНИЦА
# =============================================================
@app.route("/")
def index():
    return render_template("index.html")


# =============================================================
#   API ДЛЯ СТАТИСТИКИ (исправлено — добавлены min, max, std)
# =============================================================
@app.route("/api/stat/<metric>")
def get_stat(metric):
    """Возвращает статистические метрики по ценам товаров."""
    try:
        # Берём все цены из таблицы prices
        df = pd.read_sql("SELECT price FROM prices", ENGINE)

        if metric == "mean":
            value = f"{df['price'].mean():.2f}"
            label = "Средняя цена"
        elif metric == "median":
            value = f"{df['price'].median():.2f}"
            label = "Медианная цена"
        elif metric == "min":
            value = f"{df['price'].min():.2f}"
            label = "Минимальная цена"
        elif metric == "max":
            value = f"{df['price'].max():.2f}"
            label = "Максимальная цена"
        elif metric == "std":
            value = f"{df['price'].std():.2f}"
            label = "Стандартное отклонение"
        elif metric == "total":
            value = int(df["price"].count())
            label = "Количество записей о ценах"
        else:
            return jsonify({"error": "Неизвестная метрика"}), 400

        return jsonify({"label": label, "value": value})

    except Exception as e:
        print(f"ERROR в /api/stat/{metric}: {e}")
        return jsonify({"error": str(e)}), 500


# =============================================================
#   API ДЛЯ ГРАФИКОВ (исправлен price_types)
# =============================================================
@app.route("/api/chart/<kind>")
def get_chart(kind):
    """Генерирует графики."""
    try:
        fig, ax = plt.subplots(figsize=(8, 5))

        # --- ГИСТОГРАММА РАСПРЕДЕЛЕНИЯ ЦЕН ---
        if kind == "histogram":
            df = pd.read_sql("SELECT price FROM prices", ENGINE)

            ax.hist(df["price"], bins=15, color="#f0ad4e",
                    edgecolor="white", alpha=0.8)

            median = df["price"].median()
            ax.axvline(median, color="crimson", linestyle="--",
                       linewidth=1.5, label=f"Медиана: {median:.2f} руб.")

            mean = df["price"].mean()
            ax.axvline(mean, color="blue", linestyle="--",
                       linewidth=1.5, label=f"Среднее: {mean:.2f} руб.")

            ax.set_xlabel("Цена (руб.)")
            ax.set_ylabel("Количество записей")
            ax.set_title("Распределение цен на товары", fontweight="bold")
            ax.legend()

        # --- СРЕДНЯЯ ЦЕНА ПО КАТЕГОРИЯМ ---
        elif kind == "categories":
            df = pd.read_sql("""
                SELECT p.category,
                       ROUND(AVG(pr.price)::numeric, 2) AS avg_price
                FROM prices pr
                JOIN products p ON pr.product_id = p.id
                GROUP BY p.category
                ORDER BY avg_price DESC
            """, ENGINE)

            bars = ax.barh(df["category"], df["avg_price"],
                           color="#4a90d9", edgecolor="white")

            for bar, value in zip(bars, df["avg_price"]):
                ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
                        f"{value:.2f}", va="center", fontsize=9)

            df_all = pd.read_sql("SELECT price FROM prices", ENGINE)
            overall_avg = df_all["price"].mean()

            ax.axvline(overall_avg, color="darkorange", linestyle="--",
                       linewidth=1.3, label=f"Общее среднее: {overall_avg:.2f} руб.")

            ax.set_xlabel("Средняя цена (руб.)")
            ax.set_title("Средняя цена по категориям товаров", fontweight="bold")
            ax.legend(loc="lower right")

        # --- ТОП-10 ПОСТАВЩИКОВ ---
        elif kind == "suppliers":
            df = pd.read_sql("""
                SELECT s.name AS supplier,
                       COUNT(*) AS product_count
                FROM suppliers s
                GROUP BY s.name
                ORDER BY product_count DESC
                LIMIT 10
            """, ENGINE)

            bars = ax.bar(range(len(df)), df["product_count"],
                          color="#5cb85c", edgecolor="white")

            for i, (bar, count) in enumerate(zip(bars, df["product_count"])):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(count), ha="center", fontsize=9)

            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df["supplier"], rotation=45, ha="right", fontsize=8)
            ax.set_ylabel("Количество товаров")
            ax.set_title("ТОП-10 поставщиков по количеству товаров",
                         fontweight="bold")

            avg_products = df["product_count"].mean()
            ax.axhline(avg_products, color="crimson", linestyle="--",
                       linewidth=1.3,
                       label=f"Среднее: {avg_products:.1f} товаров")
            ax.legend()

        # --- ЦЕНОВЫЕ ДИАПАЗОНЫ (исправлено!) ---
        elif kind == "price_types":
            # Исправленный запрос — без CASE, группируем через pandas
            df = pd.read_sql("SELECT price FROM prices", ENGINE)

            # Создаём категории в pandas
            bins = [0, 1000, 5000, 20000, 50000, float("inf")]
            labels = ["До 1 000 ₽", "1 000 – 5 000 ₽", "5 000 – 20 000 ₽",
                      "20 000 – 50 000 ₽", "Более 50 000 ₽"]
            df["price_range"] = pd.cut(df["price"], bins=bins, labels=labels)

            # Считаем количество в каждой категории
            range_counts = df["price_range"].value_counts().sort_index()

            colors = ["#f0ad4e", "#5cb85c", "#4a90d9", "#d9534f", "#9b59b6"]
            wedges, texts, autotexts = ax.pie(
                range_counts.values,
                labels=range_counts.index,
                autopct="%1.1f%%",
                colors=colors[:len(range_counts)],
                startangle=90
            )

            ax.set_title("Распределение товаров по ценовым диапазонам",
                         fontweight="bold")

        else:
            plt.close(fig)
            return jsonify({"error": "Неизвестный тип графика"}), 400

        plt.tight_layout()
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)

        return send_file(buf, mimetype="image/png")

    except Exception as e:
        print(f"ERROR в /api/chart/{kind}: {e}")
        return jsonify({"error": str(e)}), 500


# =============================================================
#   ЗАПУСК СЕРВЕРА
# =============================================================
if __name__ == "__main__":
    app.run(debug=True, port=5000)