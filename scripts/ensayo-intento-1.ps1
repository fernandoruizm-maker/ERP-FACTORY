[CmdletBinding()]
param(
    [ValidateSet('Preparar', 'Ejecutar')][string]$Modo = 'Preparar',
    [ValidateRange(1, 1000000)][int]$Intento = 1,
    [string]$Python = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
    [string]$Autorizacion,
    [string]$ShaRevisado,
    [switch]$ConfirmoAutorizacionExpresa
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw 'Python local no encontrado. No se instala nada.' }

# Both phases use this exact process and environment allowlist. No profile/key additions.
function New-TrialProcessInfo([string]$Action) {
    $info = [System.Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $Python
    $info.WorkingDirectory = $repo
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    # ArgumentList requires PowerShell 7/.NET; no shell command interpolation.
    if ($null -eq $info.ArgumentList) { throw 'Se requiere PowerShell 7 para la ejecucion privada.' }
    foreach ($value in @('-B','-m','factory2.trial_command',$Action,'--attempt',"$Intento",'--authorization',$Autorizacion,'--expected-sha',$ShaRevisado)) {
        $info.ArgumentList.Add($value)
    }
    $info.Environment.Clear()
    foreach ($name in @('PATH','SYSTEMROOT','WINDIR','TEMP','TMP','PATHEXT','COMSPEC')) {
        $value = [Environment]::GetEnvironmentVariable($name, 'Process')
        if ($null -ne $value) { $info.Environment[$name] = $value }
    }
    $info.Environment['PYTHONDONTWRITEBYTECODE'] = '1'
    $info.Environment['PYTHONIOENCODING'] = 'utf-8'
    return $info
}

Push-Location $repo
try {
    if ($Modo -eq 'Preparar') {
        # Pure local calculation. No key prompt, Store, Docker or provider.
        & $Python -B -m factory2.trial_command prepare --attempt $Intento
        if ($LASTEXITCODE -ne 0) { throw 'Preparacion bloqueada.' }
        return
    }
    if (-not $ConfirmoAutorizacionExpresa -or $ShaRevisado -notmatch '^[0-9a-f]{40}$' -or
        -not (Test-Path -LiteralPath $Autorizacion -PathType Leaf)) {
        throw 'Falta autorizacion expresa, SHA revisado o expediente. No se pide la clave.'
    }
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'Se requiere PowerShell 7; no se pide la clave.' }
    # Still offline. False switch, missing ledger/review, wrong SHA or reused
    # attempt stop BEFORE displaying any private credential prompt.
    $check = [System.Diagnostics.Process]::Start((New-TrialProcessInfo 'check'))
    try {
        $check.StandardInput.Close()
        $checkOutput = $check.StandardOutput.ReadToEndAsync()
        $checkErrors = $check.StandardError.ReadToEndAsync()
        $check.WaitForExit()
        $checked = $checkOutput.GetAwaiter().GetResult() | ConvertFrom-Json
        if ($check.ExitCode -ne 0 -or $checked.status -ne 'PREFLIGHT_OK_NOT_EXECUTED') {
            $code = 'PILOT_PREFLIGHT_UNEXPECTED_NO_RETRY'
            if ($checked.reason_code -cmatch '^[A-Z0-9_]{1,80}$') { $code = $checked.reason_code }
            throw "Comprobacion bloqueada: $code. No se pide la clave ni se consume el intento."
        }
    } finally {
        $check.Dispose()
    }
    # Future authorized use only, in a terminal Fernando opens privately.
    $secret = Read-Host 'Clave restringida de Responses (entrada oculta; no compartir pantalla)' -AsSecureString
    $pointer = [IntPtr]::Zero
    $plain = $null
    $child = $null
    try {
        $info = New-TrialProcessInfo 'run'
        $child = [System.Diagnostics.Process]::Start($info)
        $output = $child.StandardOutput.ReadToEndAsync()
        $errors = $child.StandardError.ReadToEndAsync()
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
        $child.StandardInput.WriteLine($plain)
        $child.StandardInput.Close()
        $child.WaitForExit()
        # The Python entrypoint emits only a small allowlisted result. Never echo stderr.
        $result = $output.GetAwaiter().GetResult() | ConvertFrom-Json
        if ($child.ExitCode -ne 0) {
            $code = 'PILOT_PREFLIGHT_UNEXPECTED_NO_RETRY'
            if ($result.reason_code -cmatch '^[A-Z0-9_]{1,80}$') { $code = $result.reason_code }
            throw "Ensayo bloqueado: $code. Sin reintento automatico."
        }
        $result | Select-Object status,attempt,reason_code,usage,calculated_cost_usd,publication_allowed | ConvertTo-Json -Depth 4
    } finally {
        if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
        $plain = $null
        if ($null -ne $secret) { $secret.Dispose() }
        if ($null -ne $child) { $child.Dispose() }
    }
} finally {
    Pop-Location
}
