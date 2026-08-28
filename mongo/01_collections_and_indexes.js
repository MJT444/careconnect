db = db.getSiblingDB('medical_db');


db.createCollection('MedicalCatalogs');
db.createCollection('PatientReviews');
db.createCollection('NursePings');

print("Successfully created MedicalCatalogs, PatientReviews, and NursePings collections.");


db.NursePings.createIndex({ "location": "2dsphere" });
db.NursePings.createIndex(
    {
        "created_at": 1
    },
    {
        expireAfterSeconds: 7200
    }
);

print("Successfully created the indices on location and created_at columns of NursePings.");