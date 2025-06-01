import os
import xlsxwriter
from pathlib import Path
from typing import Dict, List

class ExcelExporter:
    """
    Recebe:
    - schedules (dados brutos de ocupação: indica 0 para livre, 1 para ocupado)
    - days (lista de dias da semana)
    - exam_schedule (lista de disciplinas agendadas por slot)
    - exams_in_class (disciplinas com exame em aula para exibir "1(subj)")
    E gera um arquivo .xlsx por curso na pasta 'planilhas/'.
    """

    def __init__(
        self,
        schedules: Dict[str, Dict[str, List[int]]],
        days: List[str],
        exam_schedule: Dict[str, List[List[str]]],
        exams_in_class: Dict[str, Dict[str, List[int]]],
        slots_per_day: int,
    ):
        self.schedules = schedules
        self.days = days
        self.exam_schedule = exam_schedule
        self.exams_in_class = exams_in_class
        self.slots_per_day = slots_per_day

        self.TIME_LABELS = [
            "07:00 – 07:55",
            "07:55 – 08:50",
            "09:10 – 10:05",
            "10:05 – 11:00",
            "13:00 – 13:55",
            "13:55 – 14:50",
            "15:10 – 16:05",
            "16:05 – 17:00",
        ]  # Deve ter len = slots_per_day

        self._export_all()

    def _export_all(self):
        os.makedirs("planilhas", exist_ok=True)

        for curso in self.schedules:
            self._export_por_curso(curso)

    def _export_por_curso(self, curso: str):
        wb = xlsxwriter.Workbook(f"planilhas/{curso}.xlsx")
        ws = wb.add_worksheet("grade")

        # ── formatos ─────────────────────────────────────────
        hdr_day = wb.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "bg_color": "#D9D9D9"
        })
        hdr_time = wb.add_format({
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "bg_color": "#D9D9D9"
        })
        fmt_cell = wb.add_format({
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "text_wrap": True
        })
        fmt_num = wb.add_format({
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "num_format": "0"
        })

        # ── largura de colunas e altura de linhas ───────────
        ws.set_column(0, 0, 15)               # primeira coluna para TIME_LABELS
        ws.set_column(1, len(self.days), 22)  # uma coluna para cada dia
        ws.set_row(0, 25)                     # altura da linha de cabeçalho

        # ── cabeçalho (dias) ────────────────────────────────
        ws.write(0, 0, "")  # canto superior esquerdo vazio
        for col, dia in enumerate(self.days, start=1):
            ws.write(0, col, dia.capitalize(), hdr_day)

        # ── TIME_LABELS na primeira coluna ──────────────────
        for row, label in enumerate(self.TIME_LABELS, start=1):
            ws.write(row, 0, label, hdr_time)

        # ── preencher células ───────────────────────────────
        total_slots = len(self.days) * self.slots_per_day
        for dia_idx, dia in enumerate(self.days):
            for periodo_idx in range(self.slots_per_day):
                row = periodo_idx + 1
                col = dia_idx + 1
                slot_index = dia_idx * self.slots_per_day + periodo_idx

                # 1) verifica se é "exame em aula" para este curso
                celula_exame_aula = None
                if curso in self.exams_in_class:
                    for subj, slots in self.exams_in_class[curso].items():
                        if slot_index in slots:
                            celula_exame_aula = f"1({subj})"
                            break

                if celula_exame_aula:
                    ws.write(row, col, celula_exame_aula, fmt_cell)
                    continue

                # 2) se não for exame em aula, verifica se há exame agendado
                exames_aqui = self.exam_schedule[curso][slot_index]
                if exames_aqui:
                    ws.write(row, col, " | ".join(exames_aqui), fmt_cell)
                else:
                    # 3) escreve 0/1 conforme schedules original
                    raw_flag = self.schedules[curso][dia][periodo_idx]
                    busy_flag = 0 if raw_flag == 0 else 1
                    ws.write_number(row, col, busy_flag, fmt_num)

        wb.close()
