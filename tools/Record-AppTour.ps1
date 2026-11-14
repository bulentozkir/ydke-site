[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$AppPath,
    [Parameter(Mandatory)][string]$ProfilePath,
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\assets\tour'),
    [switch]$InspectOnly
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class TourWindow {
    [StructLayout(LayoutKind.Sequential)]
    public struct Rect { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out Rect rect);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
'@
[TourWindow]::SetProcessDPIAware() | Out-Null
$AppPath = [IO.Path]::GetFullPath($AppPath)
$ProfilePath = [IO.Path]::GetFullPath($ProfilePath)
$OutputPath = [IO.Path]::GetFullPath($OutputPath)
if (-not (Test-Path -LiteralPath $AppPath -PathType Leaf)) { throw "App executable not found: $AppPath" }
if (Test-Path -LiteralPath $ProfilePath) { throw 'Use a new, empty profile path for each recording. Existing profiles are never recorded.' }
if ($ProfilePath.StartsWith((Join-Path $env:LOCALAPPDATA 'YDKE'), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The real YDKE profile must never be used for a recording.'
}
New-Item -ItemType Directory -Path $ProfilePath -Force | Out-Null
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
$process = Start-Process -FilePath $AppPath -WorkingDirectory (Split-Path $AppPath) `
    -ArgumentList @('--test-mode', "--data-dir=`"$ProfilePath`"") -PassThru
$frames = New-Object 'Collections.Generic.List[object]'

function Find-Control([string]$id, [string]$name = '') {
    $property = if ($id) { [Windows.Automation.AutomationElement]::AutomationIdProperty } else { [Windows.Automation.AutomationElement]::NameProperty }
    $value = if ($id) { $id } else { $name }
    $condition = New-Object Windows.Automation.PropertyCondition($property, $value)
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        $element = $script:root.FindFirst([Windows.Automation.TreeScope]::Descendants, $condition)
        if ($element -and -not $element.Current.IsOffscreen) { return $element }
        Start-Sleep -Milliseconds 200
    }
    throw "Visible app control not found: id=$id name=$name"
}

function Invoke-Control([string]$id, [string]$name = '') {
    $element = Find-Control $id $name
    if (-not $element.Current.IsEnabled) { throw "App control is disabled: $id $name" }
    $pattern = $null
    if ($element.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern, [ref]$pattern)) { $pattern.Invoke() }
    elseif ($element.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern, [ref]$pattern)) { $pattern.Select() }
    else { throw "Control cannot be invoked without global mouse input: $id $name" }
    Start-Sleep -Milliseconds 1100
}

function Save-Frame([string]$id, [string[]]$controls) {
    Start-Sleep -Milliseconds 500
    $rect = New-Object TourWindow+Rect
    if (-not [TourWindow]::GetWindowRect($script:handle, [ref]$rect)) { throw 'Cannot measure the YDKE window.' }
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    if ($width -lt 800 -or $height -lt 600) { throw "Recording window is too small: ${width}x${height}" }
    $boxes = @()
    foreach ($control in $controls) {
        $element = Find-Control $control
        $bounds = $element.Current.BoundingRectangle
        $x = 100 * ($bounds.Left - $rect.Left) / $width
        $y = 100 * ($bounds.Top - $rect.Top) / $height
        $w = 100 * $bounds.Width / $width
        $h = 100 * $bounds.Height / $height
        if ($w -le 0 -or $h -le 0 -or $x -lt 0 -or $y -lt 0 -or ($x + $w) -gt 100 -or ($y + $h) -gt 100) {
            throw "Control lies outside the recorded window: $control"
        }
        $boxes += @{ x=$x; y=$y; width=$w; height=$h; control=$control }
    }
    $bitmap = New-Object Drawing.Bitmap($width, $height)
    $graphics = [Drawing.Graphics]::FromImage($bitmap)
    $dc = $graphics.GetHdc()
    try {
        if (-not [TourWindow]::PrintWindow($script:handle, $dc, 2)) { throw 'Window capture failed. Desktop-wide capture is not permitted.' }
    }
    finally { $graphics.ReleaseHdc($dc); $graphics.Dispose() }
    try {
        $colors = New-Object 'Collections.Generic.HashSet[int]'
        for ($x = 0; $x -lt $width; $x += 37) {
            for ($y = 0; $y -lt $height; $y += 37) { $colors.Add($bitmap.GetPixel($x, $y).ToArgb()) | Out-Null }
        }
        if ($colors.Count -lt 15) { throw 'Captured window appears blank; no placeholder recording was saved.' }
        $bitmap.Save((Join-Path $OutputPath "$id.png"), [Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $bitmap.Dispose() }
    $frames.Add(@{ id=$id; image="$id.png"; width=$width; height=$height; highlights=$boxes })
    Write-Output "Recorded $id (${width}x${height})"
}

try {
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        $process.Refresh()
        if ($process.HasExited) { throw "YDKE exited before recording (exit $($process.ExitCode))." }
        if ($process.MainWindowHandle -ne [IntPtr]::Zero) { break }
        Start-Sleep -Milliseconds 500
    }
    $script:handle = $process.MainWindowHandle
    if ($script:handle -eq [IntPtr]::Zero) { throw 'YDKE did not open a recordable window.' }
    $script:root = [Windows.Automation.AutomationElement]::FromHandle($script:handle)
    Find-Control 'shell.StudyLanguage' | Out-Null
    if ($InspectOnly) {
        $elements = $script:root.FindAll([Windows.Automation.TreeScope]::Descendants, [Windows.Automation.Condition]::TrueCondition)
        foreach ($element in $elements) {
            if (-not $element.Current.IsOffscreen) {
                Write-Output ("{0} | {1} | {2}" -f $element.Current.ControlType.ProgrammaticName, $element.Current.AutomationId, $element.Current.Name)
            }
        }
        return
    }
    Save-Frame 'toolbar' @('shell.StudyLanguage', 'shell.Level', 'shell.WindowMode')
    Invoke-Control 'CardsItem'
    Save-Frame 'cards' @('cards.Start')
    Invoke-Control 'cards.Start'
    Save-Frame 'card-hidden' @('cards.Reveal', 'cards.Next')
    $hiddenCard = $frames[$frames.Count - 1]
    $frames.RemoveAt($frames.Count - 1)
    Invoke-Control 'cards.Reveal'
    Save-Frame 'card-reveal' @('cards.Next', 'cards.Undo')
    $frames[$frames.Count - 1]['before'] = $hiddenCard
    Invoke-Control 'QuizItem'
    Save-Frame 'quiz-picker' @('quiz.ExamPicker')
    Invoke-Control 'quiz.Exam.1'
    Invoke-Control 'quiz.Choice.0'
    Save-Frame 'quiz-answer' @('quiz.Continue')
    Invoke-Control 'WordsItem'
    Save-Frame 'words' @('library.Search', 'library.Filter.Favorites', 'library.Filter.Known')
    Invoke-Control 'SimpleGamesItem'
    Invoke-Control 'games.Item.hangman'
    Save-Frame 'games' @('game.Start', 'game.Rules', 'game.Hint')
    Invoke-Control 'StatsItem'
    Save-Frame 'statistics' @('stats.Sections')
    Invoke-Control 'ProfileItem'
    Save-Frame 'settings' @('settings.UiLanguage', 'settings.DailyGoal')
    Invoke-Control 'HelpItem'
    Save-Frame 'help' @('help.Screen', 'help.Cards', 'help.Widget')
    $manifest = @{
        interfaceLanguage='tr'
        captureMethod='Window-only PrintWindow, isolated --test-mode profile'
        appVersion=[Diagnostics.FileVersionInfo]::GetVersionInfo($AppPath).ProductVersion
        frames=$frames.ToArray()
    } | ConvertTo-Json -Depth 8
    [IO.File]::WriteAllText((Join-Path $OutputPath 'manifest.json'), $manifest, (New-Object Text.UTF8Encoding($false)))
}
finally {
    $process.Refresh()
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force }
}
