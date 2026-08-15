$hash = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
Write-Output ('COMMAND_FILE_SHA256=' + $hash)
