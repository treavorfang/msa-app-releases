"""Part Model - Inventory Management."""

import re
import random
from datetime import datetime
from peewee import AutoField, CharField, IntegerField, DecimalField, BooleanField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.supplier import Supplier
from models.branch import Branch
from models.category import Category


class Part(BaseModel):
    """Part model for inventory tracking."""
    
    id = AutoField(help_text="Primary key")
    sku = CharField(max_length=50, unique=True, help_text="Stock keeping unit")
    name = CharField(max_length=100, help_text="Part name")
    brand = CharField(max_length=50, null=True, help_text="Brand")
    model_compatibility = CharField(max_length=255, null=True, help_text="Compatible models")
    category = ForeignKeyField(Category, backref='parts', on_delete='SET NULL', null=True, help_text="Category")
    cost_price = DecimalField(max_digits=10, decimal_places=2, help_text="Cost price")
    min_stock_level = IntegerField(default=0, help_text="Minimum stock level")
    current_stock = IntegerField(default=0, help_text="Current stock")
    barcode = CharField(max_length=50, null=True, unique=True, help_text="Barcode")
    branch = ForeignKeyField(Branch, backref='parts', on_delete='SET NULL', null=True, help_text="Branch")
    supplier = ForeignKeyField(Supplier, backref='parts', on_delete='SET NULL', null=True, help_text="Supplier")
    created_at = DateTimeField(default=datetime.now, help_text="Creation timestamp")
    updated_at = DateTimeField(default=datetime.now, help_text="Update timestamp")
    is_active = BooleanField(default=True, help_text="Active status")
    
    class Meta:
        table_name = 'parts'
        indexes = ((('sku',), True), (('barcode',), True))
    
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self._generate_sku()
        if not self.barcode:
            self.barcode = self._generate_barcode()
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)
    
    def _generate_sku(self):
        """Generate SKU in format: BRAND(3)-CATEGORY(3)-NAME(4)-COUNTER(2)"""
        brand_part = "GEN"
        if self.brand:
            clean_brand = re.sub(r'[^A-Za-z0-9]', '', self.brand)
            brand_part = clean_brand[:3].upper() if clean_brand else "GEN"
        
        category_part = "PAR"
        if self.category and self.category.name:
            clean_category = re.sub(r'[^A-Za-z0-9]', '', self.category.name)
            category_part = clean_category[:3].upper() if clean_category else "PAR"
        
        name_part = "PART"
        if self.name:
            model_match = re.search(r'(\d+S?|\d+ Plus|\d+ Pro|S\d+)[^a-z]', self.name, re.IGNORECASE)
            if model_match:
                model = model_match.group(1)
                clean_model = re.sub(r'[^A-Za-z0-9]', '', model)
                name_part = clean_model[:4].upper()
            else:
                clean_name = re.sub(r'[^A-Za-z0-9]', '', self.name)
                name_part = clean_name[:4].upper() if clean_name else "PART"
        
        base_sku = f"{brand_part}-{category_part}-{name_part}"
        existing_skus = Part.select().where(Part.sku.startswith(base_sku))
        counter = existing_skus.count() + 1
        return f"{base_sku}-{counter:02d}"
    
    def _generate_barcode(self):
        """Generate barcode in format: PAR-BRAND(3)MODEL(NO)-XXXX"""
        brand_part = "GEN"
        if self.brand:
            clean_brand = re.sub(r'[^A-Za-z0-9]', '', self.brand)
            brand_part = clean_brand[:3].upper() if clean_brand else "GEN"
        
        model_number = "000"
        if self.name:
            numbers = re.findall(r'\d+', self.name)
            if numbers:
                model_number = numbers[0][:3].zfill(3)
        
        random_suffix = f"{random.randint(0, 9999):04d}"
        return f"PAR-{brand_part}{model_number}-{random_suffix}"
    
    def __str__(self):
        return self.name
    
    def is_low_stock(self):
        """Check if stock is below minimum level."""
        return self.current_stock <= self.min_stock_level