from pathlib import Path

from src.data_loader import DataLoader
from src.scheduler import Scheduler
from src.excel_exporter import ExcelExporter


def main():
    base_path = Path(__file__).parent.parent / "dados"
    loader = DataLoader(base_path)

    # 1) invoca o scheduler com os dados organizados
    sched = Scheduler(
        schedules=loader.schedules,
        subjects_by_course=loader.subjects_by_course,
        subjects_by_student=loader.subjects_by_student,
        courses_by_subject=loader.courses_by_subject,
        free_slots=loader.free_slots,
        daily_slot_ranges=loader.daily_slot_ranges,
        slots_per_day=loader.slots_per_day,
        total_slots=loader.total_slots,
    )

    exam_schedule = sched.get_exam_schedule()

    # 2) exporta para planilhas Excel
    ExcelExporter(
        schedules=loader.schedules,
        days=loader.days,
        exam_schedule=exam_schedule,
        exams_in_class=loader.exams_in_class,
        slots_per_day=loader.slots_per_day,
    )

    print("Geração de planilhas concluída.")


if __name__ == "__main__":
    main()
