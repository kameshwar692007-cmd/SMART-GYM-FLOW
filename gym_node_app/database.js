const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const ml = require('./ai_engine/ml_service');

const DB_PATH = path.join(__dirname, 'gym.db');
const db = new sqlite3.Database(DB_PATH);

// Promise helpers for clean async/await
const queryRun = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function (err) {
            if (err) reject(err);
            else resolve({ id: this.lastID, changes: this.changes });
        });
    });
};

const queryGet = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
};

const queryAll = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) reject(err);
            else resolve(rows);
        });
    });
};

// Initialize schema, migrations, and initial seed data
async function initDatabase() {
    // 1. Users Table
    await queryRun(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);

    // 2. Biometrics & Workout Preference Table (Enriched with AI predictions)
    await queryRun(`
        CREATE TABLE IF NOT EXISTS biometrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            gender TEXT DEFAULT 'Male',
            age INTEGER DEFAULT 25,
            height_cm REAL DEFAULT 175.0,
            weight_kg REAL DEFAULT 70.0,
            bmi REAL DEFAULT 22.9,
            bmi_category TEXT DEFAULT 'Normal / Healthy Weight',
            goal TEXT DEFAULT 'Bodybuilding (Muscle Mass)',
            experience TEXT DEFAULT 'Beginner (Fresher)',
            arrival_time TEXT DEFAULT '08:00 AM',
            duration_mins INTEGER DEFAULT 45,
            focus_muscle TEXT DEFAULT 'Chest',
            predicted_calories INTEGER DEFAULT 420,
            target_bpm INTEGER DEFAULT 145,
            optimal_rest_seconds INTEGER DEFAULT 75,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    `);

    // Run schema migration for existing databases
    try {
        await queryRun(`ALTER TABLE biometrics ADD COLUMN predicted_calories INTEGER DEFAULT 420`);
    } catch (e) { /* column exists */ }
    try {
        await queryRun(`ALTER TABLE biometrics ADD COLUMN target_bpm INTEGER DEFAULT 145`);
    } catch (e) { /* column exists */ }
    try {
        await queryRun(`ALTER TABLE biometrics ADD COLUMN optimal_rest_seconds INTEGER DEFAULT 75`);
    } catch (e) { /* column exists */ }

    // 3. Equipment Table
    await queryRun(`
        CREATE TABLE IF NOT EXISTS equipment (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            stations TEXT NOT NULL,
            swap_alternative TEXT,
            status TEXT DEFAULT 'Active'
        )
    `);

    // 4. Gym Operating Settings Table
    await queryRun(`
        CREATE TABLE IF NOT EXISTS gym_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    `);

    // Seed default owner and members if users table is empty
    const userCount = await queryGet(`SELECT COUNT(*) as count FROM users`);
    if (userCount.count === 0) {
        console.log("🌱 Seeding initial database records...");

        // Seed Gym Owner
        await queryRun(
            `INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)`,
            ['owner', 'admin123', 'Gym Facility Director', 'owner']
        );

        // Seed Initial Members with rich biometric records
        const seedMembers = [
            {
                username: 'alex',
                password: '123',
                fullName: 'Alex Miller',
                gender: 'Male',
                age: 24,
                heightCm: 178,
                weightKg: 74.5,
                bmi: 23.5,
                bmiCategory: 'Normal / Healthy Weight',
                goal: 'Bodybuilding (Muscle Mass)',
                experience: 'Intermediate',
                arrivalTime: '08:00 AM',
                durationMins: 45,
                focusMuscle: 'Chest'
            },
            {
                username: 'marcus',
                password: '123',
                fullName: 'Marcus Vance',
                gender: 'Male',
                age: 27,
                heightCm: 182,
                weightKg: 88.0,
                bmi: 26.6,
                bmiCategory: 'Overweight (High Muscle)',
                goal: 'Strength & Power (Powerlifting)',
                experience: 'Advanced',
                arrivalTime: '08:00 AM',
                durationMins: 45,
                focusMuscle: 'Chest'
            },
            {
                username: 'sarah',
                password: '123',
                fullName: 'Sarah Connor',
                gender: 'Female',
                age: 29,
                heightCm: 168,
                weightKg: 62.0,
                bmi: 22.0,
                bmiCategory: 'Normal / Healthy Weight',
                goal: 'Fat Loss & Lean Definition',
                experience: 'Beginner (Fresher)',
                arrivalTime: '08:00 AM',
                durationMins: 45,
                focusMuscle: 'Legs'
            },
            {
                username: 'elena',
                password: '123',
                fullName: 'Elena Rostova',
                gender: 'Female',
                age: 23,
                heightCm: 165,
                weightKg: 55.0,
                bmi: 20.2,
                bmiCategory: 'Normal / Healthy Weight',
                goal: 'General Fitness & Toning',
                experience: 'Beginner (Fresher)',
                arrivalTime: '08:15 AM',
                durationMins: 45,
                focusMuscle: 'Legs'
            }
        ];

        for (const m of seedMembers) {
            const userRes = await queryRun(
                `INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, 'member')`,
                [m.username, m.password, m.fullName]
            );

            // Compute AI predictions for seed members
            const ai = ml.predictBiometrics({
                age: m.age,
                gender: m.gender,
                heightCm: m.heightCm,
                weightKg: m.weightKg,
                experience: m.experience,
                goal: m.goal,
                durationMins: m.durationMins
            });

            await queryRun(
                `INSERT INTO biometrics (user_id, gender, age, height_cm, weight_kg, bmi, bmi_category, goal, experience, arrival_time, duration_mins, focus_muscle, predicted_calories, target_bpm, optimal_rest_seconds)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                [userRes.id, m.gender, m.age, m.heightCm, m.weightKg, m.bmi, m.bmiCategory, m.goal, m.experience, m.arrivalTime, m.durationMins, m.focusMuscle, ai.predictedCalories, ai.targetAvgBpm, ai.optimalRestSeconds]
            );
        }

        // Seed Equipment
        const initialFleet = [
            {
                id: "EQ_01",
                name: "Barbell Bench Press",
                category: "Chest",
                quantity: 2,
                stations: JSON.stringify(["Bench Press #1", "Bench Press #2"]),
                swapAlternative: "Incline Dumbbell Bench"
            },
            {
                id: "EQ_02",
                name: "Incline Dumbbell Bench",
                category: "Chest",
                quantity: 3,
                stations: JSON.stringify(["Dumbbell Bench #1", "Dumbbell Bench #2", "Dumbbell Bench #3"]),
                swapAlternative: "Seated Chest Press Machine"
            },
            {
                id: "EQ_03",
                name: "Seated Chest Press Machine",
                category: "Chest",
                quantity: 1,
                stations: JSON.stringify(["Chest Press Machine #1"]),
                swapAlternative: "Cable Crossover Station"
            },
            {
                id: "EQ_04",
                name: "Olympic Squat Rack",
                category: "Legs",
                quantity: 2,
                stations: JSON.stringify(["Squat Rack #1", "Squat Rack #2"]),
                swapAlternative: "45-Degree Leg Press"
            },
            {
                id: "EQ_05",
                name: "45-Degree Leg Press",
                category: "Legs",
                quantity: 2,
                stations: JSON.stringify(["Leg Press #1", "Leg Press #2"]),
                swapAlternative: "Plate-Loaded Hack Squat"
            },
            {
                id: "EQ_06",
                name: "Plate-Loaded Hack Squat",
                category: "Legs",
                quantity: 1,
                stations: JSON.stringify(["Hack Squat #1"]),
                swapAlternative: "45-Degree Leg Press"
            },
            {
                id: "EQ_07",
                name: "Lat Pulldown Machine",
                category: "Back",
                quantity: 2,
                stations: JSON.stringify(["Lat Pulldown #1", "Lat Pulldown #2"]),
                swapAlternative: "Seated Cable Row Station"
            },
            {
                id: "EQ_08",
                name: "Seated Cable Row Station",
                category: "Back",
                quantity: 1,
                stations: JSON.stringify(["Cable Row #1"]),
                swapAlternative: "Lat Pulldown Machine"
            },
            {
                id: "EQ_09",
                name: "Cable Crossover Station",
                category: "Full Body",
                quantity: 2,
                stations: JSON.stringify(["Cable Crossover #1", "Cable Crossover #2"]),
                swapAlternative: "Incline Dumbbell Bench"
            }
        ];

        for (const eq of initialFleet) {
            await queryRun(
                `INSERT INTO equipment (id, name, category, quantity, stations, swap_alternative, status) VALUES (?, ?, ?, ?, ?, ?, 'Active')`,
                [eq.id, eq.name, eq.category, eq.quantity, eq.stations, eq.swapAlternative]
            );
        }

        // Seed Settings
        await queryRun(`INSERT INTO gym_settings (key, value) VALUES ('openTime', '06:00 AM')`);
        await queryRun(`INSERT INTO gym_settings (key, value) VALUES ('closeTime', '10:00 PM')`);
        await queryRun(`INSERT INTO gym_settings (key, value) VALUES ('morningPeak', '07:30 AM - 09:00 AM')`);
        await queryRun(`INSERT INTO gym_settings (key, value) VALUES ('eveningPeak', '05:30 PM - 07:30 PM')`);
        await queryRun(`INSERT INTO gym_settings (key, value) VALUES ('gymName', 'Iron Peak Fitness Club')`);

        console.log("✅ Seed database created successfully with SQLite.");
    }
}

// Helper: Calculate BMI and Health Range
function computeBmi(heightCm, weightKg) {
    if (!heightCm || heightCm <= 0) return { bmi: 0, category: "Unknown", color: "#94a3b8" };
    const heightM = heightCm / 100.0;
    const bmi = parseFloat((weightKg / (heightM * heightM)).toFixed(1));
    let category = "Normal / Healthy Weight";
    let color = "#10b981";

    if (bmi < 18.5) {
        category = "Underweight (Focus on Lean Surplus & Foundation)";
        color = "#38bdf8";
    } else if (bmi >= 18.5 && bmi <= 24.9) {
        category = "Normal / Healthy Weight (Ideal for Muscle Hypertrophy)";
        color = "#10b981";
    } else if (bmi >= 25.0 && bmi <= 29.9) {
        category = "Overweight (High-Turnover Circuits & Caloric Burn)";
        color = "#f59e0b";
    } else {
        category = "Obese Range (Low-Impact Joint-Safe Conditioning)";
        color = "#ef4444";
    }
    return { bmi, category, color };
}

// User & Member operations
async function getUserByUsername(username) {
    return await queryGet(
        `SELECT u.id, u.username, u.password, u.full_name, u.role, u.created_at,
                b.gender, b.age, b.height_cm, b.weight_kg, b.bmi, b.bmi_category,
                b.goal, b.experience, b.arrival_time, b.duration_mins, b.focus_muscle,
                b.predicted_calories, b.target_bpm, b.optimal_rest_seconds, b.updated_at
         FROM users u
         LEFT JOIN biometrics b ON u.id = b.user_id
         WHERE LOWER(u.username) = LOWER(?)`,
        [username]
    );
}

async function registerUser({ username, password, fullName, role = 'member', biometrics = {} }) {
    // Check if username already exists
    const existing = await queryGet(`SELECT id FROM users WHERE LOWER(username) = LOWER(?)`, [username]);
    if (existing) {
        throw new Error(`Username '${username}' is already taken. Please choose another.`);
    }

    const userRes = await queryRun(
        `INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)`,
        [username.trim(), password, fullName.trim(), role]
    );

    const userId = userRes.id;

    // Calculate initial BMI
    const h = parseFloat(biometrics.heightCm) || 175.0;
    const w = parseFloat(biometrics.weightKg) || 70.0;
    const bmiInfo = computeBmi(h, w);

    // AI Model A Inference
    const aiPred = ml.predictBiometrics({
        age: biometrics.age || 25,
        gender: biometrics.gender || 'Male',
        heightCm: h,
        weightKg: w,
        experience: biometrics.experience || 'Beginner (Fresher)',
        goal: biometrics.goal || 'Bodybuilding (Muscle Mass)',
        durationMins: biometrics.durationMins || 45
    });

    await queryRun(
        `INSERT INTO biometrics (user_id, gender, age, height_cm, weight_kg, bmi, bmi_category, goal, experience, arrival_time, duration_mins, focus_muscle, predicted_calories, target_bpm, optimal_rest_seconds)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [
            userId,
            biometrics.gender || 'Male',
            parseInt(biometrics.age) || 25,
            h,
            w,
            bmiInfo.bmi,
            bmiInfo.category,
            biometrics.goal || 'Bodybuilding (Muscle Mass)',
            biometrics.experience || 'Beginner (Fresher)',
            biometrics.arrivalTime || '08:00 AM',
            parseInt(biometrics.durationMins) || 45,
            biometrics.focusMuscle || 'Chest',
            aiPred.predictedCalories,
            aiPred.targetAvgBpm,
            aiPred.optimalRestSeconds
        ]
    );

    return await getUserByUsername(username);
}

async function authenticateUser(username, password) {
    const user = await getUserByUsername(username);
    if (!user) {
        return null;
    }
    if (user.password !== password) {
        return null;
    }
    return user;
}

async function updateBiometrics(username, bioData) {
    const user = await getUserByUsername(username);
    if (!user) {
        throw new Error(`User '${username}' not found.`);
    }

    const h = parseFloat(bioData.heightCm) || user.height_cm || 175;
    const w = parseFloat(bioData.weightKg) || user.weight_kg || 70;
    const bmiInfo = computeBmi(h, w);

    // AI Model A Inference
    const aiPred = ml.predictBiometrics({
        age: bioData.age || user.age || 25,
        gender: bioData.gender || user.gender || 'Male',
        heightCm: h,
        weightKg: w,
        experience: bioData.experience || user.experience,
        goal: bioData.goal || user.goal,
        durationMins: bioData.durationMins || user.duration_mins || 45
    });

    await queryRun(
        `UPDATE biometrics
         SET gender = ?, age = ?, height_cm = ?, weight_kg = ?, bmi = ?, bmi_category = ?,
             goal = ?, experience = ?, arrival_time = ?, duration_mins = ?, focus_muscle = ?,
             predicted_calories = ?, target_bpm = ?, optimal_rest_seconds = ?,
             updated_at = CURRENT_TIMESTAMP
         WHERE user_id = ?`,
        [
            bioData.gender || user.gender || 'Male',
            parseInt(bioData.age) || user.age || 25,
            h,
            w,
            bmiInfo.bmi,
            bmiInfo.category,
            bioData.goal || user.goal,
            bioData.experience || user.experience,
            bioData.arrivalTime || user.arrival_time || '08:00 AM',
            parseInt(bioData.durationMins) || user.duration_mins || 45,
            bioData.focusMuscle || user.focus_muscle || 'Chest',
            aiPred.predictedCalories,
            aiPred.targetAvgBpm,
            aiPred.optimalRestSeconds,
            user.id
        ]
    );

    // If full name update provided
    if (bioData.fullName) {
        await queryRun(`UPDATE users SET full_name = ? WHERE id = ?`, [bioData.fullName, user.id]);
    }

    return await getUserByUsername(username);
}

async function getAllMembersWithBiometrics() {
    return await queryAll(`
        SELECT u.id, u.username, u.full_name, u.role, u.created_at,
               b.gender, b.age, b.height_cm, b.weight_kg, b.bmi, b.bmi_category,
               b.goal, b.experience, b.arrival_time, b.duration_mins, b.focus_muscle,
               b.predicted_calories, b.target_bpm, b.optimal_rest_seconds, b.updated_at
        FROM users u
        LEFT JOIN biometrics b ON u.id = b.user_id
        WHERE u.role = 'member'
        ORDER BY u.id ASC
    `);
}

// Equipment operations
async function getAllEquipment() {
    const rows = await queryAll(`SELECT * FROM equipment ORDER BY id ASC`);
    return rows.map(r => ({
        ...r,
        stations: JSON.parse(r.stations || '[]')
    }));
}

async function addEquipment({ name, category, quantity, swapAlternative }) {
    const qty = parseInt(quantity) || 1;
    const existing = await queryAll(`SELECT id FROM equipment`);
    const newId = `EQ_${String(existing.length + 1).padStart(2, '0')}`;
    const stations = [];
    for (let i = 1; i <= qty; i++) {
        stations.push(`${name} #${i}`);
    }

    await queryRun(
        `INSERT INTO equipment (id, name, category, quantity, stations, swap_alternative, status) VALUES (?, ?, ?, ?, ?, ?, 'Active')`,
        [newId, name, category, qty, JSON.stringify(stations), swapAlternative || '']
    );

    return {
        id: newId,
        name,
        category,
        quantity: qty,
        stations,
        swap_alternative: swapAlternative,
        status: 'Active'
    };
}

// Gym Settings
async function getGymSettings() {
    const rows = await queryAll(`SELECT key, value FROM gym_settings`);
    const settings = {};
    rows.forEach(r => {
        settings[r.key] = r.value;
    });
    return settings;
}

async function updateGymSettings(newSettings) {
    for (const [key, value] of Object.entries(newSettings)) {
        await queryRun(
            `INSERT INTO gym_settings (key, value) VALUES (?, ?)
             ON CONFLICT(key) DO UPDATE SET value = excluded.value`,
            [key, String(value)]
        );
    }
    return await getGymSettings();
}

module.exports = {
    initDatabase,
    computeBmi,
    getUserByUsername,
    registerUser,
    authenticateUser,
    updateBiometrics,
    getAllMembersWithBiometrics,
    getAllEquipment,
    addEquipment,
    getGymSettings,
    updateGymSettings
};
