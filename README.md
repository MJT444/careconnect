# MongoDB Workflows — CareConnect

This folder contains the MongoDB aggregation scripts for CareConnect's
`medical_db` database (Workflows 3 & 4 of the assignment).

## Collections used

- **NursePings** — real-time geospatial location logs for mobile nurses,
  created via `mongo-init.js` with a `2dsphere` index on `location` and a
  TTL index (`expireAfterSeconds: 7200`) on `created_at`.
- **PatientReviews** — patient-submitted reviews of clinics/appointments.

## Assumed schemas

Neither collection has enforced validation, so these are the field names
the scripts expect based on the assignment brief. If the seeder scripts
use different field names, update the aggregation pipelines to match.

**NursePings**
```json
{
  "nurse_id": "<UUID/INT>",
  "location": { "type": "Point", "coordinates": [lng, lat] },
  "status": "ACTIVE | OFFLINE",
  "created_at": "ISODate"
}
```

**PatientReviews**
```json
{
  "patient_id": "<UUID>",
  "clinic_id": "<UUID>",
  "rating": "1-5",
  "tags": ["string", "..."],
  "created_at": "ISODate"
}
```

## Workflow 3 — `02_workflow3_geonear.js`: Nearest Mobile Nurse

Given a patient's coordinates, finds the closest currently-active nurse.

- **Patient coordinates are not stored in Postgres** — the `patients`
  table (see `sql/01_schema_ddl.sql` on the `anant` branch) has no
  latitude/longitude column. We assume these are supplied by the client
  app at query time (e.g. live GPS), so the script takes them as
  hardcoded example inputs (`patientLng`, `patientLat`) at the top of
  the file rather than reading them from a database.
- **Search radius**: capped at 5km (`maxDistanceMeters = 5000`). The
  assignment brief doesn't specify a radius for this workflow
  (unlike the equivalent workflows in the other 4 projects, which do
  state 5km), so we used the same figure for consistency. Adjust to
  match your seeded data density if 5km returns no results.
- **"Nearest active nurse"** is resolved as: filter to `status: "ACTIVE"`
  pings within the radius, collapse to each nurse's most recent ping
  (nurses may have many historical pings), then sort by distance and
  take the closest one.
- Requires the `2dsphere` index on `NursePings.location` — without it,
  `$geoNear` cannot run (it's not just an optimization, it's a hard
  requirement of the stage).

## Workflow 4 — `03_workflow4_facet.js`: Multi-Faceted Review Analytics

Computes three statistics over `PatientReviews` in a single pass using
`$facet`:

1. **Rating distribution** — count of reviews per star rating (1–5).
2. **Top tags** — the 10 most frequent tags, using `$unwind` to flatten
   the `tags` array before grouping (grouping can't operate directly on
   array values).
3. **Overall average** — mean rating and total review count across all
   reviews.

- `$facet` scans the full input collection for each of its
  sub-pipelines by design — this is expected, not a missed
  optimization. There's no equivalent "index requirement" the way
  `$geoNear` has one; the EXPLAIN proof for this workflow should
  demonstrate correctness and reasonable execution time at 100k+ scale
  rather than index usage.

## Running the scripts

```bash
docker compose up -d
docker exec -it medical_mongodb mongosh \
  "mongodb://admin:password@localhost:27017/medical_db?authSource=admin" \
  mongo/02_workflow3_geonear.js

docker exec -it medical_mongodb mongosh \
  "mongodb://admin:password@localhost:27017/medical_db?authSource=admin" \
  mongo/03_workflow4_facet.js
```