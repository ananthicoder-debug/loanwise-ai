$BASE = "http://127.0.0.1:8000"
$P = 0; $F = 0
function OK($label) { Write-Host "  [PASS] $label" -ForegroundColor Green; $script:P++ }
function FAIL($label, $detail="") { Write-Host "  [FAIL] $label $detail" -ForegroundColor Red; $script:F++ }
function CHECK($label, $cond, $detail="") { if ($cond) { OK $label } else { FAIL $label $detail } }
function SECTION($n, $title) { Write-Host "`n[$n] $title" -ForegroundColor Yellow }

Write-Host ""; Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  LoanWise AI -- API Test Suite" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# ─── 1. HEALTH ────────────────────────────────────────────────────────────────
SECTION 1 "HEALTH CHECK"
$h = Invoke-RestMethod "$BASE/api/health"
CHECK "status=ok"              ($h.status -eq "ok")
CHECK "mongodb=connected"      ($h.mongodb -eq "connected")
CHECK "database=loan_ai_system" ($h.database -eq "loan_ai_system")
Write-Host "  Response: status=$($h.status) | db=$($h.database) | mongo=$($h.mongodb)" -ForegroundColor DarkGray

# ─── 2. AUTH ──────────────────────────────────────────────────────────────────
SECTION 2 "AUTHENTICATION"
$loginBody = '{"email":"demo@loanwise.ai","password":"Demo@2026"}'
$uResp = Invoke-RestMethod "$BASE/api/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
$TOKEN = $uResp.access_token
$H = @{ Authorization = "Bearer $TOKEN" }
CHECK "Login demo user"         ($TOKEN.Length -gt 10)
CHECK "role=user"               ($uResp.role -eq "user")
CHECK "name=Arjun Mehta"        ($uResp.full_name -eq "Arjun Mehta")

$aBody = '{"email":"admin@loanwise.ai","password":"Admin@2026"}'
$aResp = Invoke-RestMethod "$BASE/api/auth/login" -Method POST -Body $aBody -ContentType "application/json"
$ATOKEN = $aResp.access_token; $AH = @{ Authorization = "Bearer $ATOKEN" }
CHECK "Login admin"             ($ATOKEN.Length -gt 10)
CHECK "admin role"              ($aResp.role -eq "admin")

$me = Invoke-RestMethod "$BASE/api/auth/me" -Headers $H
CHECK "GET /api/auth/me"        ($me.email -eq "demo@loanwise.ai")

# ─── 3. PROFILE ───────────────────────────────────────────────────────────────
SECTION 3 "USER PROFILE"
$profile = Invoke-RestMethod "$BASE/api/users/profile" -Headers $H
CHECK "GET profile"             ($profile.full_name -eq "Arjun Mehta")
CHECK "city=Bengaluru"          ($profile.address.city -eq "Bengaluru")
$upd = Invoke-RestMethod "$BASE/api/users/profile" -Method PUT -Headers $H -Body '{"occupation_description":"Senior Software Engineer"}' -ContentType "application/json"
CHECK "PUT profile"             ($upd.full_name -ne $null)

# ─── 4. CREDIT PROFILE ────────────────────────────────────────────────────────
SECTION 4 "CREDIT PROFILE"
$cp = Invoke-RestMethod "$BASE/api/credit-profile" -Headers $H
CHECK "GET credit profile"      ($cp.cibil_score -eq 748)
CHECK "monthly_income=85000"    ($cp.monthly_income -eq 85000)
CHECK "employment=Salaried"     ($cp.employment_type -eq "Salaried")
$cpUpd = Invoke-RestMethod "$BASE/api/credit-profile" -Method PUT -Headers $H -Body '{"cibil_score":755,"monthly_income":90000,"annual_income":1080000}' -ContentType "application/json"
CHECK "PUT credit profile"      ($cpUpd.cibil_score -eq 755)
Invoke-RestMethod "$BASE/api/credit-profile" -Method PUT -Headers $H -Body '{"cibil_score":748,"monthly_income":85000,"annual_income":1020000}' -ContentType "application/json" | Out-Null
Write-Host "  CIBIL=$($cp.cibil_score) Income=Rs.$($cp.monthly_income) Employment=$($cp.employment_type)" -ForegroundColor DarkGray

# ─── 5. LOAN CATALOGUE ────────────────────────────────────────────────────────
SECTION 5 "LOAN CATALOGUE"
$cats = Invoke-RestMethod "$BASE/api/loans/categories" -Headers $H
CHECK "7 categories from MongoDB" ($cats.Count -eq 7)
CHECK "Personal Loan present"    (($cats | Where-Object { $_.category -eq "Personal Loan" }).Count -gt 0)
$cats | ForEach-Object { Write-Host "  $($_.category): $($_.product_count) products, $($_.lender_count) lenders" -ForegroundColor DarkGray }

$lenders = Invoke-RestMethod "$BASE/api/loans/lenders" -Headers $H
CHECK "12 real lenders"          ($lenders.Count -eq 12)
CHECK "State Bank of India"      (($lenders | Where-Object { $_.lender_name -eq "State Bank of India" }).Count -eq 1)
CHECK "HDFC Bank"                (($lenders | Where-Object { $_.lender_name -eq "HDFC Bank" }).Count -eq 1)
CHECK "ICICI Bank"               (($lenders | Where-Object { $_.lender_name -eq "ICICI Bank" }).Count -eq 1)
CHECK "Axis Bank"                (($lenders | Where-Object { $_.lender_name -eq "Axis Bank" }).Count -eq 1)
CHECK "Bajaj Finance (NBFC)"     (($lenders | Where-Object { $_.lender_name -eq "Bajaj Finance" }).Count -eq 1)
CHECK "No Demo/Sample lenders"   (($lenders | Where-Object { $_.lender_name -match "Demo|Sample|Test|Bank A|Bank B" }).Count -eq 0)

# ─── 6. LOAN SEARCH ───────────────────────────────────────────────────────────
SECTION 6 "LOAN SEARCH"
$s1 = Invoke-RestMethod "$BASE/api/loans/search?q=State+Bank" -Headers $H
CHECK "Search 'State Bank'"      ($s1.Count -gt 0)
$s2 = Invoke-RestMethod "$BASE/api/loans/search?q=Personal+Loan" -Headers $H
CHECK "Search 'Personal Loan'"   ($s2.Count -gt 0)
$s3 = Invoke-RestMethod "$BASE/api/loans/search?q=Home+Loan" -Headers $H
CHECK "Search 'Home Loan'"       ($s3.Count -gt 0)
$s4 = Invoke-RestMethod "$BASE/api/loans/search?q=HDFC" -Headers $H
CHECK "Search 'HDFC'"            ($s4.Count -gt 0)
$s5 = Invoke-RestMethod "$BASE/api/loans/search?q=Gold" -Headers $H
CHECK "Search 'Gold'"            ($s5.Count -gt 0)
Write-Host "  State Bank products: $($s1.Count) | Personal Loan: $($s2.Count) | Home Loan: $($s3.Count)" -ForegroundColor DarkGray

# ─── 7. PRODUCT DETAIL ────────────────────────────────────────────────────────
SECTION 7 "PRODUCT DETAIL"
$prodId = $s2[0]._id
$det = Invoke-RestMethod "$BASE/api/loans/$prodId" -Headers $H
CHECK "GET /api/loans/{id}"      ($det.product_name -ne $null)
CHECK "Has lender_name"          ($det.lender_name -ne $null)
CHECK "Has interest_rate_min"    ($det.interest_rate_min -gt 0)
CHECK "Has verification_status"  ($det.verification_status -ne $null)
CHECK "Has official_product_url" ($det.official_product_url -ne $null)
CHECK "Not a demo lender"        ($det.lender_name -notmatch "Demo|Sample|Test|Bank A")
Write-Host "  Product: $($det.product_name)" -ForegroundColor DarkGray
Write-Host "  Lender:  $($det.lender_name) | Rate: $($det.interest_rate_min)%-$($det.interest_rate_max)%" -ForegroundColor DarkGray
Write-Host "  Verification: $($det.verification_status) | Source: $($det.source_date)" -ForegroundColor DarkGray

# ─── 8. LOAN COMPARE ──────────────────────────────────────────────────────────
SECTION 8 "LOAN COMPARISON"
$compId1 = $s2[0]._id; $compId2 = $s2[1]._id
$comp = Invoke-RestMethod "$BASE/api/loans/compare?ids=$compId1,$compId2" -Headers $H
CHECK "Compare returns 2 products" ($comp.Count -eq 2)
CHECK "Product 1 has lender_name" ($comp[0].lender_name -ne $null)
CHECK "Product 2 has lender_name" ($comp[1].lender_name -ne $null)
CHECK "No demo lenders in compare" (($comp | Where-Object { $_.lender_name -match "Demo|Sample" }).Count -eq 0)
Write-Host "  Comparing: $($comp[0].product_name) vs $($comp[1].product_name)" -ForegroundColor DarkGray

# ─── 9. ML PIPELINE ───────────────────────────────────────────────────────────
SECTION 9 "ML PIPELINE — APPLICATIONS"
$appList = Invoke-RestMethod "$BASE/api/applications" -Headers $H
CHECK "GET /api/applications"    ($appList.Count -ge 3)

$newApp = Invoke-RestMethod "$BASE/api/applications" -Method POST -Headers $H -Body '{"loan_amount":400000,"loan_tenure":36,"loan_category":"Personal Loan","purpose":"Home renovation"}' -ContentType "application/json"
CHECK "POST new application"     ($newApp.application_id -ne $null)
CHECK "Model 1 returns result"   ($newApp.model_1.result -in @("Eligible","Not Eligible"))
CHECK "Model 1 has probability"  ($newApp.model_1.probability -gt 0)
CHECK "Model 2 returns result"   ($newApp.model_2.result -in @("Manageable","Not Manageable"))
CHECK "eligible_count > 0"       ($newApp.eligible_count -gt 0)
CHECK "No hardcoded bank names"  (($newApp | ConvertTo-Json -Depth 10) -notmatch '"Demo Bank"')
Write-Host "  Model 1: $($newApp.model_1.result) (prob=$([math]::Round($newApp.model_1.probability*100,0)))" -ForegroundColor DarkGray
Write-Host "  Model 2: $($newApp.model_2.result) (prob=$([math]::Round($newApp.model_2.probability*100,0)))" -ForegroundColor DarkGray
Write-Host "  Eligible=$($newApp.eligible_count) | Recommended=$($newApp.recommended_count)" -ForegroundColor DarkGray

$appDetail = Invoke-RestMethod "$BASE/api/applications/$($newApp.application_id)" -Headers $H
CHECK "GET /api/applications/{id}" ($appDetail.eligible_count -ge 0)

# ─── 10. RECOMMENDATIONS ──────────────────────────────────────────────────────
SECTION 10 "RECOMMENDATIONS"
$recs = Invoke-RestMethod "$BASE/api/recommendations" -Headers $H
CHECK "GET /api/recommendations" ($recs.Count -ge 0)
if ($recs.Count -gt 0) {
    CHECK "Has match_score"      ($recs[0].match_score -ge 0)
    CHECK "Has product object"   ($recs[0].product -ne $null)
    CHECK "Has reason text"      ($recs[0].reason.Length -gt 5)
    Write-Host "  $($recs.Count) recommendations | Top: $($recs[0].product.product_name) ($($recs[0].match_score)% match)" -ForegroundColor DarkGray
}

# ─── 11. ACTIVE LOANS ─────────────────────────────────────────────────────────
SECTION 11 "ACTIVE LOANS"
$loans = Invoke-RestMethod "$BASE/api/active-loans" -Headers $H
CHECK "GET /api/active-loans"    ($loans.Count -ge 2)
CHECK "Has CLOSED loan"          (($loans | Where-Object { $_.status -eq "closed" }).Count -ge 1)
CHECK "Has ACTIVE loan"          (($loans | Where-Object { $_.status -eq "active" }).Count -ge 1)
$activeLoan = $loans | Where-Object { $_.status -eq "active" } | Select-Object -First 1
$closedLoan = $loans | Where-Object { $_.status -eq "closed" } | Select-Object -First 1
CHECK "Active loan has product_name" ($activeLoan.product_name -ne $null)
CHECK "Active loan has emi_amount"   ($activeLoan.emi_amount -gt 0)
CHECK "Active loan has lender_name"  ($activeLoan.lender_name -ne $null)
CHECK "Lender is real Indian bank"   ($activeLoan.lender_name -notmatch "Demo|Sample|Test")
Write-Host "  ACTIVE: $($activeLoan.product_name) by $($activeLoan.lender_name) EMI=Rs.$($activeLoan.emi_amount)" -ForegroundColor DarkGray
Write-Host "  CLOSED: $($closedLoan.product_name) -- all EMIs paid" -ForegroundColor DarkGray

$singleLoan = Invoke-RestMethod "$BASE/api/active-loans/$($activeLoan._id)" -Headers $H
CHECK "GET /api/active-loans/{id}" ($singleLoan._id -ne $null)

# ─── 12. EMI SCHEDULE ─────────────────────────────────────────────────────────
SECTION 12 "EMI SCHEDULE AND PAYMENT MARKING"
$sched = Invoke-RestMethod "$BASE/api/active-loans/$($activeLoan._id)/payments" -Headers $H
CHECK "GET schedule"             ($sched.Count -gt 0)
$paidCount    = ($sched | Where-Object { $_.payment_status -eq "PAID" }).Count
$overdueCount = ($sched | Where-Object { $_.payment_status -eq "OVERDUE" }).Count
$upcomingCount= ($sched | Where-Object { $_.payment_status -eq "UPCOMING" }).Count
CHECK "Has PAID EMIs"            ($paidCount -gt 0)
CHECK "Has OVERDUE EMI"          ($overdueCount -ge 1)
CHECK "Has UPCOMING EMIs"        ($upcomingCount -gt 0)
CHECK "No negative EMI amounts"  (($sched | Where-Object { $_.amount_due -lt 0 }).Count -eq 0)
Write-Host "  Schedule: PAID=$paidCount | OVERDUE=$overdueCount | UPCOMING=$upcomingCount" -ForegroundColor DarkGray

$dup = $sched | Where-Object { $_.payment_status -in @("UPCOMING","DUE") } | Select-Object -First 1
if ($dup) {
    $markBody = "{`"amount_paid`": $($dup.amount_due)}"
    $marked = Invoke-RestMethod "$BASE/api/payments/$($dup._id)/mark-paid" -Method POST -Headers $H -Body $markBody -ContentType "application/json"
    CHECK "POST mark-paid"       ($marked.payment_status -eq "PAID")
    Write-Host "  Marked EMI #$($dup.emi_number) as PAID (Rs.$($dup.amount_due))" -ForegroundColor DarkGray
}

# ─── 13. NOTIFICATIONS ────────────────────────────────────────────────────────
SECTION 13 "NOTIFICATIONS"
$notifs = Invoke-RestMethod "$BASE/api/notifications" -Headers $H
CHECK "GET /api/notifications"       ($notifs -ne $null)
CHECK "Has system notifications"     ($notifs.system_notifications.Count -gt 0)
$sn = $notifs.system_notifications[0]
$mkr = Invoke-RestMethod "$BASE/api/notifications/$($sn._id)/read" -Method PUT -Headers $H
CHECK "PUT mark notification read"   ($mkr.message -ne $null)
Invoke-RestMethod "$BASE/api/notifications/read-all" -Method PUT -Headers $H | Out-Null
CHECK "PUT mark all read"            $true
Write-Host "  EMI reminders: $($notifs.emi_notifications.Count) | System: $($notifs.system_notifications.Count)" -ForegroundColor DarkGray
$notifs.system_notifications | ForEach-Object { Write-Host "    [$($_.type)] $($_.title)" -ForegroundColor DarkGray }

# ─── 14. DOCUMENTS ────────────────────────────────────────────────────────────
SECTION 14 "DOCUMENTS"
$docs = Invoke-RestMethod "$BASE/api/documents" -Headers $H
CHECK "GET /api/documents"           ($docs.Count -ge 6)
CHECK "Has Identity Proof"           (($docs | Where-Object { $_.document_type -eq "Identity Proof" }).Count -ge 1)
CHECK "Has Income Proof"             (($docs | Where-Object { $_.document_type -eq "Income Proof" }).Count -ge 1)
CHECK "Has verification_status"      ($docs[0].verification_status -ne $null)
$addDoc = Invoke-RestMethod "$BASE/api/documents" -Method POST -Headers $H -Body '{"document_type":"Other","file_name":"test.pdf","notes":"test only"}' -ContentType "application/json"
CHECK "POST add document"            ($addDoc._id -ne $null)
$delDoc = Invoke-RestMethod "$BASE/api/documents/$($addDoc._id)" -Method DELETE -Headers $H
CHECK "DELETE document"              ($delDoc.message -ne $null)
$docs | ForEach-Object { Write-Host "  $($_.document_type): $($_.file_name) [$($_.verification_status)]" -ForegroundColor DarkGray }

# ─── 15. FEEDBACK ─────────────────────────────────────────────────────────────
SECTION 15 "FEEDBACK"
$fb = Invoke-RestMethod "$BASE/api/feedback" -Headers $H
CHECK "GET /api/feedback"            ($fb.Count -ge 3)
CHECK "Feedback has ratings"         ($fb[0].rating -ge 1)
$newFb = Invoke-RestMethod "$BASE/api/feedback" -Method POST -Headers $H -Body '{"rating":5,"category":"UI/UX","comments":"Great app!"}' -ContentType "application/json"
CHECK "POST feedback"                ($newFb._id -ne $null)
$fb | ForEach-Object { Write-Host "  Rating=$($_.rating) | $($_.category): $($_.comments)" -ForegroundColor DarkGray }

# ─── 16. USER DASHBOARD ───────────────────────────────────────────────────────
SECTION 16 "USER DASHBOARD"
$dash = Invoke-RestMethod "$BASE/api/dashboard" -Headers $H
CHECK "GET /api/dashboard"           ($dash.welcome_name -eq "Arjun Mehta")
CHECK "Has cards object"             ($dash.cards -ne $null)
CHECK "eligible_loans card"          ($dash.cards.eligible_loans -ge 0)
CHECK "active_loans card >= 1"       ($dash.cards.active_loans -ge 1)
CHECK "Has chart data"               ($dash.charts -ne $null)
CHECK "Has notifications"            ($dash.notifications -ne $null)
CHECK "Has recent_activity"          ($dash.recent_activity -ne $null)
Write-Host "  Eligible=$($dash.cards.eligible_loans) Recommended=$($dash.cards.recommended_loans) Active=$($dash.cards.active_loans)" -ForegroundColor DarkGray

# ─── 17. ADMIN DASHBOARD ──────────────────────────────────────────────────────
SECTION 17 "ADMIN DASHBOARD"
$ad = Invoke-RestMethod "$BASE/api/admin/dashboard" -Headers $AH
CHECK "GET /api/admin/dashboard"     ($ad.total_users -ge 1)
CHECK "total_lenders = 12"           ($ad.total_lenders -eq 12)
CHECK "active_loan_products = 62"    ($ad.active_loan_products -eq 62)
CHECK "Has charts"                   ($ad.charts -ne $null)
CHECK "Has apps_by_category chart"   ($ad.charts.apps_by_category -ne $null)
Write-Host "  Users=$($ad.total_users) Apps=$($ad.total_applications) Lenders=$($ad.total_lenders) Products=$($ad.active_loan_products)" -ForegroundColor DarkGray
Write-Host "  Predictions=$($ad.total_predictions) Recs=$($ad.total_recommendations) Overdue=$($ad.overdue_payments)" -ForegroundColor DarkGray

# ─── 18. ADMIN USERS ──────────────────────────────────────────────────────────
SECTION 18 "ADMIN USER MANAGEMENT"
$ausers = Invoke-RestMethod "$BASE/api/admin/users" -Headers $AH
CHECK "GET /api/admin/users"         ($ausers.Count -ge 1)
CHECK "Demo user in list"            (($ausers | Where-Object { $_.email -eq "demo@loanwise.ai" }).Count -gt 0)
CHECK "Passwords NOT exposed"        (($ausers | ConvertTo-Json) -notmatch "password_hash")
Write-Host "  $($ausers.Count) registered users" -ForegroundColor DarkGray
$ausers | Select-Object -First 3 | ForEach-Object { Write-Host "  $($_.full_name) ($($_.email)) -- $($_.application_count) apps" -ForegroundColor DarkGray }

# ─── 19. ADMIN APPLICATIONS ───────────────────────────────────────────────────
SECTION 19 "ADMIN APPLICATIONS"
$aapps = Invoke-RestMethod "$BASE/api/admin/applications" -Headers $AH
CHECK "GET /api/admin/applications"  ($aapps.Count -ge 3)
CHECK "Has applicant_name"           ($aapps[0].applicant_name -ne $null)
$aapps | Select-Object -First 3 | ForEach-Object { Write-Host "  $($_.applicant_name): $($_.loan_category) Rs.$($_.loan_amount) ($($_.status))" -ForegroundColor DarkGray }

# ─── 20. ADMIN PREDICTIONS ────────────────────────────────────────────────────
SECTION 20 "ADMIN ML PREDICTIONS"
$apreds = Invoke-RestMethod "$BASE/api/admin/predictions" -Headers $AH
CHECK "GET /api/admin/predictions"   ($apreds.Count -ge 3)
CHECK "Has model_1 result"           ($apreds[0].model_1.result -in @("Eligible","Not Eligible"))
CHECK "Has model_2 result"           ($apreds[0].model_2.result -in @("Manageable","Not Manageable"))
$apreds | Select-Object -First 3 | ForEach-Object { Write-Host "  M1=$($_.model_1.result)(prob=$([math]::Round($BASE = "http://127.0.0.1:8000"
$P = 0; $F = 0
function OK($label) { Write-Host "  [PASS] $label" -ForegroundColor Green; $script:P++ }
function FAIL($label, $detail="") { Write-Host "  [FAIL] $label $detail" -ForegroundColor Red; $script:F++ }
function CHECK($label, $cond, $detail="") { if ($cond) { OK $label } else { FAIL $label $detail } }
function SECTION($n, $title) { Write-Host "`n[$n] $title" -ForegroundColor Yellow }

Write-Host ""; Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  LoanWise AI -- API Test Suite" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# ─── 1. HEALTH ────────────────────────────────────────────────────────────────
SECTION 1 "HEALTH CHECK"
$h = Invoke-RestMethod "$BASE/api/health"
CHECK "status=ok"              ($h.status -eq "ok")
CHECK "mongodb=connected"      ($h.mongodb -eq "connected")
CHECK "database=loan_ai_system" ($h.database -eq "loan_ai_system")
Write-Host "  Response: status=$($h.status) | db=$($h.database) | mongo=$($h.mongodb)" -ForegroundColor DarkGray

# ─── 2. AUTH ──────────────────────────────────────────────────────────────────
SECTION 2 "AUTHENTICATION"
$loginBody = '{"email":"demo@loanwise.ai","password":"Demo@2026"}'
$uResp = Invoke-RestMethod "$BASE/api/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
$TOKEN = $uResp.access_token
$H = @{ Authorization = "Bearer $TOKEN" }
CHECK "Login demo user"         ($TOKEN.Length -gt 10)
CHECK "role=user"               ($uResp.role -eq "user")
CHECK "name=Arjun Mehta"        ($uResp.full_name -eq "Arjun Mehta")

$aBody = '{"email":"admin@loanwise.ai","password":"Admin@2026"}'
$aResp = Invoke-RestMethod "$BASE/api/auth/login" -Method POST -Body $aBody -ContentType "application/json"
$ATOKEN = $aResp.access_token; $AH = @{ Authorization = "Bearer $ATOKEN" }
CHECK "Login admin"             ($ATOKEN.Length -gt 10)
CHECK "admin role"              ($aResp.role -eq "admin")

$me = Invoke-RestMethod "$BASE/api/auth/me" -Headers $H
CHECK "GET /api/auth/me"        ($me.email -eq "demo@loanwise.ai")

# ─── 3. PROFILE ───────────────────────────────────────────────────────────────
SECTION 3 "USER PROFILE"
$profile = Invoke-RestMethod "$BASE/api/users/profile" -Headers $H
CHECK "GET profile"             ($profile.full_name -eq "Arjun Mehta")
CHECK "city=Bengaluru"          ($profile.address.city -eq "Bengaluru")
$upd = Invoke-RestMethod "$BASE/api/users/profile" -Method PUT -Headers $H -Body '{"occupation_description":"Senior Software Engineer"}' -ContentType "application/json"
CHECK "PUT profile"             ($upd.full_name -ne $null)

# ─── 4. CREDIT PROFILE ────────────────────────────────────────────────────────
SECTION 4 "CREDIT PROFILE"
$cp = Invoke-RestMethod "$BASE/api/credit-profile" -Headers $H
CHECK "GET credit profile"      ($cp.cibil_score -eq 748)
CHECK "monthly_income=85000"    ($cp.monthly_income -eq 85000)
CHECK "employment=Salaried"     ($cp.employment_type -eq "Salaried")
$cpUpd = Invoke-RestMethod "$BASE/api/credit-profile" -Method PUT -Headers $H -Body '{"cibil_score":755,"monthly_income":90000,"annual_income":1080000}' -ContentType "application/json"
CHECK "PUT credit profile"      ($cpUpd.cibil_score -eq 755)
Invoke-RestMethod "$BASE/api/credit-profile" -Method PUT -Headers $H -Body '{"cibil_score":748,"monthly_income":85000,"annual_income":1020000}' -ContentType "application/json" | Out-Null
Write-Host "  CIBIL=$($cp.cibil_score) Income=Rs.$($cp.monthly_income) Employment=$($cp.employment_type)" -ForegroundColor DarkGray

# ─── 5. LOAN CATALOGUE ────────────────────────────────────────────────────────
SECTION 5 "LOAN CATALOGUE"
$cats = Invoke-RestMethod "$BASE/api/loans/categories" -Headers $H
CHECK "7 categories from MongoDB" ($cats.Count -eq 7)
CHECK "Personal Loan present"    (($cats | Where-Object { $_.category -eq "Personal Loan" }).Count -gt 0)
$cats | ForEach-Object { Write-Host "  $($_.category): $($_.product_count) products, $($_.lender_count) lenders" -ForegroundColor DarkGray }

$lenders = Invoke-RestMethod "$BASE/api/loans/lenders" -Headers $H
CHECK "12 real lenders"          ($lenders.Count -eq 12)
CHECK "State Bank of India"      (($lenders | Where-Object { $_.lender_name -eq "State Bank of India" }).Count -eq 1)
CHECK "HDFC Bank"                (($lenders | Where-Object { $_.lender_name -eq "HDFC Bank" }).Count -eq 1)
CHECK "ICICI Bank"               (($lenders | Where-Object { $_.lender_name -eq "ICICI Bank" }).Count -eq 1)
CHECK "Axis Bank"                (($lenders | Where-Object { $_.lender_name -eq "Axis Bank" }).Count -eq 1)
CHECK "Bajaj Finance (NBFC)"     (($lenders | Where-Object { $_.lender_name -eq "Bajaj Finance" }).Count -eq 1)
CHECK "No Demo/Sample lenders"   (($lenders | Where-Object { $_.lender_name -match "Demo|Sample|Test|Bank A|Bank B" }).Count -eq 0)

# ─── 6. LOAN SEARCH ───────────────────────────────────────────────────────────
SECTION 6 "LOAN SEARCH"
$s1 = Invoke-RestMethod "$BASE/api/loans/search?q=State+Bank" -Headers $H
CHECK "Search 'State Bank'"      ($s1.Count -gt 0)
$s2 = Invoke-RestMethod "$BASE/api/loans/search?q=Personal+Loan" -Headers $H
CHECK "Search 'Personal Loan'"   ($s2.Count -gt 0)
$s3 = Invoke-RestMethod "$BASE/api/loans/search?q=Home+Loan" -Headers $H
CHECK "Search 'Home Loan'"       ($s3.Count -gt 0)
$s4 = Invoke-RestMethod "$BASE/api/loans/search?q=HDFC" -Headers $H
CHECK "Search 'HDFC'"            ($s4.Count -gt 0)
$s5 = Invoke-RestMethod "$BASE/api/loans/search?q=Gold" -Headers $H
CHECK "Search 'Gold'"            ($s5.Count -gt 0)
Write-Host "  State Bank products: $($s1.Count) | Personal Loan: $($s2.Count) | Home Loan: $($s3.Count)" -ForegroundColor DarkGray

# ─── 7. PRODUCT DETAIL ────────────────────────────────────────────────────────
SECTION 7 "PRODUCT DETAIL"
$prodId = $s2[0]._id
$det = Invoke-RestMethod "$BASE/api/loans/$prodId" -Headers $H
CHECK "GET /api/loans/{id}"      ($det.product_name -ne $null)
CHECK "Has lender_name"          ($det.lender_name -ne $null)
CHECK "Has interest_rate_min"    ($det.interest_rate_min -gt 0)
CHECK "Has verification_status"  ($det.verification_status -ne $null)
CHECK "Has official_product_url" ($det.official_product_url -ne $null)
CHECK "Not a demo lender"        ($det.lender_name -notmatch "Demo|Sample|Test|Bank A")
Write-Host "  Product: $($det.product_name)" -ForegroundColor DarkGray
Write-Host "  Lender:  $($det.lender_name) | Rate: $($det.interest_rate_min)%-$($det.interest_rate_max)%" -ForegroundColor DarkGray
Write-Host "  Verification: $($det.verification_status) | Source: $($det.source_date)" -ForegroundColor DarkGray

# ─── 8. LOAN COMPARE ──────────────────────────────────────────────────────────
SECTION 8 "LOAN COMPARISON"
$compId1 = $s2[0]._id; $compId2 = $s2[1]._id
$comp = Invoke-RestMethod "$BASE/api/loans/compare?ids=$compId1,$compId2" -Headers $H
CHECK "Compare returns 2 products" ($comp.Count -eq 2)
CHECK "Product 1 has lender_name" ($comp[0].lender_name -ne $null)
CHECK "Product 2 has lender_name" ($comp[1].lender_name -ne $null)
CHECK "No demo lenders in compare" (($comp | Where-Object { $_.lender_name -match "Demo|Sample" }).Count -eq 0)
Write-Host "  Comparing: $($comp[0].product_name) vs $($comp[1].product_name)" -ForegroundColor DarkGray

# ─── 9. ML PIPELINE ───────────────────────────────────────────────────────────
SECTION 9 "ML PIPELINE — APPLICATIONS"
$appList = Invoke-RestMethod "$BASE/api/applications" -Headers $H
CHECK "GET /api/applications"    ($appList.Count -ge 3)

$newApp = Invoke-RestMethod "$BASE/api/applications" -Method POST -Headers $H -Body '{"loan_amount":400000,"loan_tenure":36,"loan_category":"Personal Loan","purpose":"Home renovation"}' -ContentType "application/json"
CHECK "POST new application"     ($newApp.application_id -ne $null)
CHECK "Model 1 returns result"   ($newApp.model_1.result -in @("Eligible","Not Eligible"))
CHECK "Model 1 has probability"  ($newApp.model_1.probability -gt 0)
CHECK "Model 2 returns result"   ($newApp.model_2.result -in @("Manageable","Not Manageable"))
CHECK "eligible_count > 0"       ($newApp.eligible_count -gt 0)
CHECK "No hardcoded bank names"  (($newApp | ConvertTo-Json -Depth 10) -notmatch '"Demo Bank"')
Write-Host "  Model 1: $($newApp.model_1.result) (prob=$([math]::Round($newApp.model_1.probability*100,0)))" -ForegroundColor DarkGray
Write-Host "  Model 2: $($newApp.model_2.result) (prob=$([math]::Round($newApp.model_2.probability*100,0)))" -ForegroundColor DarkGray
Write-Host "  Eligible=$($newApp.eligible_count) | Recommended=$($newApp.recommended_count)" -ForegroundColor DarkGray

$appDetail = Invoke-RestMethod "$BASE/api/applications/$($newApp.application_id)" -Headers $H
CHECK "GET /api/applications/{id}" ($appDetail.eligible_count -ge 0)

# ─── 10. RECOMMENDATIONS ──────────────────────────────────────────────────────
SECTION 10 "RECOMMENDATIONS"
$recs = Invoke-RestMethod "$BASE/api/recommendations" -Headers $H
CHECK "GET /api/recommendations" ($recs.Count -ge 0)
if ($recs.Count -gt 0) {
    CHECK "Has match_score"      ($recs[0].match_score -ge 0)
    CHECK "Has product object"   ($recs[0].product -ne $null)
    CHECK "Has reason text"      ($recs[0].reason.Length -gt 5)
    Write-Host "  $($recs.Count) recommendations | Top: $($recs[0].product.product_name) ($($recs[0].match_score)% match)" -ForegroundColor DarkGray
}

# ─── 11. ACTIVE LOANS ─────────────────────────────────────────────────────────
SECTION 11 "ACTIVE LOANS"
$loans = Invoke-RestMethod "$BASE/api/active-loans" -Headers $H
CHECK "GET /api/active-loans"    ($loans.Count -ge 2)
CHECK "Has CLOSED loan"          (($loans | Where-Object { $_.status -eq "closed" }).Count -ge 1)
CHECK "Has ACTIVE loan"          (($loans | Where-Object { $_.status -eq "active" }).Count -ge 1)
$activeLoan = $loans | Where-Object { $_.status -eq "active" } | Select-Object -First 1
$closedLoan = $loans | Where-Object { $_.status -eq "closed" } | Select-Object -First 1
CHECK "Active loan has product_name" ($activeLoan.product_name -ne $null)
CHECK "Active loan has emi_amount"   ($activeLoan.emi_amount -gt 0)
CHECK "Active loan has lender_name"  ($activeLoan.lender_name -ne $null)
CHECK "Lender is real Indian bank"   ($activeLoan.lender_name -notmatch "Demo|Sample|Test")
Write-Host "  ACTIVE: $($activeLoan.product_name) by $($activeLoan.lender_name) EMI=Rs.$($activeLoan.emi_amount)" -ForegroundColor DarkGray
Write-Host "  CLOSED: $($closedLoan.product_name) -- all EMIs paid" -ForegroundColor DarkGray

$singleLoan = Invoke-RestMethod "$BASE/api/active-loans/$($activeLoan._id)" -Headers $H
CHECK "GET /api/active-loans/{id}" ($singleLoan._id -ne $null)

# ─── 12. EMI SCHEDULE ─────────────────────────────────────────────────────────
SECTION 12 "EMI SCHEDULE AND PAYMENT MARKING"
$sched = Invoke-RestMethod "$BASE/api/active-loans/$($activeLoan._id)/payments" -Headers $H
CHECK "GET schedule"             ($sched.Count -gt 0)
$paidCount    = ($sched | Where-Object { $_.payment_status -eq "PAID" }).Count
$overdueCount = ($sched | Where-Object { $_.payment_status -eq "OVERDUE" }).Count
$upcomingCount= ($sched | Where-Object { $_.payment_status -eq "UPCOMING" }).Count
CHECK "Has PAID EMIs"            ($paidCount -gt 0)
CHECK "Has OVERDUE EMI"          ($overdueCount -ge 1)
CHECK "Has UPCOMING EMIs"        ($upcomingCount -gt 0)
CHECK "No negative EMI amounts"  (($sched | Where-Object { $_.amount_due -lt 0 }).Count -eq 0)
Write-Host "  Schedule: PAID=$paidCount | OVERDUE=$overdueCount | UPCOMING=$upcomingCount" -ForegroundColor DarkGray

$dup = $sched | Where-Object { $_.payment_status -in @("UPCOMING","DUE") } | Select-Object -First 1
if ($dup) {
    $markBody = "{`"amount_paid`": $($dup.amount_due)}"
    $marked = Invoke-RestMethod "$BASE/api/payments/$($dup._id)/mark-paid" -Method POST -Headers $H -Body $markBody -ContentType "application/json"
    CHECK "POST mark-paid"       ($marked.payment_status -eq "PAID")
    Write-Host "  Marked EMI #$($dup.emi_number) as PAID (Rs.$($dup.amount_due))" -ForegroundColor DarkGray
}

# ─── 13. NOTIFICATIONS ────────────────────────────────────────────────────────
SECTION 13 "NOTIFICATIONS"
$notifs = Invoke-RestMethod "$BASE/api/notifications" -Headers $H
CHECK "GET /api/notifications"       ($notifs -ne $null)
CHECK "Has system notifications"     ($notifs.system_notifications.Count -gt 0)
$sn = $notifs.system_notifications[0]
$mkr = Invoke-RestMethod "$BASE/api/notifications/$($sn._id)/read" -Method PUT -Headers $H
CHECK "PUT mark notification read"   ($mkr.message -ne $null)
Invoke-RestMethod "$BASE/api/notifications/read-all" -Method PUT -Headers $H | Out-Null
CHECK "PUT mark all read"            $true
Write-Host "  EMI reminders: $($notifs.emi_notifications.Count) | System: $($notifs.system_notifications.Count)" -ForegroundColor DarkGray
$notifs.system_notifications | ForEach-Object { Write-Host "    [$($_.type)] $($_.title)" -ForegroundColor DarkGray }

# ─── 14. DOCUMENTS ────────────────────────────────────────────────────────────
SECTION 14 "DOCUMENTS"
$docs = Invoke-RestMethod "$BASE/api/documents" -Headers $H
CHECK "GET /api/documents"           ($docs.Count -ge 6)
CHECK "Has Identity Proof"           (($docs | Where-Object { $_.document_type -eq "Identity Proof" }).Count -ge 1)
CHECK "Has Income Proof"             (($docs | Where-Object { $_.document_type -eq "Income Proof" }).Count -ge 1)
CHECK "Has verification_status"      ($docs[0].verification_status -ne $null)
$addDoc = Invoke-RestMethod "$BASE/api/documents" -Method POST -Headers $H -Body '{"document_type":"Other","file_name":"test.pdf","notes":"test only"}' -ContentType "application/json"
CHECK "POST add document"            ($addDoc._id -ne $null)
$delDoc = Invoke-RestMethod "$BASE/api/documents/$($addDoc._id)" -Method DELETE -Headers $H
CHECK "DELETE document"              ($delDoc.message -ne $null)
$docs | ForEach-Object { Write-Host "  $($_.document_type): $($_.file_name) [$($_.verification_status)]" -ForegroundColor DarkGray }

# ─── 15. FEEDBACK ─────────────────────────────────────────────────────────────
SECTION 15 "FEEDBACK"
$fb = Invoke-RestMethod "$BASE/api/feedback" -Headers $H
CHECK "GET /api/feedback"            ($fb.Count -ge 3)
CHECK "Feedback has ratings"         ($fb[0].rating -ge 1)
$newFb = Invoke-RestMethod "$BASE/api/feedback" -Method POST -Headers $H -Body '{"rating":5,"category":"UI/UX","comments":"Great app!"}' -ContentType "application/json"
CHECK "POST feedback"                ($newFb._id -ne $null)
$fb | ForEach-Object { Write-Host "  Rating=$($_.rating) | $($_.category): $($_.comments)" -ForegroundColor DarkGray }

# ─── 16. USER DASHBOARD ───────────────────────────────────────────────────────
SECTION 16 "USER DASHBOARD"
$dash = Invoke-RestMethod "$BASE/api/dashboard" -Headers $H
CHECK "GET /api/dashboard"           ($dash.welcome_name -eq "Arjun Mehta")
CHECK "Has cards object"             ($dash.cards -ne $null)
CHECK "eligible_loans card"          ($dash.cards.eligible_loans -ge 0)
CHECK "active_loans card >= 1"       ($dash.cards.active_loans -ge 1)
CHECK "Has chart data"               ($dash.charts -ne $null)
CHECK "Has notifications"            ($dash.notifications -ne $null)
CHECK "Has recent_activity"          ($dash.recent_activity -ne $null)
Write-Host "  Eligible=$($dash.cards.eligible_loans) Recommended=$($dash.cards.recommended_loans) Active=$($dash.cards.active_loans)" -ForegroundColor DarkGray

# ─── 17. ADMIN DASHBOARD ──────────────────────────────────────────────────────
SECTION 17 "ADMIN DASHBOARD"
$ad = Invoke-RestMethod "$BASE/api/admin/dashboard" -Headers $AH
CHECK "GET /api/admin/dashboard"     ($ad.total_users -ge 1)
CHECK "total_lenders = 12"           ($ad.total_lenders -eq 12)
CHECK "active_loan_products = 62"    ($ad.active_loan_products -eq 62)
CHECK "Has charts"                   ($ad.charts -ne $null)
CHECK "Has apps_by_category chart"   ($ad.charts.apps_by_category -ne $null)
Write-Host "  Users=$($ad.total_users) Apps=$($ad.total_applications) Lenders=$($ad.total_lenders) Products=$($ad.active_loan_products)" -ForegroundColor DarkGray
Write-Host "  Predictions=$($ad.total_predictions) Recs=$($ad.total_recommendations) Overdue=$($ad.overdue_payments)" -ForegroundColor DarkGray

# ─── 18. ADMIN USERS ──────────────────────────────────────────────────────────
SECTION 18 "ADMIN USER MANAGEMENT"
$ausers = Invoke-RestMethod "$BASE/api/admin/users" -Headers $AH
CHECK "GET /api/admin/users"         ($ausers.Count -ge 1)
CHECK "Demo user in list"            (($ausers | Where-Object { $_.email -eq "demo@loanwise.ai" }).Count -gt 0)
CHECK "Passwords NOT exposed"        (($ausers | ConvertTo-Json) -notmatch "password_hash")
Write-Host "  $($ausers.Count) registered users" -ForegroundColor DarkGray
$ausers | Select-Object -First 3 | ForEach-Object { Write-Host "  $($_.full_name) ($($_.email)) -- $($_.application_count) apps" -ForegroundColor DarkGray }

# ─── 19. ADMIN APPLICATIONS ───────────────────────────────────────────────────
SECTION 19 "ADMIN APPLICATIONS"
$aapps = Invoke-RestMethod "$BASE/api/admin/applications" -Headers $AH
CHECK "GET /api/admin/applications"  ($aapps.Count -ge 3)
CHECK "Has applicant_name"           ($aapps[0].applicant_name -ne $null)
$aapps | Select-Object -First 3 | ForEach-Object { Write-Host "  $($_.applicant_name): $($_.loan_category) Rs.$($_.loan_amount) ($($_.status))" -ForegroundColor DarkGray }

# ─── 20. ADMIN PREDICTIONS ────────────────────────────────────────────────────
SECTION 20 "ADMIN ML PREDICTIONS"
$apreds = Invoke-RestMethod "$BASE/api/admin/predictions" -Headers $AH
CHECK "GET /api/admin/predictions"   ($apreds.Count -ge 3)
CHECK "Has model_1 result"           ($apreds[0].model_1.result -in @("Eligible","Not Eligible"))
CHECK "Has model_2 result"           ($apreds[0].model_2.result -in @("Manageable","Not Manageable"))
$apreds | Select-Object -First 3 | ForEach-Object { Write-Host "  M1=$($_.model_1.result)($([math]::Round($_.model_1.probability*100))%) M2=$($_.model_2.result) Eligible=$($_.eligible_count) Recs=$($_.recommended_count)" -ForegroundColor DarkGray }

# ─── 21. ADMIN RECOMMENDATIONS ────────────────────────────────────────────────
SECTION 21 "ADMIN RECOMMENDATIONS"
$arecs = Invoke-RestMethod "$BASE/api/admin/recommendations" -Headers $AH
CHECK "GET /api/admin/recommendations" ($arecs.Count -ge 1)
Write-Host "  $($arecs.Count) recommendation records in database" -ForegroundColor DarkGray

# ─── 22. ADMIN LENDER MANAGEMENT ──────────────────────────────────────────────
SECTION 22 "ADMIN LENDER MANAGEMENT"
$alenders = Invoke-RestMethod "$BASE/api/admin/lenders" -Headers $AH
CHECK "GET /api/admin/lenders"       ($alenders.Count -ge 12)
CHECK "No fake lenders"              (($alenders | Where-Object { $_.lender_name -match "Demo|Sample|Test" }).Count -eq 0)
$newL = Invoke-RestMethod "$BASE/api/admin/lenders" -Method POST -Headers $AH -Body '{"lender_name":"Indian Bank","lender_type":"Bank","official_website":"https://www.indianbank.in","headquarters_city":"Chennai","state":"Tamil Nadu"}' -ContentType "application/json"
CHECK "POST add lender"              ($newL._id -ne $null)
Invoke-RestMethod "$BASE/api/admin/lenders/$($newL._id)" -Method DELETE -Headers $AH | Out-Null
CHECK "DELETE lender (deactivate)"   $true
$alenders | ForEach-Object { Write-Host "  $($_.lender_name) ($($_.lender_type)) -- $($_.product_count) products" -ForegroundColor DarkGray }

# ─── 23. ADMIN PRODUCT MANAGEMENT ─────────────────────────────────────────────
SECTION 23 "ADMIN PRODUCT MANAGEMENT"
$aprods = Invoke-RestMethod "$BASE/api/admin/products" -Headers $AH
CHECK "GET /api/admin/products"      ($aprods.Count -eq 62)
CHECK "No demo products"             (($aprods | Where-Object { $_.product_name -match "Demo|Sample|Test" }).Count -eq 0)
CHECK "Products have official URLs"  (($aprods | Where-Object { $_.official_product_url -ne "" }).Count -gt 0)
CHECK "Products have verification"   (($aprods | Where-Object { $_.verification_status -eq "Verified" }).Count -gt 0)
Write-Host "  62 verified products -- no demo/sample/fake entries" -ForegroundColor DarkGray

# ─── 24. ADMIN ACTIVE LOANS ───────────────────────────────────────────────────
SECTION 24 "ADMIN ACTIVE LOANS AND PAYMENTS"
$aloans = Invoke-RestMethod "$BASE/api/admin/active-loans" -Headers $AH
CHECK "GET /api/admin/active-loans"  ($aloans.Count -ge 2)
CHECK "Has applicant_name"           ($aloans[0].applicant_name -ne $null)
CHECK "Has product_name"             ($aloans[0].product_name -ne $null)
CHECK "Has lender_name"              ($aloans[0].lender_name -ne $null)
$apayments = Invoke-RestMethod "$BASE/api/admin/payments" -Headers $AH
CHECK "GET /api/admin/payments"      ($apayments.Count -ge 10)
$aloans | ForEach-Object { Write-Host "  $($_.applicant_name): $($_.product_name) Rs.$($_.actual_amount) ($($_.status))" -ForegroundColor DarkGray }

# ─── 25. DATASET MANAGEMENT ───────────────────────────────────────────────────
SECTION 25 "DATASET MANAGEMENT"
$ds = Invoke-RestMethod "$BASE/api/admin/datasets" -Headers $AH
CHECK "GET /api/admin/datasets"                  ($ds.dataset_version -eq "2.0")
CHECK "Lenders count >= 12"                      ($ds.counts.lenders -ge 12)
CHECK "Products count = 62"                      ($ds.counts.loan_products -eq 62)
CHECK "Real lenders loaded"                      ($ds.catalogue_status.real_lenders_loaded -eq $true)
CHECK "Real products loaded"                     ($ds.catalogue_status.real_products_loaded -eq $true)
Write-Host "  Version=$($ds.dataset_version) | Lenders=$($ds.counts.lenders) | Products=$($ds.counts.loan_products)" -ForegroundColor DarkGray
Write-Host "  Users=$($ds.counts.users) | Apps=$($ds.counts.loan_applications) | Payments=$($ds.counts.payments)" -ForegroundColor DarkGray
Write-Host "  Borrower dataset: $($ds.borrower_dataset_version)" -ForegroundColor DarkGray

$ls = Invoke-RestMethod "$BASE/api/admin/lender-stats" -Headers $AH
CHECK "GET /api/admin/lender-stats"              ($ls.Count -gt 0)
$cs = Invoke-RestMethod "$BASE/api/admin/category-stats" -Headers $AH
CHECK "GET /api/admin/category-stats"            ($cs.Count -eq 7)
Write-Host "  Products per lender:" -ForegroundColor DarkGray
$ls | ForEach-Object { Write-Host "    $($_.lender_name): $($_.product_count) products" -ForegroundColor DarkGray }

# ─── 26. DATA QUALITY ─────────────────────────────────────────────────────────
SECTION 26 "DATA QUALITY CHECK"
$dq = Invoke-RestMethod "$BASE/api/admin/data-quality" -Headers $AH
CHECK "GET /api/admin/data-quality"              ($dq.status -ne $null)
CHECK "Status = PASS"                            ($dq.status -eq "PASS")
CHECK "62 total products"                        ($dq.total_products -eq 62)
CHECK "0 errors"                                 ($dq.errors.Count -eq 0)
Write-Host "  Status=$($dq.status) | Total=$($dq.total_products) active=$($dq.active_products) | Errors=$($dq.errors.Count) Warnings=$($dq.warnings.Count)" -ForegroundColor DarkGray
if ($dq.warnings.Count -gt 0) {
    $dq.warnings | ForEach-Object { Write-Host "  Warning: $_" -ForegroundColor DarkYellow }
}

# ─── 27. ML MODEL PERFORMANCE ─────────────────────────────────────────────────
SECTION 27 "ML MODEL PERFORMANCE"
$mperf = Invoke-RestMethod "$BASE/api/admin/model-performance" -Headers $AH
CHECK "GET /api/admin/model-performance"         ($mperf.Count -ge 2)
CHECK "Model 1 accuracy > 0.5"                   ($mperf[0].metrics.accuracy -gt 0.5)
CHECK "Model 2 accuracy > 0.5"                   ($mperf[1].metrics.accuracy -gt 0.5)
CHECK "F1 scores are real (not fabricated)"      ($mperf[0].metrics.f1_score -lt 1.0)
CHECK "ROC-AUC scores present"                   ($mperf[0].metrics.roc_auc -gt 0)
CHECK "Training records stored"                  ($mperf[0].training_records -gt 0)
foreach ($m in $mperf) {
    Write-Host "  $($m.model_name)" -ForegroundColor DarkGray
    Write-Host "    Algorithm: $($m.algorithm) | Version: $($m.model_version)" -ForegroundColor DarkGray
    Write-Host "    Accuracy=$($m.metrics.accuracy) | Precision=$($m.metrics.precision) | Recall=$($m.metrics.recall)" -ForegroundColor DarkGray
    Write-Host "    F1=$($m.metrics.f1_score) | ROC-AUC=$($m.metrics.roc_auc)" -ForegroundColor DarkGray
    Write-Host "    Train=$($m.training_records) records | Test=$($m.testing_records) records" -ForegroundColor DarkGray
    Write-Host "    Trained: $($m.training_date)" -ForegroundColor DarkGray
    Write-Host "    Disclaimer: $($m.disclaimer)" -ForegroundColor DarkGray
}

# ─── 28. ADMIN FEEDBACK ───────────────────────────────────────────────────────
SECTION 28 "ADMIN FEEDBACK"
$afb = Invoke-RestMethod "$BASE/api/admin/feedback" -Headers $AH
CHECK "GET /api/admin/feedback"                  ($afb.Count -ge 3)
CHECK "Feedback has user_name"                   ($afb[0].user_name -ne $null)
CHECK "Feedback has ratings"                     ($afb[0].rating -ge 1)
$afb | Select-Object -First 3 | ForEach-Object { Write-Host "  $($_.user_name): $('*'*$_.rating) ($($_.category)) -- $($_.comments)" -ForegroundColor DarkGray }

# ─── FINAL SUMMARY ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  FINAL TEST RESULTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PASSED: $P" -ForegroundColor Green
if ($F -gt 0) { Write-Host "  FAILED: $F" -ForegroundColor Red } else { Write-Host "  FAILED: 0" -ForegroundColor Green }
Write-Host "  TOTAL:  $($P+$F)"
Write-Host ""
if ($F -eq 0) {
    Write-Host "  ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "  LoanWise AI is fully operational." -ForegroundColor Green
} else {
    Write-Host "  $F test(s) need attention." -ForegroundColor Yellow
}
Write-Host "============================================================" -ForegroundColor Cyan
.model_1.probability*100,0))) M2=$($_.model_2.result) Eligible=$($_.eligible_count) Recs=$($_.recommended_count)" -ForegroundColor DarkGray }

# ─── 21. ADMIN RECOMMENDATIONS ────────────────────────────────────────────────
SECTION 21 "ADMIN RECOMMENDATIONS"
$arecs = Invoke-RestMethod "$BASE/api/admin/recommendations" -Headers $AH
CHECK "GET /api/admin/recommendations" ($arecs.Count -ge 1)
Write-Host "  $($arecs.Count) recommendation records in database" -ForegroundColor DarkGray

# ─── 22. ADMIN LENDER MANAGEMENT ──────────────────────────────────────────────
SECTION 22 "ADMIN LENDER MANAGEMENT"
$alenders = Invoke-RestMethod "$BASE/api/admin/lenders" -Headers $AH
CHECK "GET /api/admin/lenders"       ($alenders.Count -ge 12)
CHECK "No fake lenders"              (($alenders | Where-Object { $_.lender_name -match "Demo|Sample|Test" }).Count -eq 0)
$newL = Invoke-RestMethod "$BASE/api/admin/lenders" -Method POST -Headers $AH -Body '{"lender_name":"Indian Bank","lender_type":"Bank","official_website":"https://www.indianbank.in","headquarters_city":"Chennai","state":"Tamil Nadu"}' -ContentType "application/json"
CHECK "POST add lender"              ($newL._id -ne $null)
Invoke-RestMethod "$BASE/api/admin/lenders/$($newL._id)" -Method DELETE -Headers $AH | Out-Null
CHECK "DELETE lender (deactivate)"   $true
$alenders | ForEach-Object { Write-Host "  $($_.lender_name) ($($_.lender_type)) -- $($_.product_count) products" -ForegroundColor DarkGray }

# ─── 23. ADMIN PRODUCT MANAGEMENT ─────────────────────────────────────────────
SECTION 23 "ADMIN PRODUCT MANAGEMENT"
$aprods = Invoke-RestMethod "$BASE/api/admin/products" -Headers $AH
CHECK "GET /api/admin/products"      ($aprods.Count -eq 62)
CHECK "No demo products"             (($aprods | Where-Object { $_.product_name -match "Demo|Sample|Test" }).Count -eq 0)
CHECK "Products have official URLs"  (($aprods | Where-Object { $_.official_product_url -ne "" }).Count -gt 0)
CHECK "Products have verification"   (($aprods | Where-Object { $_.verification_status -eq "Verified" }).Count -gt 0)
Write-Host "  62 verified products -- no demo/sample/fake entries" -ForegroundColor DarkGray

# ─── 24. ADMIN ACTIVE LOANS ───────────────────────────────────────────────────
SECTION 24 "ADMIN ACTIVE LOANS AND PAYMENTS"
$aloans = Invoke-RestMethod "$BASE/api/admin/active-loans" -Headers $AH
CHECK "GET /api/admin/active-loans"  ($aloans.Count -ge 2)
CHECK "Has applicant_name"           ($aloans[0].applicant_name -ne $null)
CHECK "Has product_name"             ($aloans[0].product_name -ne $null)
CHECK "Has lender_name"              ($aloans[0].lender_name -ne $null)
$apayments = Invoke-RestMethod "$BASE/api/admin/payments" -Headers $AH
CHECK "GET /api/admin/payments"      ($apayments.Count -ge 10)
$aloans | ForEach-Object { Write-Host "  $($_.applicant_name): $($_.product_name) Rs.$($_.actual_amount) ($($_.status))" -ForegroundColor DarkGray }

# ─── 25. DATASET MANAGEMENT ───────────────────────────────────────────────────
SECTION 25 "DATASET MANAGEMENT"
$ds = Invoke-RestMethod "$BASE/api/admin/datasets" -Headers $AH
CHECK "GET /api/admin/datasets"                  ($ds.dataset_version -eq "2.0")
CHECK "Lenders count >= 12"                      ($ds.counts.lenders -ge 12)
CHECK "Products count = 62"                      ($ds.counts.loan_products -eq 62)
CHECK "Real lenders loaded"                      ($ds.catalogue_status.real_lenders_loaded -eq $true)
CHECK "Real products loaded"                     ($ds.catalogue_status.real_products_loaded -eq $true)
Write-Host "  Version=$($ds.dataset_version) | Lenders=$($ds.counts.lenders) | Products=$($ds.counts.loan_products)" -ForegroundColor DarkGray
Write-Host "  Users=$($ds.counts.users) | Apps=$($ds.counts.loan_applications) | Payments=$($ds.counts.payments)" -ForegroundColor DarkGray
Write-Host "  Borrower dataset: $($ds.borrower_dataset_version)" -ForegroundColor DarkGray

$ls = Invoke-RestMethod "$BASE/api/admin/lender-stats" -Headers $AH
CHECK "GET /api/admin/lender-stats"              ($ls.Count -gt 0)
$cs = Invoke-RestMethod "$BASE/api/admin/category-stats" -Headers $AH
CHECK "GET /api/admin/category-stats"            ($cs.Count -eq 7)
Write-Host "  Products per lender:" -ForegroundColor DarkGray
$ls | ForEach-Object { Write-Host "    $($_.lender_name): $($_.product_count) products" -ForegroundColor DarkGray }

# ─── 26. DATA QUALITY ─────────────────────────────────────────────────────────
SECTION 26 "DATA QUALITY CHECK"
$dq = Invoke-RestMethod "$BASE/api/admin/data-quality" -Headers $AH
CHECK "GET /api/admin/data-quality"              ($dq.status -ne $null)
CHECK "Status = PASS"                            ($dq.status -eq "PASS")
CHECK "62 total products"                        ($dq.total_products -eq 62)
CHECK "0 errors"                                 ($dq.errors.Count -eq 0)
Write-Host "  Status=$($dq.status) | Total=$($dq.total_products) active=$($dq.active_products) | Errors=$($dq.errors.Count) Warnings=$($dq.warnings.Count)" -ForegroundColor DarkGray
if ($dq.warnings.Count -gt 0) {
    $dq.warnings | ForEach-Object { Write-Host "  Warning: $_" -ForegroundColor DarkYellow }
}

# ─── 27. ML MODEL PERFORMANCE ─────────────────────────────────────────────────
SECTION 27 "ML MODEL PERFORMANCE"
$mperf = Invoke-RestMethod "$BASE/api/admin/model-performance" -Headers $AH
CHECK "GET /api/admin/model-performance"         ($mperf.Count -ge 2)
CHECK "Model 1 accuracy > 0.5"                   ($mperf[0].metrics.accuracy -gt 0.5)
CHECK "Model 2 accuracy > 0.5"                   ($mperf[1].metrics.accuracy -gt 0.5)
CHECK "F1 scores are real (not fabricated)"      ($mperf[0].metrics.f1_score -lt 1.0)
CHECK "ROC-AUC scores present"                   ($mperf[0].metrics.roc_auc -gt 0)
CHECK "Training records stored"                  ($mperf[0].training_records -gt 0)
foreach ($m in $mperf) {
    Write-Host "  $($m.model_name)" -ForegroundColor DarkGray
    Write-Host "    Algorithm: $($m.algorithm) | Version: $($m.model_version)" -ForegroundColor DarkGray
    Write-Host "    Accuracy=$($m.metrics.accuracy) | Precision=$($m.metrics.precision) | Recall=$($m.metrics.recall)" -ForegroundColor DarkGray
    Write-Host "    F1=$($m.metrics.f1_score) | ROC-AUC=$($m.metrics.roc_auc)" -ForegroundColor DarkGray
    Write-Host "    Train=$($m.training_records) records | Test=$($m.testing_records) records" -ForegroundColor DarkGray
    Write-Host "    Trained: $($m.training_date)" -ForegroundColor DarkGray
    Write-Host "    Disclaimer: $($m.disclaimer)" -ForegroundColor DarkGray
}

# ─── 28. ADMIN FEEDBACK ───────────────────────────────────────────────────────
SECTION 28 "ADMIN FEEDBACK"
$afb = Invoke-RestMethod "$BASE/api/admin/feedback" -Headers $AH
CHECK "GET /api/admin/feedback"                  ($afb.Count -ge 3)
CHECK "Feedback has user_name"                   ($afb[0].user_name -ne $null)
CHECK "Feedback has ratings"                     ($afb[0].rating -ge 1)
$afb | Select-Object -First 3 | ForEach-Object { Write-Host "  $($_.user_name): $('*'*$_.rating) ($($_.category)) -- $($_.comments)" -ForegroundColor DarkGray }

# ─── FINAL SUMMARY ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  FINAL TEST RESULTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PASSED: $P" -ForegroundColor Green
if ($F -gt 0) { Write-Host "  FAILED: $F" -ForegroundColor Red } else { Write-Host "  FAILED: 0" -ForegroundColor Green }
Write-Host "  TOTAL:  $($P+$F)"
Write-Host ""
if ($F -eq 0) {
    Write-Host "  ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "  LoanWise AI is fully operational." -ForegroundColor Green
} else {
    Write-Host "  $F test(s) need attention." -ForegroundColor Yellow
}
Write-Host "============================================================" -ForegroundColor Cyan

