import shutil
from pathlib import Path
from .validator import validate_course

def process_course(course_id: str, staging_dir: str, output_dir: str) -> bool:
    """Processes raw AI outputs, validates them, and moves them to the final directory."""
    raw_dir = Path(staging_dir) / course_id / "raw"
    final_dir = Path(output_dir) / course_id
    
    if not raw_dir.exists():
        print(f"Error: Raw directory not found at {raw_dir}")
        print("Please ensure the AI agent has generated the files.")
        return False
        
    print(f"Validating raw data in {raw_dir}...")
    report = validate_course(raw_dir, course_id)
    
    if report.has_errors():
        print("Validation Failed. Please fix the following errors in the raw data:")
        for err in report.errors:
            print(f"  - {err}")
        return False
        
    print("Validation passed. Moving files to final directory...")
    
    # Create final directory if not exists
    final_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy files
    # We use copytree with dirs_exist_ok=True (Python 3.8+)
    shutil.copytree(raw_dir, final_dir, dirs_exist_ok=True)
    
    return True
