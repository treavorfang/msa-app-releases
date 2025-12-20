"""
Migration: Add Technician Bonus and Performance Tracking Tables

This migration adds two new tables:
1. technician_bonuses - Track bonuses awarded to technicians
2. technician_performance - Track monthly performance metrics

Run this migration to enable bonus management and performance tracking features.
"""

from models.technician_bonus import TechnicianBonus
from models.technician_performance import TechnicianPerformance
from config.database import db


def run_migration():
    """Create the new tables"""
    print("Creating technician bonus and performance tables...")
    
    with db:
        # Create tables
        db.create_tables([TechnicianBonus, TechnicianPerformance])
        
        print("✓ Created technician_bonuses table")
        print("✓ Created technician_performance table")
        print("\nMigration completed successfully!")
        print("\nNew features enabled:")
        print("  - Bonus tracking (performance, quality, revenue, custom)")
        print("  - Monthly performance metrics")
        print("  - Commission and bonus calculations")


def rollback_migration():
    """Drop the tables (use with caution!)"""
    print("Rolling back migration...")
    
    with db:
        db.drop_tables([TechnicianBonus, TechnicianPerformance])
        
        print("✓ Dropped technician_bonuses table")
        print("✓ Dropped technician_performance table")
        print("\nRollback completed!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        response = input("Are you sure you want to rollback? This will delete all bonus and performance data! (yes/no): ")
        if response.lower() == "yes":
            rollback_migration()
        else:
            print("Rollback cancelled.")
    else:
        run_migration()
