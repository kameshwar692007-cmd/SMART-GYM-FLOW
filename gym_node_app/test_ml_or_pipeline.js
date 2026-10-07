// test_ml_or_pipeline.js
// Automated verification suite for the ML-OR Gym Equipment Utility Optimization System

const BASE_URL = 'http://localhost:3000';

async function runTests() {
  console.log('================================================================');
  console.log('🚀 STARTING REAL-WORLD ML-OR PIPELINE INTEGRATION TEST SUITE');
  console.log('================================================================\n');

  let passed = 0;
  let failed = 0;

  // Test 1: Model A Station Dwell-Time Regressor
  try {
    console.log('[Test 1] POST /api/ai/predict-dwell (Model A Station Dwell-Time Regressor)...');
    const res = await fetch(`${BASE_URL}/api/ai/predict-dwell`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        equipCat: 0,
        muscleGroup: 0,
        setVolume: 4,
        repRangeType: 1,
        experience: 2,
        sharingMode: 1
      })
    });
    const data = await res.json();
    if (res.ok && data.dwellTimeMinutes > 0 && data.r2Score) {
      console.log(`  ✅ Passed: Predicted Dwell = ${data.dwellTimeMinutes} min`);
      console.log(`     Model A R² = ${data.r2Score}, MAE = ${data.maeMinutes} min`);
      passed++;
    } else {
      throw new Error(`Unexpected response: ${JSON.stringify(data)}`);
    }
  } catch (err) {
    console.error(`  ❌ Failed Test 1: ${err.message}`);
    failed++;
  }

  // Test 2: Model B Spatial-Temporal Utilization Forecaster
  try {
    console.log('\n[Test 2] GET /api/ai/station-utilization (Model B Heatmap & Surge Analysis)...');
    const res = await fetch(`${BASE_URL}/api/ai/station-utilization?day=Monday`);
    const data = await res.json();
    if (res.ok && data.forecast && data.forecast.matrix) {
      const hours = Object.keys(data.forecast.matrix);
      console.log(`  ✅ Passed: Generated ${hours.length} hourly spatial predictions for ${data.forecast.day}`);
      console.log(`     Machine Groups: ${data.forecast.machineGroups.join(', ')}`);
      console.log(`     Peak Bench Press at 05:00 PM = ${(data.forecast.matrix['05:00 PM'].Barbell_Bench_Press * 100).toFixed(1)}%`);
      console.log(`     Model B Macro R² = ${data.r2Score}, WAPE = ${data.wapePercent}`);
      passed++;
    } else {
      throw new Error(`Unexpected response: ${JSON.stringify(data)}`);
    }
  } catch (err) {
    console.error(`  ❌ Failed Test 2: ${err.message}`);
    failed++;
  }

  // Test 3: Owner ML-OR Utility Analytics (EUR, Idle Reduction, BIS, Procurement ROI)
  try {
    console.log('\n[Test 3] GET /api/owner/utility-analytics (EUR, Idle Reduction, BIS & Procurement ROI)...');
    const res = await fetch(`${BASE_URL}/api/owner/utility-analytics`);
    const data = await res.json();
    if (res.ok && data.analytics && data.analytics.equipmentUtilityRatio > 0) {
      console.log(`  ✅ Passed: Equipment Utility Ratio (EUR) = ${data.analytics.equipmentUtilityRatio}%`);
      console.log(`     Peak Idle Reduction = ${data.analytics.peakIdleReductionPercent}%`);
      console.log(`     Bottleneck Intensity Scores:`, data.analytics.bottleneckIntensityScores);
      console.log(`     Procurement ROI Recommendations Count: ${data.analytics.procurementRoi.length}`);
      if (data.analytics.procurementRoi.length > 0) {
        console.log(`     Sample ROI: Machine = ${data.analytics.procurementRoi[0].candidateMachine}, Retained = ${data.analytics.procurementRoi[0].monthlyRoiDollars}, Wait Drop = ${data.analytics.procurementRoi[0].projectedWaitReduction}`);
      }
      passed++;
    } else {
      throw new Error(`Unexpected response: ${JSON.stringify(data)}`);
    }
  } catch (err) {
    console.error(`  ❌ Failed Test 3: ${err.message}`);
    failed++;
  }

  // Test 4: Member Sudden-Entry Dynamic FJSP Re-scheduling
  try {
    console.log('\n[Test 4] POST /api/member/sudden-entry (Dynamic FJSP Constraint Graph Re-solver)...');
    const memRes = await fetch(`${BASE_URL}/api/owner/members`);
    const memData = await memRes.json();
    const testUsername = (memData.members && memData.members.length > 0) ? memData.members[0].username : 'alex';

    const res = await fetch(`${BASE_URL}/api/member/sudden-entry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: testUsername,
        arrivalTime: '08:00 AM',
        focusMuscle: 'Chest',
        durationMins: 45
      })
    });
    const data = await res.json();
    if (res.ok && data.success && data.plan && data.plan.steps && data.plan.steps.length > 0) {
      console.log(`  ✅ Passed: Dynamic FJSP successfully re-solved floor schedule for member '${testUsername}'`);
      console.log(`     Assigned ${data.plan.steps.length} sequential operations.`);
      const firstOp = data.plan.steps[0];
      console.log(`     Op 1: Station '${firstOp.station}' (${firstOp.equipmentName}) | Mode: ${firstOp.sharingMode} | Time: ${firstOp.timeWindow} | Dwell: ${firstOp.predictedDwellMins} min`);
      console.log(`     Global Floor EUR = ${data.eurScore}% | Active Working-In Pairs: ${data.activeWorkingInCount}`);
      passed++;
    } else {
      throw new Error(`Unexpected response: ${JSON.stringify(data)}`);
    }
  } catch (err) {
    console.error(`  ❌ Failed Test 4: ${err.message}`);
    failed++;
  }

  // Test 5: Owner Equipment Shortage Reporting
  try {
    console.log('\n[Test 5] GET /api/owner/equipment-shortage (Owner Procurement Alerts)...');
    const res = await fetch(`${BASE_URL}/api/owner/equipment-shortage`);
    const data = await res.json();
    if (res.ok && Array.isArray(data.shortages)) {
      console.log(`  ✅ Passed: Returned ${data.shortages.length} shortage notices across all time slots.`);
      if (data.shortages.length > 0) {
        console.log(`     Sample Shortage: [${data.shortages[0].timeSlot}] ${data.shortages[0].equipmentName} -> ${data.shortages[0].recommendation}`);
      }
      passed++;
    } else {
      throw new Error(`Unexpected response: ${JSON.stringify(data)}`);
    }
  } catch (err) {
    console.error(`  ❌ Failed Test 5: ${err.message}`);
    failed++;
  }

  console.log('\n================================================================');
  console.log(`🏁 TEST RESULTS: ${passed} PASSED | ${failed} FAILED`);
  console.log('================================================================\n');

  if (failed > 0) {
    process.exit(1);
  }
}

runTests();
