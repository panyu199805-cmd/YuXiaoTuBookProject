$dir = Join-Path $PSScriptRoot "..\src\static"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$png = [Convert]::FromBase64String("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcaaaEAAAABC4AAAA6CAAAAQAAAAGAAAAAQAAAAAAAAABAAAAAQ==")
@(
  "tab-home.png","tab-home-active.png",
  "tab-books.png","tab-books-active.png",
  "tab-daily.png","tab-daily-active.png",
  "tab-user.png","tab-user-active.png"
) | ForEach-Object {
  [IO.File]::WriteAllBytes((Join-Path $dir $_), $png)
}
