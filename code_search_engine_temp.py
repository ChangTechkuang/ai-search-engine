from flask import Flask, request, render_template_string
from functools import lru_cache
import os, re, faiss, numpy as np
from sentence_transformers import SentenceTransformer

# ---- Load all code blocks ----
def load_code_blocks(folder):
    docs, sources = [], []
    for root, _, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                    blocks = re.split(r'\n\s*\n|(?<=\})\s*\n', text)
                    for block in blocks:
                        clean = block.strip()
                        if len(clean) > 30:
                            docs.append(clean)
                            sources.append(path)
            except Exception as e:
                print("Error reading:", path, e)
    return docs, sources

# ---- Initialize model + FAISS ----
model = SentenceTransformer("all-MiniLM-L6-v2")
docs, sources = load_code_blocks("./jex-dev-snippets")
embeddings = model.encode(docs, convert_to_numpy=True)
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)
print(f"✅ Indexed {len(docs)} code blocks.")

# ---- Search function with cache ----
@lru_cache(maxsize=50)
def search_code(query):
    query_vec = model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_vec, 3)
    return distances, indices

# ---- Flask app ----
app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html>
    <head>
        <title>AI Code Search</title>
        <style>
        body { font-family: Arial; margin: 40px; background: #f8f9fa; }
        h1 { color: #333; }
        form { margin-bottom: 20px; }
        input { width: 100%; font-size: 14px; padding: 8px; margin-bottom: 10px; }
        pre { background: #272822; color: #f8f8f2; padding: 10px; border-radius: 8px; overflow-x: auto; }
        .file { font-size: 13px; color: #888; margin-top: 5px; }
        button { padding: 10px 20px; font-size: 15px; border: none; background: #007bff; color: white; border-radius: 6px; cursor: pointer; }
        button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>🔍 AI Code Search</h1>
        <form method="post">
        <input type="text" name="query" placeholder="Type your question or code search..."><br>
        <button type="submit">Search</button>
        </form>

        {% if results %}
        <h2>Results:</h2>
        {% for res in results %}
            <div class="file">{{res['file']}}</div>
            <pre>{{res['code']}}</pre>
        {% endfor %}
        {% endif %}
    </body>
    <script>
    const input = document.getElementById('query');
    const form = document.getElementById('searchForm');

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
        e.preventDefault();
        console.log('Searching for:', input.value); // optional custom logic
        form.submit();
        }
    });
    </script>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    query = ""
    if request.method == "POST":
        query = request.form["query"].strip()
        if not query or len(query) < 2:
            return render_template_string(HTML_TEMPLATE, results=[], query=query)

        distances, indices = search_code(query)

        # Group results by file and combine code blocks
        file_results, file_scores = {}, {}
        for dist, idx in zip(distances[0], indices[0]):
            file_path, code_block = sources[idx], docs[idx]
            file_results.setdefault(file_path, []).append(code_block)
            score = 1 - dist
            file_scores[file_path] = (file_scores.get(file_path, 0) + score)

        # Deduplicate + sort
        results = [{
            "file": file_path,
            "code": "\n\n".join(list(dict.fromkeys(code_blocks))),
            "score": f"{file_scores[file_path]:.3f}"
        } for file_path, code_blocks in file_results.items()]
        results = sorted(results, key=lambda r: float(r["score"]), reverse=True)

    return render_template_string(HTML_TEMPLATE, results=results, query=query)

if __name__ == "__main__":
    print("🚀 Running on http://127.0.0.1:5000")
    app.run(debug=True)