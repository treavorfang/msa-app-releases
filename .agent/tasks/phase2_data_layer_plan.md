# Phase 2: Data Layer Reorganization Plan

## 📊 Scope

### Files to Review

- **Models**: 34 files
- **Repositories**: 28 files
- **DTOs**: Embedded in services (to be extracted if needed)

**Total**: 62+ files

---

## 🎯 Strategy

Given the large number of files, we'll use a **sampling approach**:

### Step 1: Sample Files (Demonstrate Pattern)

Review and reorganize 3-5 representative files to establish the pattern:

- 1 simple model (e.g., Category)
- 1 complex model (e.g., Ticket)
- 1 simple repository (e.g., CategoryRepository)
- 1 complex repository (e.g., TicketRepository)

### Step 2: Document Pattern

Create a template/pattern document that can be applied to remaining files

### Step 3: Batch Processing

Apply the pattern to remaining files in logical groups:

- Core models (User, Role, Permission)
- Business models (Ticket, Device, Customer)
- Financial models (Invoice, Payment, Purchase Order)
- Configuration models (Branch, Settings, Category)

---

## 📋 Checklist Per Model File

### Documentation

- [ ] Module docstring explaining the model
- [ ] Class docstring with purpose and relationships
- [ ] Field documentation (inline comments)
- [ ] Relationship documentation
- [ ] Meta class documentation

### Code Quality

- [ ] Proper imports organization
- [ ] Consistent field ordering
- [ ] Validation rules documented
- [ ] Indexes documented
- [ ] Constraints documented

### Best Practices

- [ ] Use descriptive field names
- [ ] Add help_text where appropriate
- [ ] Document foreign key relationships
- [ ] Add **str** method
- [ ] Add **repr** method (if useful)

---

## 📋 Checklist Per Repository File

### Documentation

- [ ] Module docstring explaining repository purpose
- [ ] Class docstring with CRUD operations
- [ ] Method docstrings for all public methods
- [ ] Query optimization notes
- [ ] Transaction handling notes

### Code Quality

- [ ] Proper imports organization
- [ ] Consistent method naming
- [ ] Error handling
- [ ] No duplicate code
- [ ] Efficient queries (no N+1)

### Best Practices

- [ ] Use select_related/prefetch_related
- [ ] Add pagination where needed
- [ ] Use transactions for multi-step operations
- [ ] Return DTOs instead of models (where appropriate)
- [ ] Add filtering/sorting methods

---

## 🎯 Priority Order

### High Priority (Core Functionality)

1. **User** - Authentication foundation
2. **Role** - Authorization foundation
3. **Ticket** - Main business entity
4. **Customer** - Customer management
5. **Device** - Device tracking

### Medium Priority (Business Features)

6. **Invoice** - Financial tracking
7. **Payment** - Payment processing
8. **Part** - Inventory management
9. **Supplier** - Supplier management
10. **PurchaseOrder** - Procurement

### Low Priority (Supporting Features)

11. **Category** - Organization
12. **Branch** - Multi-branch support
13. **Settings** - Configuration
14. **AuditLog** - Tracking
15. **Others** - Supporting entities

---

## 📝 Sample Files to Start With

### Models (3 files)

1. `models/category.py` - Simple model
2. `models/ticket.py` - Complex model with relationships
3. `models/user.py` - Core authentication model

### Repositories (3 files)

1. `repositories/category_repository.py` - Simple CRUD
2. `repositories/ticket_repository.py` - Complex queries
3. `repositories/user_repository.py` - Authentication queries

---

## ⏱️ Time Estimate

### Per File

- Simple model: 10-15 minutes
- Complex model: 20-30 minutes
- Simple repository: 15-20 minutes
- Complex repository: 30-40 minutes

### Total Estimate

- Sample files (6): 2-3 hours
- Remaining files (56): 15-20 hours
- **Total**: 17-23 hours

---

## 🚀 Approach

### Option A: Full Reorganization

- Reorganize all 62 files
- Time: 17-23 hours
- Best for: Long-term maintenance

### Option B: Critical Files Only

- Reorganize top 15 priority files
- Time: 5-7 hours
- Best for: Quick wins

### Option C: Pattern + Documentation

- Create pattern/template
- Document for future application
- Reorganize 6 sample files
- Time: 2-3 hours
- Best for: Establishing standards

---

**Recommended**: Start with **Option C** to establish the pattern, then decide on full reorganization.

**Status**: Ready to begin
**Next**: Sample model reorganization
