import sys
import os

# Add src to path
sys.path.append(os.path.abspath('src/app'))

try:
    from core.dependency_container import DependencyContainer
    
    print("Initializing DependencyContainer...")
    container = DependencyContainer()
    
    print("Checking credit_note_service...")
    service = container.credit_note_service
    
    if service:
        print("SUCCESS: credit_note_service is available.")
    else:
        print("FAILURE: credit_note_service is None.")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
