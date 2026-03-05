from datetime import datetime, timedelta
from database.db_connection import get_db_connection

DAYS_PER_CHAPTER = 7
DEFAULT_CAPACITY_HOURS = 6.0


def _priority_from_days(days_remaining: int) -> str:
    if days_remaining <= 3:
        return "High"
    if days_remaining <= 10:
        return "Medium"
    return "Low"


def _progress_pct(topics: list) -> int:
    if not topics:
        return 0
    completed = sum(1 for t in topics if t["is_completed"])
    return round((completed / len(topics)) * 100)


def get_study_plan_dashboard(current_user):
    """
    Called from route with @token_required decorator.
    current_user = decoded JWT payload → { user_id, username, role }

    All DB operations go through Stored Procedures.
    Date logic: globally sequential across all subjects —
    Subject 2 chapters start right after Subject 1 ends.
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            return {"status": "error", "code": 401, "message": "Invalid token payload", "data": {}}

        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ── 1. Academic profile ── SP: sp_get_student_profile ────────────────
        cursor.callproc("sp_get_student_profile", (user_id,))
        profile = None
        for result in cursor.stored_results():
            profile = result.fetchone()

        if not profile:
            conn.close()
            return {"status": "error", "code": 404,
                    "message": "Active academic profile not found", "data": {}}

        profile_id   = profile["profile_id"]
        student_class = profile["class_name"]   # ✅ actual student class e.g. "12"
        today         = datetime.utcnow().date()

        # Global date cursor — advances sequentially across ALL subjects & chapters
        global_date_cursor = profile["register_date"].date()
        plan_start         = profile["register_date"].date()   # kept for stats

        # ── 2. Selected subjects ── SP: sp_get_student_subjects ──────────────
        cursor.callproc("sp_get_student_subjects", (profile_id,))
        subjects = []
        for result in cursor.stored_results():
            subjects = result.fetchall()

        if not subjects:
            conn.close()
            return {"status": "error", "code": 404,
                    "message": "No subjects selected for this student", "data": {}}

        # ── Per-subject loop ──────────────────────────────────────────────────
        subject_wise_plan   = []
        total_chapters      = 0
        total_hours_all     = 0.0
        total_remaining_all = 0.0

        for subj in subjects:
            subject_id          = subj["subject_id"]
            subject_name        = subj["subject_name"]
            subject_class_grade = subj["subject_class_grade"]

            # ── 3. Chapters ── SP: sp_get_chapters_by_subject ────────────────
            cursor.callproc("sp_get_chapters_by_subject", (subject_id,))
            raw_chapters = []
            for result in cursor.stored_results():
                raw_chapters = result.fetchall()

            if not raw_chapters:
                continue

            chapters_output = []
            subj_total_hrs  = 0.0
            subj_remaining  = 0.0
            subj_start_date = global_date_cursor   # first chapter of this subject

            for ch in raw_chapters:
                chapter_id   = ch["chapter_id"]
                chapter_name = ch["chapter_name"]

                # ✅ Global sequential dates
                start_date         = global_date_cursor
                end_date           = global_date_cursor + timedelta(days=DAYS_PER_CHAPTER - 1)
                global_date_cursor = end_date + timedelta(days=1)

                days_remaining = (end_date - today).days
                priority       = _priority_from_days(days_remaining)

                # ── 4. Topics ── SP: sp_get_topics_by_chapter ────────────────
                cursor.callproc("sp_get_topics_by_chapter", (chapter_id,))
                raw_topics = []
                for result in cursor.stored_results():
                    raw_topics = result.fetchall()

                # ── 5. Completed topics ── SP: sp_get_completed_topics ────────
                cursor.callproc("sp_get_completed_topics", (user_id, profile_id, chapter_id))
                completed_set = set()
                for result in cursor.stored_results():
                    completed_set = {r["topic_id"] for r in result.fetchall()}

                topics_output = []
                for t in raw_topics:
                    is_done = t["topic_id"] in completed_set
                    topics_output.append({
                        "topic_id":        t["topic_id"],
                        "topic_name":      t["topic_name"],
                        "estimated_hours": 1.0,
                        "is_completed":    is_done,
                        "status":          "Completed" if is_done else "Pending"
                    })

                progress_pct    = _progress_pct(topics_output)
                estimated_hours = float(len(topics_output))
                remaining_hours = sum(1.0 for t in topics_output if not t["is_completed"])

                subj_total_hrs += estimated_hours
                subj_remaining += remaining_hours
                total_chapters += 1

                ch_status = (
                    "Completed"   if progress_pct == 100 else
                    "In Progress" if progress_pct > 0   else
                    "Pending"
                )

                # ── 6. Upsert chapter ── SP: sp_upsert_plan_chapter ──────────
                cursor.callproc("sp_upsert_plan_chapter", (
                    user_id, profile_id, subject_id,
                    chapter_id, chapter_name, student_class,   # ✅ student's actual class
                    priority, ch_status, progress_pct,
                    estimated_hours, remaining_hours,
                    start_date, end_date, DAYS_PER_CHAPTER
                ))
                plan_chapter_id = 0
                for result in cursor.stored_results():
                    row = result.fetchone()
                    if row:
                        plan_chapter_id = row["plan_chapter_id"]

                # ── 7. Upsert topics ── SP: sp_upsert_plan_topic ─────────────
                for t in topics_output:
                    cursor.callproc("sp_upsert_plan_topic", (
                        plan_chapter_id, user_id, profile_id,
                        subject_id, chapter_id,
                        t["topic_id"], t["topic_name"],
                        t["estimated_hours"],
                        t["status"], 1 if t["is_completed"] else 0
                    ))
                    # consume result set to keep connection clean
                    for _ in cursor.stored_results():
                        pass

                start_str = start_date.strftime("%d %b")
                end_str   = end_date.strftime("%d %b")
                range_str = f"{start_date.strftime('%d')}-{end_date.strftime('%d %b')}'{end_date.strftime('%y')}"

                chapters_output.append({
                    "chapter_id":                chapter_id,
                    "chapter_name":              chapter_name,
                    "start_date":                start_str,
                    "end_date":                  end_str,
                    "start_end_date":            range_str,
                    "estimated_hours":           estimated_hours,
                    "remaining_hours":           remaining_hours,
                    "extra_practice_needed":     0.0,
                    "priority":                  priority,
                    "priority_locked_by_teacher": False,
                    "progress_percentage":       progress_pct,
                    "status":                    ch_status,
                    "target_completion_days":    DAYS_PER_CHAPTER,
                    "topics":                    topics_output
                })

            # ── 8. Upsert subject plan ── SP: sp_upsert_subject_plan ──────────
            target_days = len(raw_chapters) * DAYS_PER_CHAPTER
            plan_end    = subj_start_date + timedelta(days=target_days)
            days_left   = max((plan_end - today).days, 0)

            cursor.callproc("sp_upsert_subject_plan", (
                user_id, profile_id, subject_id, student_class,   # ✅ student's actual class
                profile["academic_year"],
                subj_start_date, subj_total_hrs, subj_remaining,
                days_left, target_days
            ))
            for _ in cursor.stored_results():
                pass

            total_hours_all     += subj_total_hrs
            total_remaining_all += subj_remaining

            subject_wise_plan.append({
                "subject_id":              subject_id,
                "subject_name":            subject_name,
                "total_subject_hours":     subj_total_hrs,
                "remaining_subject_hours": subj_remaining,
                "chapters":                chapters_output
            })

        conn.commit()
        conn.close()

        # ── Final stats ───────────────────────────────────────────────────────
        overall_target_days = total_chapters * DAYS_PER_CHAPTER
        overall_plan_end    = plan_start + timedelta(days=overall_target_days)
        days_left_overall   = max((overall_plan_end - today).days, 0)

        pending_count   = sum(
            1 for sp in subject_wise_plan
            for ch in sp["chapters"]
            if ch["status"] != "Completed"
        )
        completed_count = total_chapters - pending_count

        return {
            "status":  "success",
            "code":    200,
            "message": "Dashboard loaded successfully.",
            "data": {
                "stats": {
                    "student_name":           profile["student_name"],
                    "board_id":               profile["board_id"],
                    "board_name":             profile["board_name"],
                    "class_id":               profile["class_id"],
                    "class_name":             profile["class_name"],
                    "institute_id":           profile["school_id"],
                    "institute_name":         profile["institute_name"],
                    "chapters_assigned":      total_chapters,
                    "completed_count":        completed_count,
                    "pending_count":          pending_count,
                    "days_left":              days_left_overall,
                    "target_completion_days": overall_target_days,
                    "total_hours_remaining":  total_remaining_all,
                    "user_pref_capacity":     DEFAULT_CAPACITY_HOURS,
                    "subject_names":          [s["subject_name"] for s in subjects]
                },
                "subject_wise_plan": subject_wise_plan
            }
        }

    except Exception as e:
        return {"status": "error", "code": 500, "message": str(e), "data": {}}