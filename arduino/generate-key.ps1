# AES-128: 16 Byte Key
$keyBytes = New-Object byte[] 16
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($keyBytes)

# ───── Arduino Format ─────
$arduinoFormat = ( $keyBytes | ForEach-Object { "0x{0:X2}" -f $_ } ) -join ", "
$arduinoLine = "byte aes_key[] = { $arduinoFormat };"

# ───── Python Format ─────
$pythonFormat = ( $keyBytes | ForEach-Object { "\x{0:X2}" -f $_ } ) -join ""
$pythonLine = "aes_key = b'" + $pythonFormat + "'"

# ───── Klartext-Hex (ohne 0x oder \x) ─────
$hexPlain = ($keyBytes | ForEach-Object { "{0:X2}" -f $_ }) -join ""
$plainLine = "Plain Hex: " + $hexPlain

# ───── Ausgabe ─────
Write-Host "🔐 AES-128 Schlüssel für Arduino:"
Write-Host $arduinoLine
Write-Host ""
Write-Host "🐍 AES-128 Schlüssel für Python:"
Write-Host $pythonLine
Write-Host ""
Write-Host "🧾 AES-128 Schlüssel im Klartext (Hex):"
Write-Host $plainLine
