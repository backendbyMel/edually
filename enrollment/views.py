from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import csv
import io
import openpyxl
from sections.models import Section
from students.models import Student
from .models import Enrollment
# Create your views here.

@login_required
def search_student(request, section_pk):
    section = get_object_or_404(Section, pk=section_pk)
    query = request.GET.get('student_name', '').strip()
    results = []

    if query:
        results = Student.objects.filter(
            Q(lrn__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).filter(added_by=request.user).order_by('last_name', 'first_name')

    return render(request, 'enrollment/search_results.html', {
        'section': section,
        'results': results,
        'query': query,
    })

@login_required
def enroll_student(request, section_pk, student_pk):
    section = get_object_or_404(Section, pk=section_pk)
    student = get_object_or_404(Student, pk=student_pk)

    enrollment, created = Enrollment.objects.get_or_create(
        section=section,
        student=student,
        added_by=request.user
    )
    if created:
        messages.success(request, f'Student {enrollment.student.lrn} is enrolled successfully')
    else:
        messages.warning(request, f'Student {enrollment.student.lrn} is already enrolled')
    
    base_url = reverse('section-detail', kwargs={'pk': section_pk})
    return redirect(f"{base_url}#enrolledStudents")

@login_required
def enroll_delete(request, section_pk, enrollment_pk):
    section = get_object_or_404(Section, pk=section_pk)
    enrollment = get_object_or_404(Enrollment, pk=enrollment_pk, section=section, added_by=request.user)
    enrollment_delete = enrollment.delete()
    if enrollment_delete:
        messages.success(request, f'Student {enrollment.student.lrn} is unenrolled from the section {enrollment.section.name} successfully')
    base_url = reverse('section-detail', kwargs={'pk': section_pk})
    return redirect(f"{base_url}#enrolledStudents")


def _sanitize(value):
    """Strip whitespace and formula injection characters from cell values."""
    if value is None:
        return ""
    value = str(value).strip()
    # Prevent formula injection (security)
    if value and value[0] in ("=", "+", "-", "@"):
        value = "'" + value
    return value
 
 
def _normalize_gender(value):
    """Accept M / Male / male / MALE → M and F / Female / female → F."""
    v = _sanitize(value).upper()
    if v in ("M", "MALE", "1"):
        return "M"
    if v in ("F", "FEMALE", "0"):
        return "F"
    return None
 
 
def _parse_xlsx(uploaded_file):
    """
    Parse an uploaded .xlsx file.
    Returns a list of dicts keyed by the header row.
    Skips the first row if it looks like the Instructions sheet
    by checking if the second row is the real header.
    """
    wb = openpyxl.load_workbook(
        uploaded_file,
        read_only=True,
        data_only=True
    )
    # Prefer a sheet named 'Students' or 'Student Data'; else use active
    ws = None
    for name in ("Students", "Student Data", "Data"):
        if name in wb.sheetnames:
            ws = wb[name]
            break
    if ws is None:
        ws = wb.active
 
    rows_raw = list(ws.iter_rows(values_only=True))
    if not rows_raw:
        return []
 
    # Find the header row — the one that contains "LRN"
    header_row_index = None
    for i, row in enumerate(rows_raw):
        row_str = [str(c).strip().upper() if c else "" for c in row]
        if "LRN" in row_str:
            header_row_index = i
            break
 
    if header_row_index is None:
        return []  # No LRN column found
 
    headers = [
        str(h).strip() if h is not None else ""
        for h in rows_raw[header_row_index]
    ]
 
    result = []
    for row in rows_raw[header_row_index + 1:]:
        if not any(row):  # skip completely empty rows
            continue
        result.append(dict(zip(headers, row)))
 
    return result
 
 
def _parse_csv(uploaded_file):
    """
    Parse an uploaded .csv file.
    Handles UTF-8 BOM (from Excel CSV export).
    """
    raw = uploaded_file.read()
    # Try UTF-8 with BOM first, then plain UTF-8, then latin-1
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            decoded = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return []
 
    reader = csv.DictReader(io.StringIO(decoded))
    return [dict(row) for row in reader]
 
 
def _get_column(row, *possible_names):
    """
    Look up a value from a row dict by trying multiple possible
    column name variations (case-insensitive).
    """
    row_lower = {k.strip().lower(): v for k, v in row.items()}
    for name in possible_names:
        val = row_lower.get(name.lower())
        if val is not None:
            return _sanitize(val)
    return ""
 
 
@login_required
def bulk_enroll_students(request, section_pk):
    """
    POST-only view.
    Accepts an .xlsx or .csv file, parses each row,
    creates the student if not yet in the teacher\'s database,
    enrolls them in the section, and skips if already enrolled.
    Redirects back to Section Detail → Students tab with a summary message.
    """
    section = get_object_or_404(Section, pk=section_pk)
 
    # Security: only the section owner can bulk-enroll
    if request.user != section.adviser:
        messages.error(
            request,
            "You do not have permission to enroll students in this section."
        )
        base_url = reverse("section-detail", kwargs={"pk": section_pk})
        return redirect(f"{base_url}#enrolledStudents")
 
    if request.method != "POST":
        base_url = reverse("section-detail", kwargs={"pk": section_pk})
        return redirect(f"{base_url}#enrolledStudents")
 
    uploaded_file = request.FILES.get("student_file")
 
    # ── Validate file presence ──
    if not uploaded_file:
        messages.error(request, "No file selected. Please choose an Excel or CSV file.")
        base_url = reverse("section-detail", kwargs={"pk": section_pk})
        return redirect(f"{base_url}#enrolledStudents")
 
    # ── Validate file type ──
    filename = uploaded_file.name.lower()
    if not (filename.endswith(".xlsx") or filename.endswith(".csv")):
        messages.error(
            request,
            f'"{uploaded_file.name}" is not a supported file type. Please upload an .xlsx or .csv file.')
        base_url = reverse("section-detail", kwargs={"pk": section_pk})
        return redirect(f"{base_url}#enrolledStudents")
 
    # ── Validate file size (max 5MB) ──
    if uploaded_file.size > 5 * 1024 * 1024:
        messages.error(
            request,
            "File is too large. Maximum allowed size is 5MB."
        )
        base_url = reverse("section-detail", kwargs={"pk": section_pk})
        return redirect(f"{base_url}#enrolledStudents")
 
    # ── Parse file ──
    try:
        if filename.endswith(".xlsx"):
            rows = _parse_xlsx(uploaded_file)
        else:
            rows = _parse_csv(uploaded_file)
    except Exception as e:
        messages.error(
            request,
            f"Could not read the file. Make sure it is a valid Excel or CSV file. "
            f"({str(e)})"
        )
        base_url = reverse("section-detail", kwargs={"pk": section_pk})
        return redirect(f"{base_url}#enrolledStudents")
 
    if not rows:
        messages.error(
            request,
            "The uploaded file appears to be empty or contains no student records. "
            "Please verify the file and try again. If you're unsure of the required format, download the template first."
        )
        base_url = reverse("section-detail", kwargs={"pk": section_pk})
        return redirect(f"{base_url}#enrolledStudents")
 
    # ── Validate max rows (prevent abuse) ──
    if len(rows) > 500:
        messages.error(
            request,
            f"The file contains {len(rows)} rows. "
            "Maximum allowed is 500 students per upload. "
            "Please split the file into smaller batches."
        )
        base_url = reverse("section-detail", kwargs={"pk": section_pk})
        return redirect(f"{base_url}#enrolledStudents")
 
    # ── Process each row ──
    created_count = 0      # new students created in DB
    enrolled_count = 0     # students newly enrolled in this section
    skipped_count = 0      # already enrolled in this section
    error_count = 0
    error_messages = []
 
    for i, row in enumerate(rows, start=2):  # start=2 because row 1 = header
 
        # ── Extract fields (support multiple column name variations) ──
        lrn = _get_column(
            row, "LRN", "Learner Reference Number", "lrn", "learner reference number"
        )
        last_name = _get_column(
            row, "Last Name", "Lastname", "last_name", "apellido"
        )
        first_name = _get_column(
            row, "First Name", "Firstname", "first_name", "nombre"
        )
        middle_name = _get_column(
            row, "Middle Name", "Middlename", "middle_name", "middle initial"
        )
        gender_raw = _get_column(
            row, "Gender", "Sex", "sex/gender"
        )
        dob_raw = _get_column(
            row, "Date of Birth", "Birthday", "Birthdate",
            "date_of_birth", "dob"
        )
        
 
        # ── Skip completely empty rows ──
        if not lrn and not last_name and not first_name:
            continue
 
        # ── Validate required fields ──
        row_errors = []
 
        if not lrn:
            row_errors.append("LRN is missing")
        elif not lrn.isdigit():
            row_errors.append(f'LRN "{lrn}" must contain digits only')
        elif len(lrn) != 12:
            row_errors.append(
                f'LRN "{lrn}" must be exactly 12 digits (got {len(lrn)})'
            )
 
        if not last_name:
            row_errors.append("Last Name is missing")
 
        if not first_name:
            row_errors.append("First Name is missing")
 
        gender = _normalize_gender(gender_raw)
        if not gender:
            row_errors.append(
                f'Gender "{gender_raw}" is invalid — use M or F'
            )
 
        if row_errors:
            error_count += 1
            error_messages.append(
                f"Row {i} ({first_name} {last_name}): "
                + " | ".join(row_errors)
            )
            continue
 
        # ── Parse date of birth (flexible) ──
        parsed_dob = None
        if dob_raw:
            from datetime import datetime
            for fmt in (
                "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
                "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y"
            ):
                try:
                    parsed_dob = datetime.strptime(dob_raw, fmt).date()
                    break
                except ValueError:
                    continue
 
        # ── Get or create Student ──
        try:
            student, was_created = Student.objects.get_or_create(
                lrn=lrn,
                added_by=request.user,
                defaults={
                    "last_name": last_name.upper(),
                    "first_name": first_name.upper(),
                    "middle_name": middle_name.upper() if middle_name else "",
                    "gender": gender,
                    "date_of_birth": parsed_dob,
                }
            )
            if was_created:
                created_count += 1
 
        except Exception as e:
            error_count += 1
            error_messages.append(
                f"Row {i} ({first_name} {last_name}): "
                f"Could not save student — {str(e)}"
            )
            continue
 
        # ── Get or create Enrollment ──
        try:
            enrollment, was_enrolled = Enrollment.objects.get_or_create(
                student=student,
                section=section,
                defaults={"added_by": request.user}
            )
            if was_enrolled:
                enrolled_count += 1
            else:
                skipped_count += 1
 
        except Exception as e:
            error_count += 1
            error_messages.append(
                f"Row {i} ({first_name} {last_name}): "
                f"Could not enroll student — {str(e)}"
            )
            continue
 
    # ── Build summary message ──
    if enrolled_count == 0 and created_count == 0 and error_count == 0:
        if skipped_count > 0:
            messages.info(
                request,
                f"All {skipped_count} student(s) in the file are already "
                f"enrolled in this section. No changes were made."
            )
        else:
            messages.warning(
                request,
                "No students were processed. "
                "The file may be empty or use unrecognized column headers."
            )
    else:
        parts = []
        if enrolled_count > 0:
            parts.append(f"{enrolled_count} student(s) enrolled successfully")
        if created_count > 0:
            parts.append(f"{created_count} new student record(s) created")
        if skipped_count > 0:
            parts.append(
                f"{skipped_count} already enrolled (skipped)"
            )
        if error_count > 0:
            parts.append(f"{error_count} row(s) had errors")
 
        summary = " · ".join(parts)
 
        if error_count > 0 and enrolled_count == 0:
            messages.error(request, f"Import failed: {summary}")
        elif error_count > 0:
            messages.warning(request, f"Import complete with issues: {summary}")
        else:
            messages.success(request, f"Import complete: {summary}")
 
    # ── Show individual error details (max 5) ──
    for msg in error_messages[:5]:
        messages.warning(request, msg)
    if len(error_messages) > 5:
        messages.warning(
            request,
            f"...and {len(error_messages) - 5} more row(s) with errors. "
            f"Download the template, fix the errors, and re-upload."
        )
 
    base_url = reverse("section-detail", kwargs={"pk": section_pk})
    return redirect(f"{base_url}#enrolledStudents")
