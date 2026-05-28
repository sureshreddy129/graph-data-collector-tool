param(
    [string]$GraphToken,
    [string]$TeamsToken,
    [string]$OutputPath
)

# Import Teams module
Import-Module -Name MicrosoftTeams -RequiredVersion 5.1.0

# Connect
Connect-MicrosoftTeams -AccessTokens @($GraphToken, $TeamsToken)

Write-Host "Fetching Teams DDI numbers..."

# Fetch users with LineURI
$users = Get-CsOnlineUser -Filter {LineURI -ne $Null} |
    Select-Object DisplayName, UserPrincipalName, LineURI

# Ensure output directory exists
if (!(Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath | Out-Null
}

# Save JSON
$users | ConvertTo-Json -Depth 5 |
    Out-File "$OutputPath\DDIs.json"

Write-Host "DDI fetch completed."