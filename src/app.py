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
    base_path = Path(__file__).parent.parent / "dados"
    dias_path = base_path / "Dias.json"
    horarios_path = base_path / "Horarios.json"

    if not dias_path.exists() or not horarios_path.exists():
        print("Erro: os arquivos 'dados/Dias.json' e 'dados/Horarios.json' devem existir antes de executar o programa.")
        return

    while True:
        print("==============================================")
        print("  1 → Construir AlunosEmRecuperacao.json (GUI)")
        print("  2 → Agendar Exames em Sala (GUI)")
        print("  3 → Construir planilhas de horário (Excel)")
        print("  q → Sair")
        print("==============================================")
        choice = input("Digite 1, 2, 3 ou q e pressione Enter: ").strip()

        if choice == "1":
            gui_recovery = GUIRecoveryExtractor()
            gui_recovery.run()
            break
        elif choice == "2":
            try:
                gui_scheduler = GUIScheduler()
                gui_scheduler.run()
                break
            except Exception as e:
                print(f"Erro ao executar opção 2: {e}")
        elif choice == "3":
            try:
                run_scheduling()
                break
            except Exception as e:
                print(f"Erro ao executar opção 3: {e}")
        elif choice.lower() == "q":
            break
        else:
            print("Opção inválida.")



if __name__ == "__main__":
    main()