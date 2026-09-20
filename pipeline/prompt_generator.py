import os
from pathlib import Path

def generate_prompts_for_course(course_id: str, staging_dir: str) -> int:
    """Generates the prompt instructions for the AI agent."""
    prompts_dir = Path(staging_dir) / course_id / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    # Read the base template
    base_template_path = Path("course_generation_prompt.txt")
    if not base_template_path.exists():
        print(f"Error: {base_template_path} not found.")
        return 0
        
    with open(base_template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
        
    # Replace placeholders
    course_name = course_id.replace("-", " ").title()
    prompt_content = template_content.replace("COURSE_NAME", course_name)
    prompt_content = prompt_content.replace("Course id:", f"Course id: {course_id}")
    prompt_content = prompt_content.replace("[course_id]", course_id)
    
    # Write the main prompt
    main_prompt_path = prompts_dir / "01_course_generation.txt"
    with open(main_prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt_content)
        
    return 1

def generate_master_instructions(course_id: str, staging_dir: str) -> str:
    """Generates the master instruction file for the agent."""
    base_dir = Path(staging_dir) / course_id
    raw_dir = base_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    instructions_path = base_dir / "INSTRUCTIONS.md"
    
    content = f"""# Course Generation: {course_id}

You are tasked with generating the full course '{course_id}'.

## Agent Workflow
To ensure accuracy, you must track your own progress and constantly validate your generated files.
1. **Initialize Task Tracker:** Create a `task.md` file in `staging/{course_id}/` with a checklist of all components to generate (e.g. Chapters, Lessons, Quizzes, Tasks, Side Quests, Projects).
2. **Update Progress:** As you complete each chunk of work, mark it as `[x]` in your `task.md`.
3. **Validate Your Work:** After generating each logical group of files (e.g. after generating all quizzes, or all side quests), you MUST run the validation script from the terminal to catch errors immediately:
   `./generate_pipeline.py validate-raw "{course_id}"`
4. **Fix Errors:** If the validation command returns errors, fix the JSON schemas before moving to the next item on your checklist.

## Generation Steps
1. **Read Prompt:** Read the exact formatting requirements in `prompts/01_course_generation.txt`.
2. **Generate Continuously:** Follow the rules to generate the entire course.
3. **Save Files:** Save the generated JSON files into the `raw/` directory (e.g. `raw/chapters.json`, `raw/quizzes/ch_1.json`, `raw/projects/project1.json`).

**Important Requirements:**
- Make sure all generated files are valid JSON without any markdown code blocks wrapped around them when you save them to disk.
"""
    with open(instructions_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return str(instructions_path)
