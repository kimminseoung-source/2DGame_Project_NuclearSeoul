# Party line-up check (ART_FEEDBACK.md checklist): the characters side by side on the street
# at game size (1x), as black silhouettes (are they told apart by shape alone?), and enlarged.
# Usage: powershell -ExecutionPolicy Bypass -File tools/sprites/lineup.ps1 -Names hero,nurse,worker -Out assets/characters/previews/party_v1.png
param(
    [Parameter(Mandatory)] [string[]] $Names,
    [Parameter(Mandatory)] [string] $Out,
    [string] $Sheet = "idle",
    [int] $Frame = 0
)
Add-Type -AssemblyName System.Drawing
$Names = @($Names | ForEach-Object { $_ -split "," })   # -File passes "a,b,c" as one string
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$cw = 96; $ch = 64; $n = $Names.Count
$big = 3
$W = [int]([Math]::Max(60 + $n * $cw * $big, 820)); $H = [int](30 + 150 + 30 + $ch * 2 + 30 + $ch * $big + 40)
$img = New-Object System.Drawing.Bitmap $W, $H
$g = [System.Drawing.Graphics]::FromImage($img)
$g.InterpolationMode = "NearestNeighbor"; $g.PixelOffsetMode = "Half"
$g.Clear([System.Drawing.Color]::FromArgb(22, 26, 32))
$font = New-Object System.Drawing.Font "Malgun Gothic", 11, ([System.Drawing.FontStyle]::Bold)
$white = [System.Drawing.Brushes]::White
$sheets = foreach ($name in $Names) { [System.Drawing.Bitmap]::FromFile((Join-Path $root "assets\characters\$name\$Sheet.png")) }
$src = New-Object System.Drawing.Rectangle ($Frame * $cw), 0, $cw, $ch

# 1) Game size on the street (1x), next to the current hand-drawn hero.
$g.DrawString("1) 게임 크기(1배), 맨 왼쪽은 지금 주인공", $font, $white, [float]8, [float]6)
$bg = [System.Drawing.Bitmap]::FromFile((Join-Path $root "assets\surface_side.png"))
$g.DrawImage($bg, (New-Object System.Drawing.Rectangle 8, 30, 768, 150), (New-Object System.Drawing.Rectangle 0, 260, 768, 150), [System.Drawing.GraphicsUnit]::Pixel)
$floor = 30 + 120
$hero = [System.Drawing.Bitmap]::FromFile((Join-Path $root "assets\survivor_bat_walk_side.png"))
$g.DrawImage($hero, (New-Object System.Drawing.Rectangle 60, ($floor - 58), 77, 58), (New-Object System.Drawing.Rectangle 0, 58, 77, 58), [System.Drawing.GraphicsUnit]::Pixel)
for ($i = 0; $i -lt $n; $i++) {
    $g.DrawImage($sheets[$i], (New-Object System.Drawing.Rectangle (150 + $i * 80), ($floor - 60), $cw, $ch), $src, [System.Drawing.GraphicsUnit]::Pixel)
}

# 2) Silhouettes (2x): every solid pixel painted black on a light ground.
$y = 30 + 150 + 8
$g.DrawString("2) 실루엣(2배): 모양만으로 구분되는가", $font, $white, [float]8, [float]$y)
$y += 24
$g.FillRectangle((New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(200, 200, 195))), 8, $y, ($W - 16), ($ch * 2))
for ($i = 0; $i -lt $n; $i++) {
    $sil = New-Object System.Drawing.Bitmap $cw, $ch
    for ($py = 0; $py -lt $ch; $py++) { for ($px = 0; $px -lt $cw; $px++) {
        if ($sheets[$i].GetPixel($Frame * $cw + $px, $py).A -gt 0) { $sil.SetPixel($px, $py, [System.Drawing.Color]::Black) } } }
    $g.DrawImage($sil, (New-Object System.Drawing.Rectangle (20 + $i * $cw * 2), $y, ($cw * 2), ($ch * 2)))
    $sil.Dispose()
}

# 3) Enlarged (3x) with names.
$y += $ch * 2 + 8
$g.DrawString("3) 확대(3배)", $font, $white, [float]8, [float]$y)
$y += 24
for ($i = 0; $i -lt $n; $i++) {
    $g.DrawImage($sheets[$i], (New-Object System.Drawing.Rectangle (20 + $i * $cw * $big), $y, ($cw * $big), ($ch * $big)), $src, [System.Drawing.GraphicsUnit]::Pixel)
    $g.DrawString($Names[$i], $font, $white, [float](24 + $i * $cw * $big), [float]($y + $ch * $big + 2))
}
$g.Dispose(); $bg.Dispose(); $hero.Dispose(); foreach ($s in $sheets) { $s.Dispose() }
$img.Save((Join-Path $root $Out), [System.Drawing.Imaging.ImageFormat]::Png); $img.Dispose()
"saved $Out"
