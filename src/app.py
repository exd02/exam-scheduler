from pathlib import Path

from src.data_loader import DataLoader
from src.scheduler import Scheduler
from src.excel_exporter import ExcelExporter
from src.gui_recovery_extractor import GUIRecoveryExtractor
from src.gui_scheduler import GUIScheduler


def run_scheduling():
    """
    Carrega todos os JSONs de 'dados/' → monta o modelo CP-SAT →
    gera as planilhas em 'planilhas/'.
    """
    base_path = Path(__file__).parent.parent / "dados"
    loader = DataLoader(base_path)

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

    ExcelExporter(
        schedules=loader.schedules,
        days=loader.days,
        exam_schedule=exam_schedule,
        exams_in_class=loader.exams_in_class,
        slots_per_day=loader.slots_per_day,
    )

    print("⏳ Planilhas de horário geradas em 'planilhas/' com sucesso.")


def main():
    print("==============================================")
    print("  1 → Construir AlunosEmRecuperacao.json (GUI)")
    print("  2 → Agendar Exames em Sala (GUI)")
    print("  3 → Construir planilhas de horário (Excel)")
    print("==============================================")
    choice = input("Digite 1, 2 ou 3 e pressione Enter: ").strip()

    if choice == "1":
        gui_recovery = GUIRecoveryExtractor()
        gui_recovery.run()
    elif choice == "2":
        gui_scheduler = GUIScheduler()
        gui_scheduler.run()
    elif choice == "3":
        run_scheduling()
    else:
        print("Opção inválida. Rode novamente e digite '1', '2' ou '3'.")


if __name__ == "__main__":
    main()