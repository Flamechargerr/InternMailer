# PowerShell script to download all csrankings-[a-z].csv files from CSRankings GitHub gh-pages branch into the data directory

$letters = @()
for ($c = [byte][char]'a'; $c -le [byte][char]'z'; $c++) {
    $letters += [char]$c
}
$baseUrl = "https://raw.githubusercontent.com/emeryberger/CSRankings/gh-pages/csrankings-"
$ext = ".csv"

foreach ($letter in $letters) {
    $url = "$baseUrl$letter$ext"
    $outfile = "csrankings-$letter.csv"
    Write-Host "Downloading $url ..."
    Invoke-WebRequest -Uri $url -OutFile $outfile
}

Write-Host "All csrankings-[a-z].csv files downloaded to the data directory." 