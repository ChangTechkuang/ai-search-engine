import streamlit as st
import json, re, faiss, numpy as np
from sentence_transformers import SentenceTransformer

# -------- DATA LOADING --------
def load_code_blocks(json_path):
    docs, sources = [], []
    try:
        with open(json_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            json_objects = re.split(r'\}\s*\{', content)
            for i, obj in enumerate(json_objects, 1):
                s = obj.strip()
                if not s: continue
                if i == 1 and not s.endswith('}'):
                    s += '}'
                else:
                    s = '{' + s if not s.startswith('{') else s
                if not s.endswith('}'):
                    s += '}'
                try:
                    entry = json.loads(s)
                    name = entry.get("file_name", f"unknown_{i}")
                    code = entry.get("code", entry.get("block", "")).strip()
                    imports = entry.get("imports", [])
                    if imports:
                        code = f"Imports: {' '.join(imports)}\n\n{code}"
                    if len(code) > 30:
                        docs.append(code)
                        sources.append(name)
                except Exception as e:
                    st.error(f"Error in JSON object {i}: {e}")
    except FileNotFoundError:
        st.error(f"Error: Dataset file not found: {json_path}")
    except Exception as e:
        st.error(f"Error reading dataset file: {e}")
    return docs, sources

# -------- MODEL AND INDEX SETUP --------
@st.cache_resource
def get_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@st.cache_resource
def get_index():
    model = get_model()
    docs, sources = load_code_blocks("./dataset/jexdataset.jsonl")
    if not docs:
        st.error("❌ No code blocks loaded. Please check ./dataset/jexdataset.jsonl")
        st.stop()
    emb = model.encode(docs, convert_to_numpy=True)
    idx = faiss.IndexFlatL2(emb.shape[1])
    idx.add(emb)
    return model, idx, docs, sources

model, index, docs, sources = get_index()
if 'index_loaded' not in st.session_state:
    st.session_state.index_loaded = True
    st.success(f"✅ Indexed {len(docs)} code blocks.")

# -------- LANGUAGE DETECTION --------
def detect_language(file_path):
    if not file_path: return "text"
    f = file_path.lower()
    ext_map = {
        '.js': 'javascript', '.jsp': 'java', '.java': 'java', '.py': 'python',
        '.html': 'html', '.css': 'css', '.xml': 'xml', '.json': 'json',
        '.sql': 'sql', '.sh': 'bash', '.md': 'markdown', '.cpp': 'cpp',
        '.c': 'c', '.cs': 'csharp', '.php': 'php', '.rb': 'ruby', '.go': 'go',
        '.rs': 'rust', '.ts': 'typescript', '.jsx': 'javascript', '.tsx': 'typescript'
    }
    if f.endswith('_act.jsp') or f.endswith('.jsp') or '*_act.jsp' in f:
        return 'java'
    for ext, lang in ext_map.items():
        if f.endswith(ext):
            return lang
    return "text"

# -------- SEARCH --------
@st.cache_data(max_entries=50)
def search_code(query):
    qvec = model.encode([query], convert_to_numpy=True)
    dist, idxs = index.search(qvec, 2)
    return dist, idxs

# -------- UI --------
st.set_page_config(page_title="AI Code Search", page_icon="🔍", layout="wide")
st.title("🔍 AI Code Search")

query = st.text_input("Search Query", value=st.session_state.get('query', ''), placeholder="Type your question or code search...", key="search_input")
st.session_state.query = query

if query and len(query.strip()) >= 2:
    with st.spinner("Searching..."):
        distances, indices = search_code(query.strip())

    file_blocks, scores, seen = {}, {}, set()
    for dist, idx in zip(distances[0], indices[0]):
        fp, cb = sources[idx], docs[idx]
        block_id = (fp, cb[:100])
        if block_id in seen:
            continue
        seen.add(block_id)
        file_blocks.setdefault(fp, []).append(cb)
        score = 1 / (1 + dist)
        scores[fp] = max(scores.get(fp, 0), score)

    sorted_files = sorted(file_blocks.items(), key=lambda x: scores[x[0]], reverse=True)
    if sorted_files:
        st.subheader("Results")
        for fp, blocks in sorted_files:
            code = "\n\n---\n\n".join(dict.fromkeys(blocks))
            lang, score = detect_language(fp), scores[fp]
            st.markdown(f"**📄 {fp}** (Similarity: {score:.3f})")
            st.code(code, language=lang)
            st.divider()
    else:
        st.info("No results found.")
elif query and len(query.strip()) < 2:
    st.warning("Please enter at least 2 characters to search.")

# -------- SIDEBAR --------
with st.sidebar:
    st.header("About")
    st.info("This AI-powered code search engine uses semantic similarity to find relevant code blocks from your dataset. Enter a natural language query or code-related question to search.")
    st.markdown("---")
    st.metric("Total Code Blocks", len(docs))
    st.markdown("---")
    st.caption("Powered by SentenceTransformers & FAISS")
