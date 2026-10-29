
from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from collections import deque
from datetime import datetime

app = Flask(__name__)
DATABASE = "wardrobe.db"


# =========================
# DATABASE
# =========================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS clothes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                color TEXT NOT NULL,
                occasion TEXT NOT NULL,
                last_worn TEXT DEFAULT ''
            )
        """)


# =========================
# OOP: CLOTHING CLASS
# =========================

class Clothing:
    def __init__(self, name, category, color, occasion):
        self.name = name
        self.category = category
        self.color = color
        self.occasion = occasion


# =========================
# DSA: STACK AND QUEUE
# =========================

# Stack: most recently worn items are at the end.
recently_worn = []

# Queue: outfit requests are handled first-in, first-out.
outfit_queue = deque()


# =========================
# OOP: WARDROBE CLASS
# =========================

class Wardrobe:
    def add_clothing(self, clothing):
        with get_db() as db:
            db.execute("""
                INSERT INTO clothes (name, category, color, occasion)
                VALUES (?, ?, ?, ?)
            """, (
                clothing.name,
                clothing.category,
                clothing.color,
                clothing.occasion
            ))

    def get_all(self):
        with get_db() as db:
            return db.execute(
                "SELECT * FROM clothes ORDER BY id DESC"
            ).fetchall()

    def search(self, keyword="", category="", color=""):
        query = """
            SELECT * FROM clothes
            WHERE name LIKE ?
            AND category LIKE ?
            AND color LIKE ?
            ORDER BY id DESC
        """
        with get_db() as db:
            return db.execute(query, (
                f"%{keyword}%",
                f"%{category}%",
                f"%{color}%"
            )).fetchall()

    def delete(self, item_id):
        with get_db() as db:
            db.execute("DELETE FROM clothes WHERE id = ?", (item_id,))

    def update(self, item_id, clothing):
        with get_db() as db:
            db.execute("""
                UPDATE clothes
                SET name=?, category=?, color=?, occasion=?
                WHERE id=?
            """, (
                clothing.name,
                clothing.category,
                clothing.color,
                clothing.occasion,
                item_id
            ))

    def mark_worn(self, item_id):
        with get_db() as db:
            item = db.execute(
                "SELECT * FROM clothes WHERE id=?", (item_id,)
            ).fetchone()

            if item:
                worn_time = datetime.now().strftime("%d %b %Y, %I:%M %p")
                db.execute(
                    "UPDATE clothes SET last_worn=? WHERE id=?",
                    (worn_time, item_id)
                )

                recently_worn.append({
                    "id": item["id"],
                    "name": item["name"],
                    "time": worn_time
                })

                # Keep only the 10 most recent actions.
                if len(recently_worn) > 10:
                    recently_worn.pop(0)

    def get_stats(self):
        with get_db() as db:
            total = db.execute(
                "SELECT COUNT(*) FROM clothes"
            ).fetchone()[0]

            categories = db.execute("""
                SELECT category, COUNT(*) AS total
                FROM clothes GROUP BY category
                ORDER BY total DESC
            """).fetchall()

        return total, categories


wardrobe = Wardrobe()


# =========================
# WEBSITE DESIGN
# =========================

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Closet & Co. | Wardrobe Manager</title>
<style>
:root {
  --cream: #f8f5ef;
  --white: #fffefa;
  --brown: #604936;
  --dark: #30261f;
  --muted: #887d70;
  --border: #e9e0d4;
  --green: #64775b;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--cream);
  color: var(--dark);
  font-family: Arial, sans-serif;
}
header {
  background: var(--white);
  border-bottom: 1px solid var(--border);
  padding: 20px 6%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}
.brand { font-size: 23px; font-weight: 700; letter-spacing: -1px; }
.brand span { color: var(--brown); }
header small { color: var(--muted); }
main { max-width: 1200px; margin: 35px auto; padding: 0 22px; }
.hero {
  background: #e9dfd0;
  padding: 32px;
  border-radius: 20px;
  margin-bottom: 24px;
}
.eyebrow {
  color: var(--brown);
  text-transform: uppercase;
  letter-spacing: 2px;
  font-size: 11px;
  font-weight: bold;
}
h1 { font-size: clamp(28px, 4vw, 42px); margin: 12px 0; }
h2 { font-size: 20px; }
p { line-height: 1.6; }
.muted { color: var(--muted); }
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 25px;
}
.stat, .panel {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px;
}
.stat strong { display: block; font-size: 30px; margin-top: 8px; }
.layout {
  display: grid;
  grid-template-columns: 330px 1fr;
  gap: 22px;
  align-items: start;
}
input, select {
  width: 100%;
  padding: 12px;
  margin: 7px 0 14px;
  border: 1px solid var(--border);
  border-radius: 9px;
  background: white;
  font: inherit;
}
label { font-size: 13px; font-weight: bold; }
button, .button {
  display: inline-block;
  border: none;
  border-radius: 9px;
  background: var(--brown);
  color: white;
  padding: 12px 15px;
  font: inherit;
  cursor: pointer;
  text-decoration: none;
  text-align: center;
}
button:hover, .button:hover { opacity: .88; }
.secondary { background: #e9dfd0; color: var(--dark); }
.danger { background: #9c5145; }
.full { width: 100%; }
.toolbar {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr auto;
  gap: 8px;
  align-items: center;
}
.toolbar input, .toolbar select { margin: 0; min-width: 0; }
.toolbar button { padding: 12px; }
.clothes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 20px;
}
.item {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: white;
  padding: 17px;
  min-width: 0;
}
.item-icon {
  background: #f0e8dc;
  height: 76px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 32px;
  margin-bottom: 14px;
}
.item h3 { margin: 7px 0; overflow-wrap: anywhere; }
.tag {
  display: inline-block;
  background: #eee8de;
  color: var(--brown);
  padding: 5px 8px;
  border-radius: 30px;
  font-size: 11px;
  margin: 3px 3px 3px 0;
}
.actions { display: flex; gap: 7px; flex-wrap: wrap; margin-top: 14px; }
.actions button, .actions a { font-size: 12px; padding: 9px; }
.empty { text-align: center; padding: 35px 10px; }
.notice {
  background: #e7eddf;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 15px;
}
footer { text-align: center; padding: 30px; color: var(--muted); font-size: 13px; }
@media(max-width: 850px) {
  .layout { grid-template-columns: 1fr; }
}
@media(max-width: 560px) {
  main { padding: 0 13px; margin-top: 20px; }
  .stats { gap: 8px; }
  .stat { padding: 13px; }
  .stat strong { font-size: 23px; }
  .clothes { grid-template-columns: 1fr; }
  .toolbar { grid-template-columns: 1fr 1fr; }
  .hero { padding: 23px; }
}
</style>
</head>
<body>
<header>
  <div>
    <div class="brand">Closet <span>& Co.</span></div>
    <small>YOUR PERSONAL WARDROBE MANAGER</small>
  </div>
  <a href="#add" class="button">+ Add Clothing</a>
</header>

<main>
  <section class="hero">
    <div class="eyebrow">Your style, organized</div>
    <h1>A wardrobe that works for you.</h1>
    <p class="muted">Keep your favorites organized, discover outfit ideas,
    and make getting dressed a little easier.</p>
  </section>

  {% if message %}
    <div class="notice">{{ message }}</div>
  {% endif %}

  <section class="stats">
    <div class="stat">
      <span class="muted">Total clothing items</span>
      <strong>{{ total }}</strong>
    </div>
    <div class="stat">
      <span class="muted">Categories</span>
      <strong>{{ categories|length }}</strong>
    </div>
    <div class="stat">
      <span class="muted">Recent wear records</span>
      <strong>{{ recent|length }}</strong>
    </div>
  </section>

  <div class="layout">
    <aside>
      <section class="panel" id="add">
        <h2>{{ "Edit clothing" if editing else "Add to your wardrobe" }}</h2>
        <p class="muted">Enter a few details to organize an item.</p>
        <form method="post" action="{{ url_for('save_item') }}">
          <input type="hidden" name="item_id"
                 value="{{ editing.id if editing else '' }}">
          <label>Clothing name</label>
          <input name="name" placeholder="e.g. White linen shirt"
                 value="{{ editing.name if editing else '' }}" required>
          <label>Category</label>
          <select name="category" required>
            {% for c in ["Tops", "Bottoms", "Dresses", "Outerwear",
                         "Shoes", "Accessories", "Ethnic Wear", "Other"] %}
              <option value="{{ c }}"
                {% if editing and editing.category == c %}selected{% endif %}>
                {{ c }}
              </option>
            {% endfor %}
          </select>
          <label>Color</label>
          <input name="color" placeholder="e.g. Beige"
                 value="{{ editing.color if editing else '' }}" required>
          <label>Occasion</label>
          <select name="occasion" required>
            {% for o in ["Casual", "College", "Formal", "Party",
                         "Festive", "Sports", "Everyday", "Other"] %}
              <option value="{{ o }}"
                {% if editing and editing.occasion == o %}selected{% endif %}>
                {{ o }}
              </option>
            {% endfor %}
          </select>
          <button class="full" type="submit">
            {{ "Save Changes" if editing else "Add Clothing" }}
          </button>
          {% if editing %}
            <a class="button secondary full" style="margin-top:8px"
               href="{{ url_for('home') }}">Cancel edit</a>
          {% endif %}
        </form>
      </section>

      <section class="panel" style="margin-top:18px">
        <h2>Outfit idea</h2>
        <p class="muted">Choose an occasion for a suggestion from your clothes.</p>
        <form method="post" action="{{ url_for('outfit') }}">
          <select name="occasion">
            {% for o in ["Casual", "College", "Formal", "Party",
                         "Festive", "Sports", "Everyday", "Other"] %}
              <option>{{ o }}</option>
            {% endfor %}
          </select>
          <button class="full" type="submit">Suggest an Outfit</button>
        </form>
        {% if outfit_items is not none %}
          {% if outfit_items %}
            <div class="notice" style="margin-top:12px">
              <strong>Your {{ outfit_occasion }} picks</strong>
              {% for item in outfit_items %}
                <p>{{ item.name }} · {{ item.color }} {{ item.category }}</p>
              {% endfor %}
            </div>
          {% else %}
            <p class="muted">No matching clothes yet. Add items for this occasion.</p>
          {% endif %}
        {% endif %}
        {% if queue_count %}
          <p class="muted">Outfit requests waiting: {{ queue_count }}</p>
        {% endif %}
      </section>
    </aside>

    <section class="panel">
      <h2>Your clothing collection</h2>
      <p class="muted">Search, filter, and manage your items.</p>
      <form class="toolbar" method="get" action="{{ url_for('home') }}">
        <input name="q" placeholder="Search name..."
               value="{{ q }}">
        <select name="category">
          <option value="">All categories</option>
          {% for c in categories %}
            <option value="{{ c.category }}"
              {% if selected_category == c.category %}selected{% endif %}>
              {{ c.category }}
            </option>
          {% endfor %}
        </select>
        <select name="color">
          <option value="">All colors</option>
          {% for c in colors %}
            <option value="{{ c }}"
              {% if selected_color == c %}selected{% endif %}>{{ c }}</option>
          {% endfor %}
        </select>
        <button type="submit">Search</button>
      </form>

      <form method="get" action="{{ url_for('home') }}"
            style="display:flex;gap:8px;align-items:center;margin-top:12px">
        <input type="hidden" name="q" value="{{ q }}">
        <input type="hidden" name="category" value="{{ selected_category }}">
        <input type="hidden" name="color" value="{{ selected_color }}">
        <label for="sort">Sort:</label>
        <select id="sort" name="sort" onchange="this.form.submit()">
          <option value="newest" {% if sort == "newest" %}selected{% endif %}>Recently added</option>
          <option value="name" {% if sort == "name" %}selected{% endif %}>Name A–Z</option>
          <option value="category" {% if sort == "category" %}selected{% endif %}>Category</option>
        </select>
      </form>

      {% if clothes %}
        <div class="clothes">
          {% for item in clothes %}
            <article class="item">
              <div class="item-icon">♧</div>
              <span class="tag">{{ item.category }}</span>
              <h3>{{ item.name }}</h3>
              <p class="muted">{{ item.color }} · {{ item.occasion }}</p>
              {% if item.last_worn %}
                <p class="muted">Last worn: {{ item.last_worn }}</p>
              {% endif %}
              <div class="actions">
                <form method="post" action="{{ url_for('worn', item_id=item.id) }}">
                  <button type="submit" class="secondary">Mark worn</button>
                </form>
                <a class="button secondary"
                   href="{{ url_for('home', edit=item.id) }}">Edit</a>
                <form method="post" action="{{ url_for('delete_item', item_id=item.id) }}"
                      onsubmit="return confirm('Delete this clothing item?')">
                  <button class="danger" type="submit">Delete</button>
                </form>
              </div>
            </article>
          {% endfor %}
        </div>
      {% else %}
        <div class="empty">
          <div style="font-size:40px">♧</div>
          <h3>Your wardrobe starts here.</h3>
          <p class="muted">Add your first clothing item using the form.</p>
        </div>
      {% endif %}
    </section>
  </div>

  <section class="panel" style="margin-top:22px">
    <h2>Recently worn</h2>
    {% if recent %}
      {% for item in recent|reverse %}
        <p>{{ item.name }} <span class="muted">— {{ item.time }}</span></p>
      {% endfor %}
    {% else %}
      <p class="muted">Your wear history will appear here.</p>
    {% endif %}
  </section>
</main>

<footer>Closet & Co. · Built with Python, Flask, OOP and DSA</footer>
</body>
</html>
"""


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    color = request.args.get("color", "")
    sort = request.args.get("sort", "newest")

    clothes = wardrobe.search(q, category, color)
    clothes = list(clothes)

    # Sorting: O(n log n) average time for Python's Timsort.
    if sort == "name":
        clothes.sort(key=lambda item: item["name"].lower())
    elif sort == "category":
        clothes.sort(key=lambda item: item["category"].lower())

    total, categories = wardrobe.get_stats()

    with get_db() as db:
        colors = [
            row["color"] for row in db.execute(
                "SELECT DISTINCT color FROM clothes ORDER BY color"
            ).fetchall()
        ]

        editing_id = request.args.get("edit", type=int)
        editing = None
        if editing_id:
            editing = db.execute(
                "SELECT * FROM clothes WHERE id=?", (editing_id,)
            ).fetchone()

    return render_template_string(
        PAGE,
        clothes=clothes,
        total=total,
        categories=categories,
        colors=colors,
        selected_category=category,
        selected_color=color,
        q=q,
        sort=sort,
        editing=editing,
        recent=recently_worn,
        message=request.args.get("message", ""),
        outfit_items=None,
        outfit_occasion="",
        queue_count=len(outfit_queue)
    )


@app.route("/save", methods=["POST"])
def save_item():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    color = request.form.get("color", "").strip()
    occasion = request.form.get("occasion", "").strip()
    item_id = request.form.get("item_id", "").strip()

    if not all([name, category, color, occasion]):
        return redirect(url_for("home", message="Please fill in every field."))

    clothing = Clothing(name, category, color, occasion)

    if item_id:
        wardrobe.update(int(item_id), clothing)
        message = "Clothing updated successfully!"
    else:
        wardrobe.add_clothing(clothing)
        message = "Clothing added successfully!"

    return redirect(url_for("home", message=message))


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    wardrobe.delete(item_id)
    return redirect(url_for("home", message="Clothing deleted."))


@app.route("/worn/<int:item_id>", methods=["POST"])
def worn(item_id):
    wardrobe.mark_worn(item_id)
    return redirect(url_for("home", message="Wear history updated!"))


@app.route("/outfit", methods=["POST"])
def outfit():
    occasion = request.form.get("occasion", "Casual")

    # Queue: process the oldest request first.
    outfit_queue.append(occasion)
    requested_occasion = outfit_queue.popleft()

    with get_db() as db:
        matches = db.execute("""
            SELECT * FROM clothes
            WHERE lower(occasion) = lower(?)
            ORDER BY id DESC LIMIT 4
        """, (requested_occasion,)).fetchall()

        total, categories = wardrobe.get_stats()

        colors = [
            row["color"] for row in db.execute(
                "SELECT DISTINCT color FROM clothes ORDER BY color"
            ).fetchall()
        ]

    return render_template_string(
        PAGE,
        clothes=wardrobe.get_all(),
        total=total,
        categories=categories,
        colors=colors,
        selected_category="",
        selected_color="",
        q="",
        sort="newest",
        editing=None,
        recent=recently_worn,
        message="Outfit suggestion generated!",
        outfit_items=matches,
        outfit_occasion=requested_occasion,
        queue_count=len(outfit_queue)
    )


# Create the database when the app starts.
init_db()

if __name__ == "__main__":
    app.run(debug=True)
