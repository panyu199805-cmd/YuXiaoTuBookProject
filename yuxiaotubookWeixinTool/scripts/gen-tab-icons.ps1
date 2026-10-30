# 生成微信小程序 TabBar 个性化图标（81x81 PNG）
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$dir = Join-Path $PSScriptRoot "..\src\static"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$size = 81
$inactive = "#8A8A8A"
$active = "#5B9AA0"

function Save-TabIcon {
  param(
    [string]$Name,
    [string]$Color,
    [scriptblock]$Draw
  )
  $path = Join-Path $dir $Name
  $bmp = New-Object System.Drawing.Bitmap $size, $size
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $g.Clear([System.Drawing.Color]::FromArgb(0, 0, 0, 0))
  $pen = New-Object System.Drawing.Pen ([System.Drawing.ColorTranslator]::FromHtml($Color)), 3.6
  $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
  $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
  $pen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
  $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml($Color))
  & $Draw $g $pen $brush
  $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose()
  $bmp.Dispose()
  $pen.Dispose()
  $brush.Dispose()
  Write-Host "  $Name"
}

function Draw-Home {
  param($g, $pen, $brush)
  $pts = @(
    (New-Object System.Drawing.PointF 40.5, 18),
    (New-Object System.Drawing.PointF 62, 36),
    (New-Object System.Drawing.PointF 62, 58),
    (New-Object System.Drawing.PointF 19, 58),
    (New-Object System.Drawing.PointF 19, 36)
  )
  $g.DrawPolygon($pen, $pts)
  $g.DrawRectangle($pen, 30, 42, 21, 16)
}

function Draw-Books {
  param($g, $pen, $brush)
  $g.DrawRectangle($pen, 22, 20, 18, 42)
  $g.DrawLine($pen, 31, 20, 31, 62)
  $g.DrawRectangle($pen, 41, 20, 18, 42)
  $g.DrawLine($pen, 50, 20, 50, 62)
  $g.DrawLine($pen, 22, 28, 31, 28)
  $g.DrawLine($pen, 41, 28, 50, 28)
}

function Draw-Daily {
  param($g, $pen, $brush)
  $g.DrawRectangle($pen, 20, 22, 41, 38)
  $g.DrawLine($pen, 20, 32, 61, 32)
  $g.DrawLine($pen, 30, 18, 30, 26)
  $g.DrawLine($pen, 51, 18, 51, 26)
  $g.FillEllipse($brush, 36, 40, 6, 6)
  $g.DrawLine($pen, 28, 48, 53, 48)
  $g.DrawLine($pen, 28, 54, 45, 54)
}

function Draw-User {
  param($g, $pen, $brush)
  $g.DrawEllipse($pen, 28, 18, 25, 25)
  $path = New-Object System.Drawing.Drawing2D.GraphicsPath
  $path.AddArc(18, 44, 45, 28, 180, 180)
  $g.DrawPath($pen, $path)
  $path.Dispose()
}

Write-Host "Generating tab icons..." -ForegroundColor Cyan
foreach ($colorPair in @(
  @{ Suffix = ""; Color = $inactive },
  @{ Suffix = "-active"; Color = $active }
)) {
  $c = $colorPair.Color
  $s = $colorPair.Suffix
  Save-TabIcon "tab-home$s.png" $c ${function:Draw-Home}
  Save-TabIcon "tab-books$s.png" $c ${function:Draw-Books}
  Save-TabIcon "tab-daily$s.png" $c ${function:Draw-Daily}
  Save-TabIcon "tab-user$s.png" $c ${function:Draw-User}
}

Write-Host "Done -> $dir" -ForegroundColor Green
