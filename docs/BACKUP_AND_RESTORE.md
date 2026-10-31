# Disaster Recovery & Database Backup / Restore Guide

This operational guide details the database backup, verification, and restore procedures for the **Nueva Ecija Travel Itinerary** pilot application.

---

## 1. Overview & Operational Principles

Data integrity and disaster recovery are essential for both local pilot laptops and production cloud infrastructure. The database management script `scripts/db_backup_restore.py` provides:

1. **Deterministic Snapshots**: Generates timestamped SQL or binary snapshots with schema DDL and row data.
2. **Entity Verification**: Programmatically parses snapshots to verify presence of core entities (`users`, `municipalities`, `places`, `itineraries`).
3. **Disaster Recovery Drills**: Automated canary verification ensuring that lost data can be faithfully restored with zero data corruption.
4. **Multi-Engine Support**: Operates identically with **PostgreSQL** (via `pg_dump` and `psql`) and **SQLite** (for local development and CI testing).

---

## 2. CLI Usage & Operations

The backup utility is located at `scripts/db_backup_restore.py` and can be invoked from the repository root:

```bash
# 1. Create a snapshot in the default /backups folder
python scripts/db_backup_restore.py backup

# 2. Create a snapshot at a custom path
python scripts/db_backup_restore.py backup --output backups/ne_pilot_snapshot.sql

# 3. Verify backup file integrity
python scripts/db_backup_restore.py verify backups/ne_pilot_snapshot.sql

# 4. Restore database from snapshot
python scripts/db_backup_restore.py restore backups/ne_pilot_snapshot.sql

# 5. Run full automated backup and restore drill
python scripts/db_backup_restore.py drill
```

---

## 3. Automated Drill Lifecycle

The `drill` command simulates an end-to-end catastrophic loss and recovery cycle:

```
[Step 1/6] Seeding canary user record into database...
[Step 2/6] Generating backup snapshot...
[Step 3/6] Verifying snapshot integrity...
[Step 4/6] Simulating data loss (deleting canary record)...
[Step 5/6] Restoring database from snapshot...
[Step 6/6] Verifying canary restoration & cleanup...
```

This procedure is executed automatically as part of the automated test suite in `backend/tests/test_backup_restore.py`.

---

## 4. Production Deployment Scheduling

In production environments (Docker or standalone PostgreSQL host), schedule automated snapshots via cron:

```cron
# Daily backup at 02:00 AM UTC
0 2 * * * cd /opt/CaseStudy && python scripts/db_backup_restore.py backup >> /var/log/ne_backup.log 2>&1
```
