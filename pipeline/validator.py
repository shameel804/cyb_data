import json
from pathlib import Path

class ValidationReport:
    def __init__(self):
        self.errors = []
        
    def add_error(self, msg: str):
        self.errors.append(msg)
        
    def has_errors(self) -> bool:
        return len(self.errors) > 0

def validate_json_file(file_path: Path, report: ValidationReport, strict_missing: bool = True) -> dict:
    if not file_path.exists():
        if strict_missing:
            report.add_error(f"Missing file: {file_path}")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        report.add_error(f"Invalid JSON in {file_path}: {e}")
        return None

def check_required_keys(data: dict, required_keys: list, file_path: Path, report: ValidationReport, context: str = ""):
    if not isinstance(data, dict):
        report.add_error(f"{file_path}: {context} should be a JSON object")
        return False
    
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        report.add_error(f"{file_path}: {context} missing required key(s) {missing_keys}")
        return False
    return True

def validate_course(course_dir: Path, course_id: str, strict_missing: bool = True) -> ValidationReport:
    report = ValidationReport()
    
    # 1. Check chapters.json
    chapters_file = course_dir / "chapters.json"
    chapters_data = validate_json_file(chapters_file, report, strict_missing)
    
    chapter_ids = []
    if chapters_data:
        if "chapters" not in chapters_data:
            report.add_error(f"{chapters_file} missing 'chapters' array.")
        else:
            for i, ch in enumerate(chapters_data["chapters"]):
                if check_required_keys(ch, ["id", "languageId", "title", "description"], chapters_file, report, f"Chapter {i}"):
                    chapter_ids.append(ch["id"])
                    if ch["languageId"] != course_id:
                        report.add_error(f"{chapters_file}: Chapter {ch['id']} has incorrect languageId: {ch['languageId']}")
    
    # 2. Check Lessons
    lessons_dir = course_dir / "lessons"
    for ch_id in chapter_ids:
        ch_lesson_dir = lessons_dir / ch_id
        index_file = ch_lesson_dir / "index.json"
        
        index_data = validate_json_file(index_file, report, strict_missing)
        lesson_ids = []
        if index_data and "lessons" in index_data:
            for i, l in enumerate(index_data["lessons"]):
                if check_required_keys(l, ["id", "title", "description"], index_file, report, f"Lesson {i} in {ch_id}"):
                    lesson_ids.append(l["id"])
                    
        # Check individual lesson files
        for l_id in lesson_ids:
            l_file = ch_lesson_dir / f"{l_id}.json"
            l_data = validate_json_file(l_file, report, strict_missing)
            if l_data:
                if check_required_keys(l_data, ["id", "chapterId", "title", "description", "slides"], l_file, report):
                    if l_data["chapterId"] != ch_id:
                        report.add_error(f"{l_file}: Lesson has incorrect chapterId: {l_data['chapterId']}")
                    
                    for j, slide in enumerate(l_data["slides"]):
                        check_required_keys(slide, ["id", "type", "title", "content"], l_file, report, f"Slide {j}")
                        
        # Check tasks if tasks.json exists
        tasks_file = ch_lesson_dir / "tasks.json"
        if tasks_file.exists():
            tasks_data = validate_json_file(tasks_file, report, strict_missing)
            if tasks_data and "tasks" in tasks_data:
                for j, t in enumerate(tasks_data["tasks"]):
                    if check_required_keys(t, ["id", "title", "description", "estimatedMinutes"], tasks_file, report, f"Task {j}"):
                        t_id = t["id"]
                        t_file = ch_lesson_dir / "tasks" / f"{t_id}.json"
                        t_detail = validate_json_file(t_file, report, strict_missing)
                        if t_detail:
                            check_required_keys(t_detail, ["id", "title", "description", "estimatedMinutes", "problemStatement"], t_file, report)

    # 3. Check Quizzes
    quizzes_dir = course_dir / "quizzes"
    for ch_id in chapter_ids:
        quiz_file = quizzes_dir / f"{ch_id}.json"
        quiz_data = validate_json_file(quiz_file, report, strict_missing)
        if quiz_data:
            if check_required_keys(quiz_data, ["id", "chapterId", "title", "questions"], quiz_file, report):
                if quiz_data["chapterId"] != ch_id:
                    report.add_error(f"{quiz_file}: Quiz has incorrect chapterId: {quiz_data['chapterId']}")
                for j, q in enumerate(quiz_data["questions"]):
                    if check_required_keys(q, ["id", "type", "question", "options", "explanation", "xpReward", "difficulty"], quiz_file, report, f"Question {j}"):
                        for k, opt in enumerate(q["options"]):
                            if isinstance(opt, dict):
                                check_required_keys(opt, ["id", "text"], quiz_file, report, f"Question {j} Option {k}")

    # 4. Check Side Quests
    sq_file = course_dir / "side_quests.json"
    if sq_file.exists():
        sq_data = validate_json_file(sq_file, report, strict_missing)
        if sq_data and isinstance(sq_data, list):
            for i, sq in enumerate(sq_data):
                if check_required_keys(sq, ["id", "title", "triggerChapterIndex"], sq_file, report, f"Side Quest {i}"):
                    sq_id = sq["id"]
                    sq_detail_file = course_dir / "side_quests" / f"{sq_id}.json"
                    sq_detail = validate_json_file(sq_detail_file, report, strict_missing)
                    if sq_detail:
                        check_required_keys(sq_detail, ["id", "title", "triggerChapterIndex", "questions"], sq_detail_file, report)
                        if "questions" in sq_detail:
                            for j, q in enumerate(sq_detail["questions"]):
                                check_required_keys(q, ["id", "type", "question", "options", "explanation", "xpReward", "difficulty"], sq_detail_file, report, f"Question {j}")
        elif sq_data:
             report.add_error(f"{sq_file} should be a JSON Array.")

    # 5. Check Projects
    proj_file = course_dir / "projects.json"
    if proj_file.exists():
        proj_data = validate_json_file(proj_file, report, strict_missing)
        if proj_data and "projects" in proj_data:
            for i, p in enumerate(proj_data["projects"]):
                if check_required_keys(p, ["id", "title", "description", "difficulty", "estimatedHours"], proj_file, report, f"Project {i}"):
                    p_id = p["id"]
                    p_detail_file = course_dir / "projects" / f"{p_id}.json"
                    p_detail = validate_json_file(p_detail_file, report, strict_missing)
                    if p_detail:
                        check_required_keys(p_detail, ["id", "title", "description", "difficulty", "estimatedHours", "problemStatement"], p_detail_file, report)

    return report
