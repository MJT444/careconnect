const patientLng = 78;
const patientLat = 17;
const maxDistanceMeters = 5000;

const db = db.getSiblingDB("medical_db");

const pipeline = [
  {
    $geoNear: {
      near: {
        type: "Point",
        coordinates: [patientLng, patientLat],
      },
      distanceField: "distance_meters",
      maxDistance: maxDistanceMeters,
      spherical: true,
      query: { status: "ACTIVE" },
    },
  },
  { $sort: { nurse_id: 1, created_at: -1 } },
  {
    $group: {
      _id: "$nurse_id",
      nurse_id: { $first: "$nurse_id" },
      location: { $first: "$location" },
      distance_meters: { $first: "$distance_meters" },
      last_seen: { $first: "$created_at" },
      status: { $first: "$status" },
    },
  },
  { $sort: { distance_meters: 1 } },
  { $limit: 1 },
  {
    $project: {
      _id: 0,
      nurse_id: 1,
      distance_meters: { $round: ["$distance_meters", 1] },
      distance_km: { $round: [{ $divide: ["$distance_meters", 1000] }, 2] },
      last_seen: 1,
      location: 1,
    },
  },
];

const result = db.NursePings.aggregate(pipeline).toArray();

printjson(result);