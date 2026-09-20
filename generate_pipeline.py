#!/usr/bin/env python3
"""
Cybron Course Generation Pipeline — Main CLI

Usage:
    # Generate prompts for a course
    python3 generate_pipeline.py prompts "course_id"

    # Process staged AI outputs → validate + merge + output
    python3 generate_pipeline.py process "course_id"

    # Validate an existing course
    python3 generate_pipeline.py validate "course_id"

    # Show status of a course
    python3 generate_pipeline.py status "course_id"
"""
import argparse
import sys
from pathlib import Path

from pipeline.prompt_generator import generate_prompts_for_course, generate_master_instructions
from pipeline.post_processor import process_course
from pipeline.validator import validate_course

STAGING_DIR = "staging"
COURSES_DIR = "v2/courses"

def cmd_prompts(args):
    """Generate prompt files for AI agent to read."""
    course_id = args.course_id
    print(f"\n📝 Generating prompts for course: {course_id}")
    
    count = generate_prompts_for_course(
        course_id=course_id,
        staging_dir=STAGING_DIR
    )

    instructions_path = generate_master_instructions(
        course_id=course_id,
        staging_dir=STAGING_DIR
    )

    print(f"\n{'='*60}")
    print(f"✅ Generated {count} prompt instructions")
    print(f"📋 Master instructions: {instructions_path}")
    print(f"\n📌 Next step: Tell your AI agent to read {instructions_path}")
    print(f"   and follow the instructions to generate course data.")
    print(f"{'='*60}")

def cmd_process(args):
    """Process staged AI outputs: validate and merge into v1/courses."""
    course_id = args.course_id
    print(f"\n⚙️ Processing staged outputs for: {course_id}")
    
    success = process_course(
        course_id=course_id,
        staging_dir=STAGING_DIR,
        output_dir=COURSES_DIR
    )
    
    if success:
        print(f"\n✅ Processing complete! Output saved to {COURSES_DIR}/{course_id}/")
    else:
        print(f"\n❌ Processing failed. Check logs above.")
        sys.exit(1)

def cmd_validate(args):
    """Validate an existing course or all courses."""
    courses_to_validate = []
    
    if getattr(args, 'all', False):
        courses_dir = Path(COURSES_DIR)
        if courses_dir.exists():
            for d in courses_dir.iterdir():
                if d.is_dir():
                    courses_to_validate.append(d.name)
        if not courses_to_validate:
            print(f"❌ No courses found in {COURSES_DIR}")
            sys.exit(1)
    else:
        if not args.course_id:
            print("❌ Specify a course_id or use --all")
            sys.exit(1)
        courses_to_validate = [args.course_id]

    total_errors = 0
    print(f"\n{'='*60}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    for course_id in courses_to_validate:
        course_path = Path(COURSES_DIR) / course_id
        
        if not course_path.exists():
            print(f"  ❌ {course_id}: Course not found")
            total_errors += 1
            continue

        report = validate_course(course_path, course_id)

        if report.has_errors():
            print(f"  ❌ {course_id}: Failed with {len(report.errors)} errors")
            for err in report.errors:
                print(f"     - {err}")
            total_errors += len(report.errors)
        else:
            print(f"  ✅ {course_id}: Passed")

    if total_errors > 0:
        print(f"\n❌ Validation failed with {total_errors} total errors.")
        sys.exit(1)
    else:
        print(f"\n✅ All validations passed!")

def cmd_validate_raw(args):
    """Validate partial/raw outputs in the staging directory (strict schema, lenient missing)."""
    course_id = args.course_id
    raw_path = Path(STAGING_DIR) / course_id / "raw"
    
    if not raw_path.exists():
        print(f"❌ Raw directory not found: {raw_path}")
        sys.exit(1)

    print(f"🔍 Validating RAW course data: {course_id}")
    report = validate_course(raw_path, course_id, strict_missing=False)

    if report.has_errors():
        print(f"\n❌ Raw validation failed with {len(report.errors)} errors:")
        for err in report.errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"\n✅ Raw validation passed! Schemas look good.")

def cmd_status(args):
    """Show status of course generation."""
    course_id = args.course_id
    staging = Path(STAGING_DIR) / course_id
    output_dir = Path(COURSES_DIR) / course_id
    
    print(f"\n📦 Course: {course_id}")
    
    # Check prompts
    prompts_dir = staging / "prompts"
    prompt_count = len(list(prompts_dir.glob("*.txt"))) if prompts_dir.exists() else 0
    
    # Check raw
    raw_dir = staging / "raw"
    raw_count = len(list(raw_dir.glob("**/*.json"))) if raw_dir.exists() else 0
    
    # Check output
    has_output = output_dir.exists() and (output_dir / "chapters.json").exists()
    
    if has_output:
        status = "✅ Done"
    elif raw_count > 0:
        status = "🔄 Ready to process"
    elif prompt_count > 0:
        status = "📝 Prompts ready"
    else:
        status = "⬜ Not started"
        
    print(f"Prompts Generated: {prompt_count}")
    print(f"Raw Files Generated: {raw_count}")
    print(f"Status: {status}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Cybron Course Generation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # prompts
    p_prompts = subparsers.add_parser("prompts", help="Generate AI prompt files")
    p_prompts.add_argument("course_id", help="Target Course ID (e.g. 'ethical-hacking')")

    # process
    p_process = subparsers.add_parser("process", help="Process staged AI outputs")
    p_process.add_argument("course_id", help="Target Course ID")

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate an existing course")
    p_validate.add_argument("course_id", nargs="?", help="Target Course ID")
    p_validate.add_argument("--all", action="store_true", help="Validate all courses")

    # validate-raw
    p_validate_raw = subparsers.add_parser("validate-raw", help="Validate raw AI output in staging")
    p_validate_raw.add_argument("course_id", help="Target Course ID")

    # status
    p_status = subparsers.add_parser("status", help="Show course generation status")
    p_status.add_argument("course_id", help="Target Course ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "prompts":
        cmd_prompts(args)
    elif args.command == "process":
        cmd_process(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "validate-raw":
        cmd_validate_raw(args)
    elif args.command == "status":
        cmd_status(args)

if __name__ == "__main__":
    main()
