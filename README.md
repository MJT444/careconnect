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
  table (see `sql/01_schema_ddl.sql` — every folder and file is on the main branch) has no
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

1. **Execute Workflow 3**:
   ```bash
   mongosh "mongodb://admin:password@localhost:27017/medical_db?authSource=admin" mongo/02_workflow3_geonear.js
   ```
2. **Execute Workflow 4**:
   ```bash
   mongosh "mongodb://admin:password@localhost:27017/medical_db?authSource=admin" mongo/03_workflow4_facet.js
   ```

## EXPLAIN Plans Summary

The detailed execution statistics are saved in `performance/mongo_execution_stats.json`.

**Workflow 3 (`02_workflow3_geonear.js`)**:
- Uses the `GEO_NEAR_2DSPHERE` stage, backed by the `location_2dsphere` index, to efficiently find nearby nurses without scanning the entire collection.
- Applies an additional `FETCH` filter for the `ACTIVE` status.
- Final stages sort by distance and limit the result to 1.

**Workflow 4 (`03_workflow4_facet.js`)**:
- Initiates with a `COLLSCAN` (Collection Scan) because `$facet` inherently requires scanning all documents to compute multi-faceted aggregations across the entire dataset.
- Projects the necessary fields (`rating` and `tags`) using `PROJECTION_SIMPLE` before splitting into three parallel sub-pipelines:
  1. `ratingDistribution`: Uses `$group` and `$sort`.
  2. `topTags`: Uses `$unwind` on the array, followed by `$group`, `$sort`, and `$limit`.
  3. `overallAverage`: Uses `$group` to calculate total count and average rating.