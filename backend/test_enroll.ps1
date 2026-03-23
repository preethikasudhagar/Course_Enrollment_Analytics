$loginBody = "username=student%40test.com&password=password123"
$loginResp = Invoke-RestMethod -Uri "http://localhost:8000/login" -Method POST -ContentType "application/x-www-form-urlencoded" -Body $loginBody -SessionVariable session
$token = $loginResp.data.access_token
if (!$token) { $token = $loginResp.access_token }
if (!$token) { Write-Host "Checking response..."; $loginResp | ConvertTo-Json -Depth 5; exit }
Write-Host "Login OK, token: $($token.Substring(0,20))..."
$headers = @{Authorization="Bearer $token"}

# Course status BEFORE
$vitals = Invoke-RestMethod -Uri "http://localhost:8000/analytics/student-vitals" -Headers $headers
$se = $vitals.courses | Where-Object { $_.course_name -like "*Software Engineering*" } | Select-Object -First 1
Write-Host "SE BEFORE: enrolled=$($se.enrolled_students) limit=$($se.seat_limit)"

# Check if already enrolled
$myEnroll = Invoke-RestMethod -Uri "http://localhost:8000/enrollments/my" -Headers $headers
$alreadyIn = $myEnroll | Where-Object { $_.course_id -eq $se.id }
if ($alreadyIn) {
    Write-Host "Already enrolled - good, duplicate prevention works."
} else {
    Write-Host "Enrolling in Software Engineering (id=$($se.id))..."
    $enrollBody = "{`"course_id`": $($se.id)}"
    $r = Invoke-RestMethod -Uri "http://localhost:8000/enroll" -Method POST -ContentType "application/json" -Body $enrollBody -Headers $headers
    $r | ConvertTo-Json -Depth 4

    $vitals2 = Invoke-RestMethod -Uri "http://localhost:8000/analytics/student-vitals" -Headers $headers
    $se2 = $vitals2.courses | Where-Object { $_.course_name -like "*Software Engineering*" } | Select-Object -First 1
    Write-Host "SE AFTER: enrolled=$($se2.enrolled_students) limit=$($se2.seat_limit)"
    
    if ($se2.enrolled_students -gt $se.enrolled_students) { Write-Host "✅ enrolled_students increased correctly" }
    if ($se.enrolled_students -eq $se.seat_limit -and $se2.seat_limit -gt $se.seat_limit) { Write-Host "✅ Seat expanded!" }
}

$notifs = Invoke-RestMethod -Uri "http://localhost:8000/notifications/" -Headers $headers
Write-Host "Notifications: $($notifs.data.Count)"
if ($notifs.data[0]) { Write-Host "Latest: $($notifs.data[0].message) @ $($notifs.data[0].timestamp)" }
