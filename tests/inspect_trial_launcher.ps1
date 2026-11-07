param([string]$Launcher)
$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Launcher, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Launcher syntax invalid' }
$definition = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'New-TrialProcessInfo'
}, $true)
if ($null -eq $definition) { throw 'Missing common process constructor' }
# Load only a function declaration; the rest of the launch script is never executed.
. ([scriptblock]::Create($definition.Extent.Text))
$Python = 'FICTICIO_NO_EJECUTAR'
$repo = 'FICTICIO'
$Autorizacion = 'FICTICIO.json'
$ShaRevisado = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
$observed = foreach ($action in @('check','run')) {
    $info = New-TrialProcessInfo $action
    [pscustomobject]@{
        action = $info.ArgumentList[3]
        environment = @($info.Environment.Keys | Sort-Object)
        shell = $info.UseShellExecute
    }
}
$observed | ConvertTo-Json -Depth 4 -Compress
