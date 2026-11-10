# Builds one preview image of a character's action sheets (enlarged) plus a game-scale
# comparison with the current hero on the street background.
# Usage: powershell -File tools/sprites/preview_sheets.ps1 -SheetDir assets/characters/base -Out assets/characters/previews/base.png -Title "기본 몸"
param(
    [Parameter(Mandatory)] [string] $SheetDir,
    [Parameter(Mandatory)] [string] $Out,
    [string] $Title = "",
    [int] $Scale = 2
)
Add-Type -AssemblyName System.Drawing
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$actions = "idle", "walk", "sneak", "swing", "hurt", "down", "pickup"
$cellW = 96; $cellH = 64; $labelW = 90; $rowH = $cellH * $Scale + 10
$sheets = @{}
foreach ($a in $actions) {
    $path = Join-Path $SheetDir "$a.png"
    if (Test-Path $path) { $sheets[$a] = [System.Drawing.Bitmap]::FromFile((Resolve-Path $path)) }
}
$maxW = ($sheets.Values | ForEach-Object { $_.Width } | Measure-Object -Maximum).Maximum
$width = [Math]::Max($labelW + $maxW * $Scale + 10, 820)
$height = 40 + $rowH * $sheets.Count + 230
$width = [int]$width; $height = [int]$height
$img = New-Object System.Drawing.Bitmap $width, $height
$g = [System.Drawing.Graphics]::FromImage($img)
$g.InterpolationMode = "NearestNeighbor"; $g.PixelOffsetMode = "Half"
$g.Clear([System.Drawing.Color]::FromArgb(22, 26, 32))
$font = New-Object System.Drawing.Font "Malgun Gothic", 11, ([System.Drawing.FontStyle]::Bold)
$white = [System.Drawing.Brushes]::White
$g.DrawString("$Title  (동작별 시트, ${Scale}배 확대)", $font, $white, 8, 8)
$y = 36
$grid = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(60, 120, 130, 140)), 1
foreach ($a in $actions) {
    if (-not $sheets.ContainsKey($a)) { continue }
    $s = $sheets[$a]; $n = $s.Width / $cellW
    $g.DrawString("$a (${n}칸)", $font, $white, 8, $y + $cellH * $Scale / 2 - 10)
    $g.DrawImage($s, (New-Object System.Drawing.Rectangle $labelW, $y, ($s.Width * $Scale), ($cellH * $Scale)),
        (New-Object System.Drawing.Rectangle 0, 0, $s.Width, $cellH), [System.Drawing.GraphicsUnit]::Pixel)
    for ($i = 0; $i -le $n; $i++) { $g.DrawLine($grid, $labelW + $i * $cellW * $Scale, $y, $labelW + $i * $cellW * $Scale, $y + $cellH * $Scale) }
    $y += $rowH
}
# Game scale (2x so it is visible): street crop, current hero vs new idle frame on the same floor line.
$g.DrawString("게임 화면 비교 (2배): 왼쪽 지금 주인공, 오른쪽 새 캐릭터", $font, $white, 8, $y + 6)
$bg = [System.Drawing.Bitmap]::FromFile((Join-Path $root "assets\surface_side.png"))
$hero = [System.Drawing.Bitmap]::FromFile((Join-Path $root "assets\survivor_bat_walk_side.png"))
$top = $y + 32; $floor = $top + 180
$g.DrawImage($bg, (New-Object System.Drawing.Rectangle 8, $top, 400, 190), (New-Object System.Drawing.Rectangle 300, 290, 200, 95), [System.Drawing.GraphicsUnit]::Pixel)
$g.DrawImage($hero, (New-Object System.Drawing.Rectangle 70, ($floor - 116), 154, 116), (New-Object System.Drawing.Rectangle 0, 0, 77, 58), [System.Drawing.GraphicsUnit]::Pixel)
$first = if ($sheets.ContainsKey("idle")) { $sheets["idle"] } else { $sheets.Values | Select-Object -First 1 }
$g.DrawImage($first, (New-Object System.Drawing.Rectangle 210, ($floor - 120), 192, 128), (New-Object System.Drawing.Rectangle 0, 0, 96, 64), [System.Drawing.GraphicsUnit]::Pixel)
$g.Dispose(); $bg.Dispose(); $hero.Dispose(); foreach ($s in $sheets.Values) { $s.Dispose() }
New-Item -ItemType Directory -Force (Split-Path $Out) | Out-Null
$img.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png); $img.Dispose()
"saved $Out"
