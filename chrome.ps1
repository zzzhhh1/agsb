# 获取当前用户桌面路径
$DesktopPath = [Environment]::GetFolderPath("Desktop")

# 存放 Chrome 用户数据 - 修改为桌面的chrome文件夹
$UserDataPath = "$DesktopPath\chrome\Chrome_UserData"

# 存放快捷方式图标，从这个文件夹里打开浏览器分身 - 修改为桌面的chrome文件夹
$FilePath = "$DesktopPath\chrome\Chrome_ShortCuts"

# Chrome 浏览器的目标路径
$TargetPath = "C:\Program Files\Google\Chrome\Application\chrome.exe"

# 工作目录
$WorkingDirectory = "C:\Program Files\Google\Chrome\Application"

# 设置生成分身的数量（从1到10）
$array = 1..10

# 检查并创建chrome主目录（如果不存在）
$ChromeMainPath = "$DesktopPath\chrome"
if (-not (Test-Path $ChromeMainPath)) {
    New-Item -ItemType Directory -Path $ChromeMainPath -Force
    Write-Host "已创建目录: $ChromeMainPath"
}

# 检查并创建用户数据目录（如果不存在）
if (-not (Test-Path $UserDataPath)) {
    New-Item -ItemType Directory -Path $UserDataPath -Force
    Write-Host "已创建目录: $UserDataPath"
}

# 检查并创建快捷方式目录（如果不存在）
if (-not (Test-Path $FilePath)) {
    New-Item -ItemType Directory -Path $FilePath -Force
    Write-Host "已创建目录: $FilePath"
}

foreach ($n in $array)
{
    $x = $n.ToString()
    $ShortcutFile = "$FilePath\Chrome_$x.lnk"

    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)

    $Shortcut.TargetPath = $TargetPath
    $Shortcut.Arguments = "--user-data-dir=$UserDataPath\$x"
    $Shortcut.WorkingDirectory = $WorkingDirectory
    $Shortcut.Description = "Chrome Browser Profile $x" # 更具描述性的备注

    $Shortcut.Save()
    Write-Host "已创建快捷方式: Chrome_$x.lnk"
}

Write-Host "所有Chrome分身快捷方式创建完成！"
Write-Host "快捷方式位置: $FilePath"
Write-Host "用户数据位置: $UserDataPath"
