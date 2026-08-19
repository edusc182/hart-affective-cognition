#!/usr/bin/env python3
import re

# Ajusta esta ruta a tu máquina (relativa a la raíz del proyecto).
file_path = r"hart_agent\src\main.rs"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Add UTF_8 import
content = re.sub(
    r'use std::time::Duration;',
    'use std::time::Duration;\nuse encoding_rs::UTF_8;',
    content
)

# Fix 2: Add decoder before sampler
content = re.sub(
    r'    ctx\.decode\(&mut batch\)\s+\.map_err\(\|err\| format!\("Decode inicial falló:',
    '    ctx.decode(&mut batch)\n        .map_err(|err| format!("Decode inicial falló:',
    content
)

# Add decoder after the first decode
content = re.sub(
    r'        \.map_err\(\|err\| format!\("Decode inicial falló: \{err\}"\)\)\?;(\n\n    // JSON estricto)',
    '        .map_err(|err| format!("Decode inicial falló: {err}"))?;\n\n    let mut decoder = UTF_8.new_decoder();\\1',
    content
)

# Fix 3: Fix token_to_piece call
content = re.sub(
    r'let token_str = model\.token_to_piece\(token\)\.unwrap_or_default\(\);',
    'let token_str = model.token_to_piece(token, &mut decoder, true, None).unwrap_or_default();',
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("File patched successfully!")
