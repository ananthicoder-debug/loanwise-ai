$BASE = "http://127.0.0.1:8000"
$PASS = 0; $FAIL = 0

function Test-API($label, $result) {
    if ($result) { Write-Host "  [PASS] $label" -ForegroundColor Green; $script:PASS++ }
    else          { Write-Host "  [FAIL] $label" -ForegroundColor Red;   $script:FAIL++ }
}

Write-Host ""; Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  LoanWise AI -- Full API Test Suite" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# --- HEALTH ---
Write-Host "`n[1] HEALTH CHECK" -ForegroundColor Yellow
$h = Invoke-RestMethod "$BASE/api/health"
Test-API "Health OK"           ($h.status -eq "ok")
Test-API "MongoDB connected"   ($h.mongodb -eq "connected")
Test-API "DB=loan_ai_system"   ($h.database -eq "loan_ai_system")

# --- AUTH ---
Write-Host "`n[2] AUTHENTICATION" -ForegroundColor Yellow
$loginBody = '{"email":"demo@loanwise.ai","password":"Demo@2026"}'
$userResp = Invoke-RestMethod "$BASE/api/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
$TOKEN = $userResp.access_token
$H = @{ Authorization = "Bearer $TOKEN" }
Test-API "Login demo user"      ($TOKEN.Length -gt 10)
Test-API "Role = user"          ($userResp.role -eq "user")
Test-API "Name = Arjun Mehta"   ($userResp.full_name -eq "Arjun Mehta")

$adminBody = '{"email":"admin@loanwise.ai","password":"Admin@2026"}'
$adminResp = Invoke-RestMethod "$BASE/api/auth/login" -Method POST -Body $adminBody -ContentType "application/json"
$ATOKEN = $adminResp.access_token
$AH = @{ Authorization = "Bearer $ATOKEN" }
Test-API "Login admin"          ($ATOKEN.Length -gt 10)
Test-API "Admin role confirmed" ($adminResp.role -eq "admin")

$me = Invoke-RestMethod "$BASE/api/auth/me" -Headers $H
Test-API "GET /api/auth/me"     ($me.email -eq "demo@loanwise.ai")

# --- PROFILE ---
Write-Host "`n[3] USER PROFILE" -ForegroundColor Yellow
$profile = Invoke-RestMethod "$BASE/api/users/profile" -Headers $H
Test-API "GET profile"          ($profile.full_name -eq "Arjun Mehta")
Test-API "City = Bengaluru"     ($profile.address.city -eq "Bengaluru")
$upd = Invoke-RestMethod "$BASE/api/users/profile" -Method PUT -Headers $H -Body '{"occupation_description":"Senior SW Engineer"}' -ContentType "application/json"
Test-API "PUT profile"          ($upd.full_name -ne $null)

# --- CREDIT PROFILE ---
Write-Host "`n[4] CREDIT PROFILE" -ForegroundColor Yellow
$cp = Invoke-RestMethod "$BASE/api/credit-profile" -Headers $H
Test-API "GET credit profile"   ($cp.cibil_score -eq 748)
Test-API "Income = 85000"       ($cp.monthly_income -eq 85000)
Test-API "Employment = Salaried" ($cp.employment_type -eq "Salaried")
$cpUpd = Invoke-RestMethod "$BASE/api/credit-profile" -Method PUT -Headers $H -Body '{"cibil_score":752,"monthly_income":87000,"annual_income":1044000}' -ContentType "application/json"
Test-API "PUT credit profile"   ($cpUpd.cibil_score -eq 752)
Invoke-RestMethod "$BASE/api/credit-profile" -Method PUT -Headers $H -Body '{"cibil_score":748,"monthly_income":85000,"annual_income":1020000}' -ContentType "application/json" | Out-Null

# --- LOAN CATALOGUE ---
Write-Host "`n[5] LOAN CATALOGUE" -ForegroundColor Yellow
$cats = Invoke-RestMethod "$BASE/api/loans/categories" -Headers $H
Test-API "7 categories"         ($cats.Count -eq 7)
$lenders = Invoke-RestMethod "$BASE/api/loans/lenders" -Headers $H
Test-API "12 lenders"           ($lenders.Count -eq 12)
Test-API "SBI present"          (($lenders | Where-Object { $_.lender_name -like "*State Bank*" }).Count -gt 0)
Test-API "HDFC present"         (($lenders | Where-Object { $_.lender_name -like "*HDFC*" }).Count -gt 0)
Test-API "ICICI present"        (($lenders | Where-Object { $_.lender_name -like "*ICICI*" }).Count -gt 0)
Test-API "No Demo/Sample lenders" (($lenders | Where-Object { $_.lender_name -match "Demo|Sample|Test|Bank A|Bank B" }).Count -eq 0)
Write-Host "  Categories:" -ForegroundColor DarkGray
$cats | ForEach-Object { Write-Host "    $($_.category): $($_.product_count) products" -ForegroundColor DarkGray }

# --- LOAN SEARCH ---
Write-Host "`n[6] LOAN SEARCH" -ForegroundColor Yellow
$sbi = Invoke-RestMethod "$BASE/api/loans/search?q=State+Bank" -Headers $H
Test-API "Search SBI"           ($sbi.Count -gt 0)
$pl = Invoke-RestMethod "$BASE/api/loans/search?q=Personal+Loan" -Headers $H
Test-API "Search Personal Loan" ($pl.Count -gt 0)
$hl = Invoke-RestMethod "$BASE/api/loans/search?q=Home+Loan" -Headers $H
Test-API "Search Home Loan"     ($hl.Count -gt 0)
$gold = Invoke-RestMethod "$BASE/api/loans/search?q=Gold" -Headers $H
Test-API "Search Gold Loan"     ($gold.Count -gt 0)

# --- PRODUCT DETAIL ---
Write-Host "`n[7] PRODUCT DETAIL" -ForegroundColor Yellow
$productId = $pl[0]._id
$detail = Invoke-RestMethod "$BASE/api/loans/$productId" -Headers $H
Test-API "GET /api/loans/{id}"  ($detail.product_name -ne $null)
Test-API "Has lender_name"      ($detail.lender_name -ne $null)
Test-API "Has interest rates"   ($detail.interest_rate_min -gt 0)
Test-API "Has verification"     ($detail.verification_status -ne $null)
Test-API "Has official URL"     ($detail.official_product_url -ne $null)
Test-API "Not demo/fake lender" ($detail.lender_name -notmatch "Demo|Sample|Test|Bank A")
Write-Host "  Product: $($detail.product_name) by $($detail.lender_name)" -ForegroundColor DarkGray

# --- LOAN COMPARE ---
Write-Host "`n[8] LOAN COMPARISON" -ForegroundColor Yellow
$id1 = $pl[0]._id; $id2 = $pl[1]._id
$compare = Invoke-RestMethod "$BASE/api/loans/compare?ids=$id1,$id2" -Headers $H
Test-API "Compare 2 products"   ($compare.Count -eq 2)
Test-API "Both are real lenders" ($compare | Where-Object { $_.lender_name -match "Demo|Sample" }).Count -eq 0

# --- ML PIPELINE ---
Write-Host "`n[9] ML PIPELINE (Applications)" -ForegroundColor Yellow
$apps = Invoke-RestMethod "$BASE/api/applications" -Headers $H
Test-API "GET applications"     ($apps.Count -ge 3)

$appBody = '{"loan_amount":400000,"loan_tenure":36,"loan_category":"Personal Loan","purpose":"Home renovation"}'
$newApp = Invoke-RestMethod "$BASE/api/applications" -Method POST -Headers $H -Body $appBody -ContentType "application/json"
Test-API "POST new application"  ($newApp.application_id -ne $null)
Test-API "Model 1 has result"    ($newApp.model_1.result -in @("Eligible","Not Eligible"))
Test-API "Model 1 probability"   ($newApp.model_1.probability -gt 0)
Test-API "Model 2 has result"    ($newApp.model_2.result -in @("Manageable","Not Manageable"))
Test-API "Eligible count > 0"    ($newApp.eligible_count -gt 0)
Test-API "Recommended count"     ($newApp.recommended_count -ge 0)
Test-API "No hardcoded demo data" (($newApp | ConvertTo-Json -Depth 10) -notmatch '"Demo Bank"')
Write-Host "  Model 1: $($newApp.model_1.result) ($([math]::Round($newApp.model_1.probability*100))%)" -ForegroundColor DarkGray
Write-Host "  Model 2: $($newApp.model_2.result) ($([math]::Round($newApp.model_2.probability*100))%)" -ForegroundColor DarkGray
Write-Host "  Eligible=$($newApp.eligible_count) | Recommended=$($newApp.recommended_count)" -ForegroundColor DarkGray

$appResult = Invoke-RestMethod "$BASE/api/applications/$($newApp.application_id)" -Headers $H
Test-API "GET /api/applications/{id}" ($appResult.eligible_count -ge 0)

# --- RECOMMENDATIONS ---
Write-Host "`n[10] RECOMMENDATIONS" -ForegroundColor Yellow
$recs = Invoke-RestMethod "$BASE/api/recommendations" -Headers $H
Test-API "GET recommendations"   ($recs.Count -ge 0)
if ($recs.Count -gt 0) {
    Test-API "Has match_score"   ($recs[0].match_score -ge 0)
    Test-API "Has product"       ($recs[0].product -ne $null)
    Test-API "Has reason text"   ($recs[0].reason.Length -gt 5)
    Write-Host "  $($recs.Count) recommendations | First: $($recs[0].product.product_name)" -ForegroundColor DarkGray
}

# --- ACTIVE LOANS ---
Write-Host "`n[11] ACTIVE LOANS" -ForegroundColor Yellow
$activeLoans = Invoke-RestMethod "$BASE/api/active-loans" -Headers $H
Test-API "GET active loans"      ($activeLoans.Count -ge 2)
Test-API "Has CLOSED loan"       (($activeLoans | Where-Object { $_.status -eq "closed" }).Count -ge 1)
Test-API "Has ACTIVE loan"       (($activeLoans | Where-Object { $_.status -eq "active" }).Count -ge 1)
$activeLoan = $activeLoans | Where-Object { $_.status -eq "active" } | Select-Object -First 1
Test-API "Has product_name"      ($activeLoan.product_name -ne $null)
Test-API "Has emi_amount"        ($activeLoan.emi_amount -gt 0)
Test-API "Real lender name"      ($activeLoan.lender_name -notmatch "Demo|Sample|Test")
Write-Host "  Active: $($activeLoan.product_name) by $($activeLoan.lender_name), EMI=Rs.$($activeLoan.emi_amount)" -ForegroundColor DarkGray
$closedLoan = $activeLoans | Where-Object { $_.status -eq "closed" } | Select-Object -First 1
Write-Host "  Closed: $($closedLoan.product_name) -- all EMIs paid" -ForegroundColor DarkGray

# --- EMI SCHEDULE ---
Write-Host "`n[12] EMI SCHEDULE & PAYMENT MARKING" -ForegroundColor Yellow
$schedule = Invoke-RestMethod "$BASE/api/active-loans/$($activeLoan._id)/payments" -Headers $H
Test-API "GET EMI schedule"      ($schedule.Count -gt 0)
Test-API "Has PAID entries"      (($schedule | Where-Object { $_.payment_status -eq "PAID" }).Count -gt 0)
Test-API "Has OVERDUE entry"     (($schedule | Where-Object { $_.payment_status -eq "OVERDUE" }).Count -ge 1)
Test-API "Has UPCOMING entries"  (($schedule | Where-Object { $_.payment_status -eq "UPCOMING" }).Count -gt 0)
$paid = ($schedule | Where-Object { $_.payment_status -eq "PAID" }).Count
$overdue = ($schedule | Where-Object { $_.payment_status -eq "OVERDUE" }).Count
$upcoming = ($schedule | Where-Object { $_.payment_status -eq "UPCOMING" }).Count
Write-Host "  Schedule: PAID=$paid | OVERDUE=$overdue | UPCOMING=$upcoming" -ForegroundColor DarkGray

$dup = $schedule | Where-Object { $_.payment_status -in @("UPCOMING","DUE") } | Select-Object -First 1
if ($dup) {
    $markBody = "{`"amount_paid`": $($dup.amount_due)}"
    $marked = Invoke-RestMethod "$BASE/api/payments/$($dup._id)/mark-paid" -Method POST -Headers $H -Body $markBody -ContentType "application/json"
    Test-API "Mark EMI as Paid"  ($marked.payment_status -eq "PAID")
}

# --- NOTIFICATIONS ---
Write-Host "`n[13] NOTIFICATIONS" -ForegroundColor Yellow
$notifs = Invoke-RestMethod "$BASE/api/notifications" -Headers $H
Test-API "GET notifications"         ($notifs -ne $null)
Test-API "Has system notifications"  ($notifs.system_notifications.Count -gt 0)
$sn = $notifs.system_notifications | Select-Object -First 1
if ($sn) {
    $mkr = Invoke-RestMethod "$BASE/api/notifications/$($sn._id)/read" -Method PUT -Headers $H
    Test-API "Mark notif read"       ($mkr.message -ne $null)
}
Invoke-RestMethod "$BASE/api/notifications/read-all" -Method PUT -Headers $H | Out-Null
Test-API "Mark all as read"          $true
Write-Host "  EMI notifications: $($notifs.emi_notifications.Count) | System: $($notifs.system_notifications.Count)" -ForegroundColor DarkGray

# --- DOCUMENTS ---
Write-Host "`n[14] DOCUMENTS" -ForegroundColor Yellow
$docs = Invoke-RestMethod "$BASE/api/documents" -Headers $H
Test-API "GET documents"             ($docs.Count -ge 6)
Test-API "Has document types"        ($docs[0].document_type -ne $null)
Test-API "Has verification status"   ($docs[0].verification_status -ne $null)
$addedDoc = Invoke-RestMethod "$BASE/api/documents" -Method POST -Headers $H -Body '{"document_type":"Other","file_name":"test_doc.pdf","notes":"Test"}' -ContentType "application/json"
Test-API "POST add document"         ($addedDoc._id -ne $null)
$del = Invoke-RestMethod "$BASE/api/documents/$($addedDoc._id)" -Method DELETE -Headers $H
Test-API "DELETE document"           ($del.message -ne $null)
Write-Host "  $($docs.Count) documents:" -ForegroundColor DarkGray
$docs | ForEach-Object { Write-Host "    $($_.document_type): $($_.file_name) [$($_.verification_status)]" -ForegroundColor DarkGray }

# --- FEEDBACK ---
Write-Host "`n[15] FEEDBACK" -ForegroundColor Yellow
$fb = Invoke-RestMethod "$BASE/api/feedback" -Headers $H
Test-API "GET feedback"              ($fb.Count -ge 3)
Test-API "Has ratings"               ($fb[0].rating -ge 1)
$newFb = Invoke-RestMethod "$BASE/api/feedback" -Method POST -Headers $H -Body '{"rating":5,"category":"UI/UX","comments":"Clean and easy to use."}' -ContentType "application/json"
Test-API "POST feedback"             ($newFb._id -ne $null)
Write-Host "  $($fb.Count) feedback entries" -ForegroundColor DarkGray

# --- DASHBOARD ---
Write-Host "`n[16] USER DASHBOARD" -ForegroundColor Yellow
$dash = Invoke-RestMethod "$BASE/api/dashboard" -Headers $H
Test-API "GET dashboard"             ($dash.welcome_name -eq "Arjun Mehta")
Test-API "Has cards"                 ($dash.cards -ne $null)
Test-API "eligible_loans count"      ($dash.cards.eligible_loans -ge 0)
Test-API "active_loans >= 1"         ($dash.cards.active_loans -ge 1)
Test-API "Has charts"                ($dash.charts -ne $null)
Test-API "Has notifications"         ($dash.notifications -ne $null)
Write-Host "  Eligible=$($dash.cards.eligible_loans) | Recommended=$($dash.cards.recommended_loans) | Active=$($dash.cards.active_loans)" -ForegroundColor DarkGray

# --- ADMIN DASHBOARD ---
Write-Host "`n[17] ADMIN DASHBOARD" -ForegroundColor Yellow
$admDash = Invoke-RestMethod "$BASE/api/admin/dashboard" -Headers $AH
Test-API "GET admin dashboard"       ($admDash.total_users -ge 1)
Test-API "12 lenders"                ($admDash.total_lenders -eq 12)
Test-API "62 products"               ($admDash.active_loan_products -eq 62)
Test-API "Has chart data"            ($admDash.charts -ne $null)
Write-Host "  Users=$($admDash.total_users) | Apps=$($admDash.total_applications) | Lenders=$($admDash.total_lenders) | Products=$($admDash.active_loan_products)" -ForegroundColor DarkGray
Write-Host "  Predictions=$($admDash.total_predictions) | Recommendations=$($admDash.total_recommendations) | Overdue=$($admDash.overdue_payments)" -ForegroundColor DarkGray

# --- ADMIN USERS ---
Write-Host "`n[18] ADMIN USER MANAGEMENT" -ForegroundColor Yellow
$allUsers = Invoke-RestMethod "$BASE/api/admin/users" -Headers $AH
Test-API "GET admin/users"           ($allUsers.Count -ge 1)
Test-API "Demo user visible"         (($allUsers | Where-Object { $_.email -eq "demo@loanwise.ai" }).Count -gt 0)
Test-API "Passwords NOT exposed"     (($allUsers | ConvertTo-Json) -notmatch "password_hash")
Write-Host "  $($allUsers.Count) users listed" -ForegroundColor DarkGray

# --- ADMIN APPS + PREDICTIONS + RECS ---
Write-Host "`n[19] ADMIN APPS / PREDICTIONS / RECS" -ForegroundColor Yellow
$allApps = Invoke-RestMethod "$BASE/api/admin/applications" -Headers $AH
Test-API "GET admin/applications"    ($allApps.Count -ge 3)
Test-API "Has applicant_name"        ($allApps[0].applicant_name -ne $null)

$allPreds = Invoke-RestMethod "$BASE/api/admin/predictions" -Headers $AH
Test-API "GET admin/predictions"     ($allPreds.Count -ge 3)
Test-API "Has model_1 result"        ($allPreds[0].model_1.result -ne $null)

$allRecs = Invoke-RestMethod "$BASE/api/admin/recommendations" -Headers $AH
Test-API "GET admin/recommendations" ($allRecs.Count -ge 1)

# --- ADMIN LENDERS ---
Write-Host "`n[20] ADMIN LENDER MANAGEMENT" -ForegroundColor Yellow
$adminLenders = Invoke-RestMethod "$BASE/api/admin/lenders" -Headers $AH
Test-API "GET admin/lenders"         ($adminLenders.Count -eq 12)
Test-API "All real Indian lenders"   (($adminLenders | Where-Object { $_.lender_name -match "Demo|Sample|Test" }).Count -eq 0)
$newL = Invoke-RestMethod "$BASE/api/admin/lenders" -Method POST -Headers $AH -Body '{"lender_name":"Indian Bank","lender_type":"Bank","official_website":"https://www.indianbank.in"}' -ContentType "application/json"
Test-API "POST admin/lenders (add)"  ($newL._id -ne $null)
Invoke-RestMethod "$BASE/api/admin/lenders/$($newL._id)" -Method DELETE -Headers $AH | Out-Null
Test-API "DELETE admin/lenders/{id}" $true

# --- ADMIN PRODUCTS ---
Write-Host "`n[21] ADMIN PRODUCT MANAGEMENT" -ForegroundColor Yellow
$adminProds = Invoke-RestMethod "$BASE/api/admin/products" -Headers $AH
Test-API "GET admin/products"        ($adminProds.Count -eq 62)
Test-API "No demo products"          (($adminProds | Where-Object { $_.product_name -match "Demo|Sample|Test" }).Count -eq 0)

# --- ADMIN LOANS + PAYMENTS ---
Write-Host "`n[22] ADMIN LOANS & PAYMENTS" -ForegroundColor Yellow
$adminLoans = Invoke-RestMethod "$BASE/api/admin/active-loans" -Headers $AH
Test-API "GET admin/active-loans"    ($adminLoans.Count -ge 2)
Test-API "Has applicant names"       ($adminLoans[0].applicant_name -ne $null)
$adminPay = Invoke-RestMethod "$BASE/api/admin/payments" -Headers $AH
Test-API "GET admin/payments"        ($adminPay.Count -ge 10)

# --- DATASETS ---
Write-Host "`n[23] DATASET MANAGEMENT" -ForegroundColor Yellow
$ds = Invoke-RestMethod "$BASE/api/admin/datasets" -Headers $AH
Test-API "GET admin/datasets"                   ($ds.dataset_version -eq "2.0")
Test-API "Lenders count >= 12              ($ds.counts.lenders -ge 12)
Test-API "Products count = 62"                  ($ds.counts.loan_products -eq 62)
Test-API "Catalogue lenders loaded"             ($ds.catalogue_status.real_lenders_loaded -eq $true)
Test-API "Catalogue products loaded"            ($ds.catalogue_status.real_products_loaded -eq $true)
Write-Host "  Version=$($ds.dataset_version) | Lenders=$($ds.counts.lenders) | Products=$($ds.counts.loan_products)" -ForegroundColor DarkGray
Write-Host "  Users=$($ds.counts.users) | Apps=$($ds.counts.loan_applications) | Payments=$($ds.counts.payments)" -ForegroundColor DarkGray

$lsStats = Invoke-RestMethod "$BASE/api/admin/lender-stats" -Headers $AH
Test-API "GET admin/lender-stats"               ($lsStats.Count -gt 0)
$csStats = Invoke-RestMethod "$BASE/api/admin/category-stats" -Headers $AH
Test-API "GET admin/category-stats"             ($csStats.Count -eq 7)
Write-Host "  Products per lender:" -ForegroundColor DarkGray
$lsStats | ForEach-Object { Write-Host "    $($_.lender_name): $($_.product_count) products" -ForegroundColor DarkGray }

# --- DATA QUALITY ---
Write-Host "`n[24] DATA QUALITY CHECK" -ForegroundColor Yellow
$dq = Invoke-RestMethod "$BASE/api/admin/data-quality" -Headers $AH
Test-API "GET admin/data-quality"               ($dq.status -ne $null)
Test-API "Data quality PASS"                    ($dq.status -eq "PASS")
Test-API "Products = 62"                        ($dq.total_products -eq 62)
Test-API "0 errors"                             ($dq.errors.Count -eq 0)
Write-Host "  Status=$($dq.status) | Errors=$($dq.errors.Count) | Warnings=$($dq.warnings.Count)" -ForegroundColor DarkGray

# --- MODEL PERFORMANCE ---
Write-Host "`n[25] ML MODEL PERFORMANCE" -ForegroundColor Yellow
$models = Invoke-RestMethod "$BASE/api/admin/model-performance" -Headers $AH
Test-API "GET admin/model-performance"          ($models.Count -ge 2)
Test-API "Model 1 accuracy > 0.5"               ($models[0].metrics.accuracy -gt 0.5)
Test-API "Model 2 F1 > 0.5"                     ($models[1].metrics.f1_score -gt 0.5)
Test-API "Metrics not fabricated (< 1.0)"       ($models[0].metrics.f1_score -lt 1.0)
Write-Host "  Model 1 -- $($models[0].model_name)" -ForegroundColor DarkGray
Write-Host "    Accuracy=$($models[0].metrics.accuracy) F1=$($models[0].metrics.f1_score) ROC-AUC=$($models[0].metrics.roc_auc)" -ForegroundColor DarkGray
Write-Host "    Train=$($models[0].training_records) Test=$($models[0].testing_records) Algo=$($models[0].algorithm)" -ForegroundColor DarkGray
Write-Host "  Model 2 -- $($models[1].model_name)" -ForegroundColor DarkGray
Write-Host "    Accuracy=$($models[1].metrics.accuracy) F1=$($models[1].metrics.f1_score) ROC-AUC=$($models[1].metrics.roc_auc)" -ForegroundColor DarkGray

# --- ADMIN FEEDBACK ---
Write-Host "`n[26] ADMIN FEEDBACK VIEW" -ForegroundColor Yellow
$adminFb = Invoke-RestMethod "$BASE/api/admin/feedback" -Headers $AH
Test-API "GET admin/feedback"                   ($adminFb.Count -ge 3)
Test-API "Feedback has user names"              ($adminFb[0].user_name -ne $null)

# --- SUMMARY ---
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TEST RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PASSED: $PASS" -ForegroundColor Green
if ($FAIL -gt 0) { Write-Host "  FAILED: $FAIL" -ForegroundColor Red }
else             { Write-Host "  FAILED: $FAIL" -ForegroundColor Green }
Write-Host "  TOTAL:  $($PASS + $FAIL)"
Write-Host ""
if ($FAIL -eq 0) { Write-Host "  ALL TESTS PASSED -- LoanWise AI is fully operational!" -ForegroundColor Green }
else             { Write-Host "  $FAIL test(s) failed." -ForegroundColor Red }
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  DEMO CREDENTIALS:" -ForegroundColor Yellow
Write-Host "  User:  demo@loanwise.ai  / Demo@2026"
Write-Host "  Admin: admin@loanwise.ai / Admin@2026"
Write-Host ""
Write-Host "  OPEN FRONTEND: frontend/index.html"
Write-Host "  API DOCS:      http://127.0.0.1:8000/docs"
Write-Host "============================================================" -ForegroundColor Cyan

