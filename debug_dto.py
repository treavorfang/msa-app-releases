
import sys
import os
sys.path.append(os.getcwd() + '/src/app')

from models.device import Device
from dtos.device_dto import DeviceDTO
from peewee import SqliteDatabase

# Setup in-memory DB for testing
test_db = SqliteDatabase(':memory:')
Device._meta.database = test_db
test_db.connect()
from models.customer import Customer

test_db.create_tables([Device, Customer])

c = Customer.create(name="TestCustomer", phone="123")

# 1. Create Device
print("Creating device with lock_type='PIN'...")
d = Device.create(
    brand="TestBrand",
    model="TestModel",
    lock_type="PIN",
    passcode="1234",
    customer=c
)
print(f"Device created: ID={d.id}, lock_type={d.lock_type}, passcode={d.passcode}")

# 2. Fetch it back
print("Fetching device...")
d_fetched = Device.get_by_id(d.id)
print(f"Device fetched: ID={d_fetched.id}, lock_type={d_fetched.lock_type}")

# 3. Convert to DTO
print("Converting to DTO...")
dto = DeviceDTO.from_model(d_fetched)
print(f"DTO lock_type: {dto.lock_type}")
print(f"DTO passcode: {dto.passcode}")

if dto.lock_type == "PIN":
    print("SUCCESS: DTO preserved lock_type")
else:
    print("FAILURE: DTO lost lock_type")

test_db.close()
