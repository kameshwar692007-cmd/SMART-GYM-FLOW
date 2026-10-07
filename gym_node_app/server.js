const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const cors = require('cors');
const db = require('./database');
const ml = require('./ai_engine/ml_service');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// ---------------------------------------------------------------------------
// HTML Page Routes
// ---------------------------------------------------------------------------
app.get('/', (req, res) => {
    res.sendFile('index.html', { root: path.join(__dirname, 'public') });
});

app.get('/owner/login', (req, res) => {
    res.sendFile('owner-login.html', { root: path.join(__dirname, 'public') });
});

app.get('/owner/dashboard', (req, res) => {
    res.sendFile('owner-dashboard.html', { root: path.join(__dirname, 'public') });
});

app.get('/member/login', (req, res) => {
    res.sendFile('member-login.html', { root: path.join(__dirname, 'public') });
});

app.get('/member/assessment', (req, res) => {
    res.sendFile('member-assessment.html', { root: path.join(__dirname, 'public') });
});

app.get('/member/workout', (req, res) => {
    res.sendFile('member-workout.html', { root: path.join(__dirname, 'public') });
});

// ---------------------------------------------------------------------------
// ML-OR API Endpoints: Models A & B + Operations Research Analytics
// ---------------------------------------------------------------------------

// Model A: Predict Station Dwell Time (t_dwell in minutes)
app.post('/api/ai/predict-dwell', (req, res) => {
    try {
        const { equipCat, muscleGroup, setVolume, repRangeType, experience, sharingMode } = req.body;
        const dwellTimeMins = ml.predictDwellTime({
            equipCat: parseInt(equipCat) || 0,
            muscleGroup: parseInt(muscleGroup) || 0,
            setVolume: parseInt(setVolume) || 3,
            repRangeType: parseInt(repRangeType) || 1,
            experience: parseInt(experience) || 2,
            sharingMode: parseInt(sharingMode) || 1
        });
        res.json({
            success: true,
            model: "Model A (Station Dwell Time Regressor)",
            r2Score: 0.9798,
            maeMinutes: 0.52,
            dwellTimeMinutes: dwellTimeMins
        });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Model B: Machine-Level Spatial-Temporal Utilization Forecaster (U_k,t)
app.get('/api/ai/station-utilization', (req, res) => {
    try {
        const day = req.query.day || "Monday";
        const forecast = ml.getStationUtilizationForecast(day);
        res.json({
            success: true,
            model: "Model B (Spatial-Temporal Machine Utilization Forecaster)",
            r2Score: 0.9788,
            wapePercent: "5.84%",
            forecast
        });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Operations Research: Equipment Utility Ratio (EUR), BIS & Procurement ROI
app.get('/api/owner/utility-analytics', async (req, res) => {
    try {
        const members = await db.getAllMembersWithBiometrics();
        const equipmentFleet = await db.getAllEquipment();
        const schedule = ml.solveFJSP(members, equipmentFleet);

        res.json({
            success: true,
            analytics: schedule.operationsResearch,
            shortages: schedule.equipmentShortages
        });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// ---------------------------------------------------------------------------
// Sudden Entry & Flexible Job-Shop Scheduling (FJSP) Endpoints
// ---------------------------------------------------------------------------

// Sudden Member Entry / Timing Change: Re-solves FJSP constraint graph in real time
app.post('/api/member/sudden-entry', async (req, res) => {
    try {
        const { username, arrivalTime, focusMuscle, durationMins } = req.body;
        if (!username) {
            return res.status(400).json({ success: false, message: "Username is required for sudden entry." });
        }

        const user = await db.getUserByUsername(username);
        if (!user) {
            return res.status(404).json({ success: false, message: "Member not found." });
        }

        // Update arrival timing & workout focus in SQLite
        const updatedUser = await db.updateBiometrics(username, {
            arrivalTime: arrivalTime || user.arrival_time || '08:00 AM',
            focusMuscle: focusMuscle || user.focus_muscle || 'Chest',
            durationMins: durationMins || user.duration_mins || 45
        });

        // Re-solve the FJSP constraint graph with Model A dwell times
        const members = await db.getAllMembersWithBiometrics();
        const equipmentFleet = await db.getAllEquipment();
        const schedule = ml.solveFJSP(members, equipmentFleet);

        const userPlan = schedule.memberPlans[username.toLowerCase()] || schedule.memberPlans[updatedUser.full_name.toLowerCase()];

        res.json({
            success: true,
            message: `⚡ Sudden entry processed for ${updatedUser.full_name} at ${updatedUser.arrival_time}! FJSP re-optimized with EUR ${schedule.operationsResearch.equipmentUtilityRatio}%.`,
            member: userPlan ? userPlan.member : updatedUser,
            plan: userPlan,
            eurScore: schedule.operationsResearch.equipmentUtilityRatio,
            activeWorkingInCount: schedule.workingInPairings.length,
            equipmentShortageCount: schedule.equipmentShortages.length
        });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Floor Schedule Matrix (Solved via FJSP with Model A Dwell Times)
app.get('/api/owner/floor-schedule', async (req, res) => {
    try {
        const members = await db.getAllMembersWithBiometrics();
        const equipmentFleet = await db.getAllEquipment();
        const schedule = ml.solveFJSP(members, equipmentFleet);
        res.json({ success: true, schedule });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Member Workout Plan (Derived from FJSP Solver)
app.get('/api/member/workout/:name', async (req, res) => {
    try {
        const memberKey = decodeURIComponent(req.params.name).toLowerCase();
        const members = await db.getAllMembersWithBiometrics();
        const equipmentFleet = await db.getAllEquipment();
        const schedule = ml.solveFJSP(members, equipmentFleet);

        const userPlan = schedule.memberPlans[memberKey];
        if (userPlan) {
            return res.json({
                success: true,
                plan: userPlan,
                eurScore: schedule.operationsResearch.equipmentUtilityRatio
            });
        }

        const firstKey = Object.keys(schedule.memberPlans)[0];
        if (firstKey) {
            return res.json({
                success: true,
                plan: schedule.memberPlans[firstKey],
                eurScore: schedule.operationsResearch.equipmentUtilityRatio
            });
        }

        return res.status(404).json({ success: false, message: "No workout plan found." });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Equipment Shortage & Requisition Reports
app.get('/api/owner/equipment-shortage', async (req, res) => {
    try {
        const members = await db.getAllMembersWithBiometrics();
        const equipmentFleet = await db.getAllEquipment();
        const schedule = ml.solveFJSP(members, equipmentFleet);
        res.json({
            success: true,
            shortages: schedule.equipmentShortages,
            totalDeficits: schedule.equipmentShortages.length,
            bottleneckIntensityScores: schedule.operationsResearch.bottleneckIntensityScores,
            procurementRoi: schedule.operationsResearch.procurementRoi
        });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// ---------------------------------------------------------------------------
// User Authentication & Biometrics API Endpoints
// ---------------------------------------------------------------------------

// User Registration
app.post('/api/auth/register', async (req, res) => {
    try {
        const { username, password, fullName, gender, age, heightCm, weightKg, goal, experience, arrivalTime, focusMuscle, durationMins } = req.body;
        
        if (!username || !password || !fullName) {
            return res.status(400).json({ success: false, message: "Username, password, and full name are required." });
        }

        const newUser = await db.registerUser({
            username,
            password,
            fullName,
            role: 'member',
            biometrics: {
                gender,
                age,
                heightCm,
                weightKg,
                goal,
                experience,
                arrivalTime,
                focusMuscle,
                durationMins
            }
        });

        res.json({
            success: true,
            message: `User '${username}' registered successfully!`,
            user: {
                id: newUser.id,
                username: newUser.username,
                fullName: newUser.full_name,
                role: newUser.role
            },
            biometrics: {
                bmi: newUser.bmi,
                bmiCategory: newUser.bmi_category,
                heightCm: newUser.height_cm,
                weightKg: newUser.weight_kg,
                goal: newUser.goal,
                arrivalTime: newUser.arrival_time
            }
        });
    } catch (err) {
        res.status(400).json({ success: false, message: err.message });
    }
});

// Member Authentication
app.post('/api/member/login', async (req, res) => {
    try {
        const { username, password, name } = req.body;
        const searchUser = username || name;
        if (!searchUser) {
            return res.status(400).json({ success: false, message: "Please provide a username." });
        }

        const user = await db.getUserByUsername(searchUser);
        if (!user) {
            return res.status(404).json({ success: false, message: `Member '${searchUser}' not found. Please register as a new member.` });
        }

        if (password && user.password !== password) {
            return res.status(401).json({ success: false, message: "Incorrect password. Please verify your credentials." });
        }

        res.json({
            success: true,
            message: "Authentication successful",
            member: {
                id: user.id,
                username: user.username,
                name: user.full_name,
                gender: user.gender,
                age: user.age,
                heightCm: user.height_cm,
                weightKg: user.weight_kg,
                bmi: user.bmi,
                bmiCategory: user.bmi_category,
                goal: user.goal,
                experience: user.experience,
                todayArrivalTime: user.arrival_time,
                durationMins: user.duration_mins,
                focusMuscle: user.focus_muscle
            }
        });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Owner Authentication
app.post('/api/owner/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        const user = await db.authenticateUser(username, password);
        if (user && user.role === 'owner') {
            return res.json({ success: true, message: `Welcome ${user.full_name}` });
        }
        return res.status(401).json({ success: false, message: "Invalid Owner credentials. (Default: owner / admin123)" });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Member Assessment Update
app.post('/api/member/assessment', async (req, res) => {
    try {
        const { username, name, gender, age, heightCm, weightKg, goal, experience, arrivalTime, durationMins, focusMuscle } = req.body;
        const targetUsername = username || name;

        if (!targetUsername) {
            return res.status(400).json({ success: false, message: "Username is required to save assessment." });
        }

        let user = await db.getUserByUsername(targetUsername);

        if (!user) {
            const cleanUser = targetUsername.toLowerCase().replace(/\s+/g, '_');
            user = await db.registerUser({
                username: cleanUser,
                password: '123',
                fullName: targetUsername,
                biometrics: {
                    gender,
                    age,
                    heightCm,
                    weightKg,
                    goal,
                    experience,
                    arrivalTime,
                    durationMins,
                    focusMuscle
                }
            });
        } else {
            user = await db.updateBiometrics(user.username, {
                fullName: name || user.full_name,
                gender,
                age,
                heightCm,
                weightKg,
                goal,
                experience,
                arrivalTime,
                durationMins,
                focusMuscle
            });
        }

        const bmiResult = db.computeBmi(parseFloat(heightCm), parseFloat(weightKg));

        res.json({
            success: true,
            message: "Biometrics updated in SQLite!",
            member: {
                id: user.id,
                username: user.username,
                name: user.full_name,
                gender: user.gender,
                age: user.age,
                heightCm: user.height_cm,
                weightKg: user.weight_kg,
                bmi: user.bmi,
                bmiCategory: user.bmi_category,
                goal: user.goal,
                experience: user.experience,
                todayArrivalTime: user.arrival_time,
                durationMins: user.duration_mins,
                focusMuscle: user.focus_muscle
            },
            bmiResult
        });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Member Profile Lookup
app.get('/api/member/profile/:username', async (req, res) => {
    try {
        const user = await db.getUserByUsername(req.params.username);
        if (!user) {
            return res.status(404).json({ success: false, message: "User not found" });
        }
        res.json({
            success: true,
            user: {
                id: user.id,
                username: user.username,
                name: user.full_name,
                gender: user.gender,
                age: user.age,
                heightCm: user.height_cm,
                weightKg: user.weight_kg,
                bmi: user.bmi,
                bmiCategory: user.bmi_category,
                goal: user.goal,
                experience: user.experience,
                todayArrivalTime: user.arrival_time,
                durationMins: user.duration_mins,
                focusMuscle: user.focus_muscle
            }
        });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Owner Equipment Operations
app.get('/api/owner/equipment', async (req, res) => {
    try {
        const equipment = await db.getAllEquipment();
        res.json({ success: true, equipment });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.post('/api/owner/equipment', async (req, res) => {
    try {
        const { name, category, quantity, swapAlternative } = req.body;
        const newEquipment = await db.addEquipment({
            name,
            category,
            quantity,
            swapAlternative
        });
        res.json({ success: true, equipment: newEquipment });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Owner Gym Settings
app.get('/api/owner/settings', async (req, res) => {
    try {
        const settings = await db.getGymSettings();
        res.json({ success: true, settings });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

app.post('/api/owner/settings', async (req, res) => {
    try {
        const { openTime, closeTime, morningPeak, eveningPeak } = req.body;
        const updated = await db.updateGymSettings({
            ...(openTime ? { openTime } : {}),
            ...(closeTime ? { closeTime } : {}),
            ...(morningPeak ? { morningPeak } : {}),
            ...(eveningPeak ? { eveningPeak } : {})
        });
        res.json({ success: true, settings: updated });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// Owner Member Database
app.get('/api/owner/members', async (req, res) => {
    try {
        const members = await db.getAllMembersWithBiometrics();
        res.json({ success: true, members });
    } catch (err) {
        res.status(500).json({ success: false, message: err.message });
    }
});

// ---------------------------------------------------------------------------
// Server Bootstrap
// ---------------------------------------------------------------------------
async function startServer() {
    try {
        await db.initDatabase();

        app.listen(PORT, () => {
            console.log(`====================================================`);
            console.log(`🚀 Smart Gym Node.js Server running on http://localhost:${PORT}`);
            console.log(`💾 Connected to SQLite Database (gym.db)`);
            console.log(`⚙️ ML-OR Engine Active: Model A (Dwell Time) & Model B (Spatial Utilization)`);
            console.log(`⚡ Flexible Job-Shop Scheduling (FJSP) with EUR Maximization Online`);
            console.log(`🏢 Gym Owner Portal:  http://localhost:${PORT}/owner/login`);
            console.log(`👤 Gym Member Portal: http://localhost:${PORT}/member/login`);
            console.log(`====================================================`);
        });
    } catch (err) {
        console.error("❌ Failed to start server:", err);
    }
}

startServer();
