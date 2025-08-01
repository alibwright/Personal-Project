from flask import Flask, request, render_template_string, render_template
import csv
from difflib import get_close_matches

app = Flask(__name__)

# Load prices once on startup for speed
def load_prices(filename="/Users/alisonbarone/Desktop/Personal Project/Winco_Meat_Veggies_Large_cleaned.csv"):
    prices = {}
    with open(filename, mode='r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            store = row['store'].strip()
            item = row['item'].strip().lower()
            price = float(row['price_per_unit'])
            unit = row['unit'].strip()
            prices[(store, item)] = (price, unit)
    return prices

prices = load_prices()

def suggest_items(input_item, store, all_items, max_suggestions=3):
    # Filter for items in the current store only
    store_items = [item for (s, item) in all_items if s == store.lower()]
    
    # Try to get close matches
    matches = get_close_matches(input_item, store_items, n=max_suggestions, cutoff=0.6)
    return matches


def parse_grocery_list(text):
    shopping_list = {}
    # Expect input lines like: item, quantity
    for line in text.strip().split("\n"):
        if "," in line:
            item, qty = line.split(",", 1)
            item = item.strip().lower()
            try:
                qty = float(qty.strip())
                shopping_list[item] = qty
            except ValueError:
                pass
    return shopping_list

@app.route('/', methods=['GET', 'POST'])
def home():
    result = None
    missing_items = []
    if request.method == 'POST':
        store = request.form.get('store').strip()
        grocery_text = request.form.get('grocery_list')
        shopping_list = parse_grocery_list(grocery_text)
        total = 0.0
        details = []
        for item, qty in shopping_list.items():
            key = (store, item)
            if key in prices:
                price, unit = prices[key]
                cost = price * qty
                total += cost
                details.append(f"{item.title()} ({qty} {unit}): ${cost:.2f}")
            else:
             # Suggest similar items
                suggestions = suggest_items(item, store, prices.keys())
                if suggestions:
                    formatted_suggestions = ", ".join(suggestions)
                    missing_items.append(f"{item} (Did you mean: {formatted_suggestions}?)")
                else:
                    missing_items.append(f"{item} (No suggestions)")
        result = {
            'total': total,
            'details': details,
            'missing': missing_items,
            'store': store
        }
    return render_template('home.html', result=result), render_template_string('''
        <h1>Grocery Price Calculator</h1>
        <form method="POST">
            <label>Which store are you shopping at?</label><br>
            <input name="store" required placeholder="e.g., 
Winco"><br><br>
            
            <label>Enter grocery list (one item per line, format: 
item, quantity):</label><br>
            <textarea name="grocery_list" rows="10" cols="40" 
placeholder="chicken breast, 2
broccoli, 1.5
bacon, 1" required></textarea><br><br>
            
            <button type="submit">Calculate Total</button>
        </form>
        
        {% if result %}
            <h2>Results for {{ result.store }}</h2>
            <ul>
            {% for line in result.details %}
                <li>{{ line }}</li>
            {% endfor %}
            </ul>
            <p><strong>Total cost: ${{ "%.2f"|format(result.total) 
}}</strong></p>
            
            {% if result.missing %}
                <p><em>Missing items (not found):</em></p>
                <ul>
                {% for mi in result.missing %}
                    <li>{{ mi }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endif %}
    ''' , result=result)

if __name__ == '__main__':
    app.run(debug=True)
