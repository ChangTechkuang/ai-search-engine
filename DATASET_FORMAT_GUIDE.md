# Dataset Format Guide for *_act.jsp Files with Library Imports

## Current Data Formats

### Format 1: Simple Format (from `create_dataset.py`)
```json
{
  "file_name": "action/JexData__getItemSize_act.jsp",
  "ext": "jsp",
  "code": "<%@page contentType=\"text/html; charset=UTF-8\"%>\n\n<%@page import=\"jex.web.util.WebCommonUtil\"%>\n<%@page import=\"jex.data.JexData\"%>\n...\n<% ... code ... %>"
}
```

**Pros:**
- Simple structure
- Contains full file content
- Easy to generate

**Cons:**
- Imports not searchable separately
- Harder to filter by library usage

---

### Format 2: Block-based Format (from `search_app2.py`)
```json
{"id": 1, "file_name": "JexData__getItemSize_act.jsp", "path": "action/JexData__getItemSize_act.jsp", "block": "<%@page contentType=\"text/html; charset=UTF-8\"%>"}
{"id": 2, "file_name": "JexData__getItemSize_act.jsp", "path": "action/JexData__getItemSize_act.jsp", "block": "<%@page import=\"jex.web.util.WebCommonUtil\"%>\n..."}
{"id": 3, "file_name": "JexData__getItemSize_act.jsp", "path": "action/JexData__getItemSize_act.jsp", "block": "JexData input = util.createIDOData(\"TEST_IDO\");\n..."}
```

**Pros:**
- Splits code into smaller searchable blocks
- Better for finding specific code patterns

**Cons:**
- Multiple entries per file
- Imports separated from code context

---

### Format 3: Enhanced Format with Imports (Recommended)
```json
{
  "file_name": "action/JexData__getItemSize_act.jsp",
  "ext": "jsp",
  "code": "<%@page contentType=\"text/html; charset=UTF-8\"%>\n\n<%@page import=\"jex.web.util.WebCommonUtil\"%>\n...\n<% ... code ... %>",
  "imports": [
    "jex.web.util.WebCommonUtil",
    "jex.data.JexData",
    "jex.data.impl.JexDataRecordList",
    "jex.resource.cci.JexConnection",
    "jex.web.exception.JexWebBIZException",
    "jex.resource.cci.JexConnectionManager",
    "jex.data.impl.ido.JexDataInIDO",
    "jex.data.item.DataItem"
  ],
  "code_body": "JexData input = util.createIDOData(\"TEST_IDO\");\nint fieldSize = input._getItemSize();\n..."
}
```

**Pros:**
- ✅ Imports extracted as searchable metadata
- ✅ Full code preserved
- ✅ Code body available without directives
- ✅ Better searchability (can search by library name)
- ✅ Supports filtering by imports

**Cons:**
- Slightly more complex structure

---

## How to Generate Enhanced Format

Use the provided script:
```bash
python create_dataset_with_imports.py
```

This will:
1. Extract all `<%@page import="...">` statements
2. Store them in an `imports` array
3. Extract code body without page directives
4. Keep full code in `code` field

---

## Example JSP File Structure

```jsp
<%@page contentType="text/html; charset=UTF-8"%>

<%@page import="jex.web.util.WebCommonUtil"%>
<%@page import="jex.data.JexData"%>
<%@page import="jex.data.item.DataItem"%>
<%
    JexData input = util.createIDOData("TEST_IDO");
    int fieldSize = input._getItemSize();
    
    for(int i = 0; i < fieldSize; i++) {
        DataItem item = input._getDataItem(i);
        String fieldId = item.getId();
    }
%>
```

**Extracted Data:**
- `imports`: `["jex.web.util.WebCommonUtil", "jex.data.JexData", "jex.data.item.DataItem"]`
- `code`: Full file content
- `code_body`: Code between `<%` and `%>` tags

---

## Search Engine Support

The `load_code_blocks()` function in `code_search_engine.py` now supports all three formats:

1. **Format 1**: Uses `code` field directly
2. **Format 2**: Uses `block` field
3. **Format 3**: Uses `code` field + includes `imports` in searchable text

When `imports` field is present, it's prepended to the code for better searchability, so you can search for:
- Library names: "JexData", "WebCommonUtil"
- Full code: "createIDOData"
- Combined: "JexData createIDOData"

---

## Recommendation

**Use Format 3 (Enhanced Format)** for `*_act.jsp` files because:
- Better searchability for library-specific code
- Can filter/search by imported libraries
- Maintains full code context
- More structured and maintainable