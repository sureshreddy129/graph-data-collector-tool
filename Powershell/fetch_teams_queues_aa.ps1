param (
    [string]$GraphToken,
    [string]$TeamsToken,
    [string]$OutputPath
)

Import-Module MicrosoftTeams

Write-Output "Connecting to Microsoft Teams..."
Connect-MicrosoftTeams -AccessTokens @($GraphToken, $TeamsToken)

Write-Output "Fetching Call Queues..."
Get-CsCallQueue |
    ConvertTo-Json -Depth 6 |
    Out-File "$OutputPath\CallQueues.json"

Write-Output "Fetching Auto Attendants..."
Get-CsAutoAttendant |
    ConvertTo-Json -Depth 6 |
    Out-File "$OutputPath\AutoAttendants.json"

