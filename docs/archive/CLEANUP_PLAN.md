# Code Cleanup Plan - MSA Application

## Overview

Comprehensive cleanup to remove duplicates, unused code, and deprecated features.

---

## Phase 1: Remove Job Tab (Deprecated)

### Files to Check/Remove:

- [ ] `/views/jobs/` directory (if exists)
- [ ] Job-related imports in `main_window.py`
- [ ] Job tab creation in `main_window.py`
- [ ] Job-related actions/menu items

---

## Phase 2: Remove Old/Unused Code

### Admin Dashboard

- [ ] Old `setup_roles_tab()` method (now using modern version)
- [ ] Unused role-related methods
- [ ] Old branch-related code (already removed branch tab)

### Main Window

- [ ] Old branch selector code (already removed)
- [ ] Unused imports
- [ ] Deprecated menu items

### Views

- [ ] Old `RolesTab` widget (`views/admin/tabs/roles_tab.py`)
- [ ] Unused dialog files
- [ ] Deprecated components

---

## Phase 3: Check for Duplicates

### Models

- [ ] Duplicate model definitions
- [ ] Unused model files

### Services

- [ ] Duplicate service methods
- [ ] Unused service files

### Controllers

- [ ] Duplicate controller methods
- [ ] Unused controller files

### Repositories

- [ ] Duplicate repository methods
- [ ] Unused repository files

---

## Phase 4: Clean Up Imports

### Check all files for:

- [ ] Unused imports
- [ ] Duplicate imports
- [ ] Circular import issues

---

## Phase 5: Remove Unused Assets

### Static Files

- [ ] Unused icons
- [ ] Unused images
- [ ] Unused CSS files

---

## Phase 6: Documentation Cleanup

### Remove/Update:

- [ ] Old README sections
- [ ] Deprecated documentation
- [ ] Outdated comments in code

---

## Execution Order

1. **Remove Job Tab** (biggest impact)
2. **Remove old RolesTab widget**
3. **Clean up Admin Dashboard**
4. **Clean up Main Window**
5. **Remove unused imports**
6. **Final verification**

---

**Status**: Ready to execute
**Date**: 2025-12-07
