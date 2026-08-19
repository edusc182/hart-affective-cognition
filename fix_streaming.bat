@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0..\hart_agent\src"

REM Add UTF_8 import after Duration
powershell -Command "(Get-Content main.rs) -replace 'use std::time::Duration;', 'use std::time::Duration;`nuse encoding_rs::UTF_8;' | Set-Content main.rs"

REM Add decoder initialization before sampler
powershell -Command "(Get-Content main.rs) -replace '    // JSON estricto: greedy reduce alucinaciones de formato.', '    let mut decoder = UTF_8.new_decoder();`n    // JSON estricto: greedy reduce alucinaciones de formato.' | Set-Content main.rs"

REM Fix token_to_piece call
powershell -Command "(Get-Content main.rs) -replace '        let token_str = model\.token_to_piece\(token\)\.unwrap_or_default\(\);', '        let token_str = model.token_to_piece(token, &mut decoder, true, None).unwrap_or_default();' | Set-Content main.rs"

echo Fixed! Building now...
cd /d "%~dp0"
