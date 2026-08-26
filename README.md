# Care Connect

This project contains the basic infrastructure setup for the Care Connect application. It uses Docker and Docker Compose to spin up a MongoDB instance that is pre-configured with the required databases, collections, and indices.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your machine
- [Docker Compose](https://docs.docker.com/compose/install/) (comes bundled with Docker Desktop)

## Setup Instructions

1. **Start the database:**
   Open a terminal in the root folder of this project and run the following command to start the MongoDB container in the background:
   ```bash
   docker-compose up -d
   ```

2. **Verify it is running:**
   Check the status of your containers to make sure `medical_mongodb` is up:
   ```bash
   docker ps
   ```

## Database Details

When the container is spun up for the first time, it automatically runs the `mongo-init.js` script to configure the database.

- **Port:** `27017`
- **Root Username:** `admin`
- **Root Password:** `password`
- **Database Name:** `medical_db`

**Collections Created:**
- `MedicalCatalogs`
- `PatientReviews`
- `NursePings` (Includes a `2dsphere` geospatial index on `location` and a TTL index on `created_at` that expires documents after 2 hours)

## Troubleshooting

### "The indices weren't created" or "My changes to mongo-init.js aren't showing up"
The `mongo-init.js` initialization script is **only executed the very first time** the database starts up (i.e., when its data directory is completely empty). 

If you previously started the database and later updated the `mongo-init.js` file, MongoDB will ignore the new changes. To apply them, you must completely wipe the existing database volume and start fresh:

```bash
# This will delete the database volume and all existing data!
docker-compose down -v

# Start the database again (it will run the init script this time)
docker-compose up -d
```
