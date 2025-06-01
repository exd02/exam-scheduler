import flet as ft
import json
from pathlib import Path
from typing import Dict, List, Set

from src.json_operations import confirm_and_save


class GUIScheduler:
    """
    Interface Flet para marcar exames em sala de aula:
    - Carrega Horarios.json e Dias.json de 'dados/'
    - Permite marcar quais disciplinas terão prova em cada slot
    - Salva em ExamesEmAula.json
    """

    def __init__(self):
        self.page: ft.Page | None = None
        self.selections: Dict[str, Set[int]] = {}
        self.current_slots: List[List[int]] = []
        self.current_course: str | None = None

    @staticmethod
    def _load_static_data() -> tuple[Dict[str, Dict[str, List[int]]], List[str]]:
        """
        Lê Horarios.json e Dias.json em 'dados/'.
        Retorna (horarios, days).
        """
        horarios_path = Path("dados/Horarios.json")
        dias_path = Path("dados/Dias.json")

        if not horarios_path.exists() or not dias_path.exists():
            raise FileNotFoundError("dados/Horarios.json ou dados/Dias.json não encontrado(s).")

        horarios = json.loads(horarios_path.read_text(encoding="utf-8"))
        days = json.loads(dias_path.read_text(encoding="utf-8"))
        return horarios, days

    def _build_ui(self, page: ft.Page):
        self.page = page
        page.title = "Agendador de Exames em Aula"
        page.window.maximized = True
        page.padding = 20

        horarios, days = self._load_static_data()
        cursos = list(horarios.keys())
        num_days = len(days)

        # Cabeçalho e instruções
        page.add(
            ft.Text("Agendador de Exames em Aula", size=30, weight=ft.FontWeight.BOLD),
            ft.Text("Gerencie quais disciplinas terão prova em sala", size=20),
            ft.Text(
                "Clique no slot que corresponde à aula da disciplina para marcar o exame. "
                "O texto ficará vermelho.",
                size=14
            ),
            ft.Divider(thickness=1),
        )

        # Dropdown de cursos e botões
        course_dropdown = ft.Dropdown(
            width=200,
            options=[ft.dropdown.Option(key=c, text=c) for c in cursos],
            value=cursos[0] if cursos else None,
        )
        load_button = ft.ElevatedButton("Carregar Quadro", height=45)
        export_button = ft.ElevatedButton("Exportar configuração", height=40)
        export_button.disabled = True

        def export_config_click(e: ft.ControlEvent):
            if not self.current_course:
                return

            config_path = Path("dados/ExamesEmAula.json")
            if config_path.exists():
                all_configs = json.loads(config_path.read_text(encoding="utf-8"))
            else:
                all_configs = {}

            all_configs[self.current_course] = {
                disc: list(idxs) for disc, idxs in self.selections.items()
            }

            confirm_and_save(
                page=page,
                output_file=str(config_path),
                data=all_configs,
                success_message="Exportado para 'dados/ExamesEmAula.json' com sucesso!"
            )

        export_button.on_click = export_config_click

        page.add(
            ft.Row([ft.Text("Curso:"), course_dropdown, load_button, export_button], spacing=10),
            ft.Divider(thickness=1),
        )

        # Tabela de horários
        columns = [ft.DataColumn(label=ft.Text(d.upper())) for d in days]
        data_table = ft.DataTable(columns=columns, rows=[], border=ft.border.all(1, ft.Colors.BLUE))
        scrollable = ft.Row(controls=[data_table], expand=True, scroll=ft.ScrollMode.ALWAYS)

        def refresh_rows():
            if not self.current_slots:
                return

            SLOTS_PER_DAY = len(self.current_slots[0])
            new_rows: List[ft.DataRow] = []

            for period in range(SLOTS_PER_DAY):
                cells: List[ft.DataCell] = []
                for day_idx in range(num_days):
                    idx = day_idx * SLOTS_PER_DAY + period
                    value = self.current_slots[day_idx][period]
                    txt = ft.Text(str(value))

                    if value != 0:
                        if value in self.selections and idx in self.selections[value]:
                            txt.color = ft.Colors.RED
                        elif value in self.selections:
                            txt.color = ft.Colors.GREY_800

                        def on_tap(e: ft.ControlEvent, disc=value, idx=idx):
                            sel = self.selections.setdefault(disc, set())
                            if idx in sel:
                                del self.selections[disc]
                            else:
                                self.selections[disc] = {idx}
                            refresh_rows()

                        cell_content = ft.GestureDetector(content=txt, on_tap=on_tap)
                    else:
                        cell_content = txt

                    cells.append(ft.DataCell(cell_content))

                new_rows.append(ft.DataRow(cells=cells))

            data_table.rows = new_rows
            page.update()

        def carregar_quadro(e: ft.ControlEvent):
            nome = course_dropdown.value
            self.current_course = nome
            grade = horarios.get(nome, {})
            self.current_slots = [grade.get(d, [0] * 8) for d in days]
            self.selections.clear()

            config_path = Path("dados/ExamesEmAula.json")
            if config_path.exists():
                all_configs = json.loads(config_path.read_text(encoding="utf-8"))
                if nome in all_configs:
                    for disc, idxs in all_configs[nome].items():
                        self.selections[disc] = set(idxs)

            export_button.disabled = False
            page.add(scrollable)
            refresh_rows()

        load_button.on_click = carregar_quadro

    def run(self):
        ft.app(target=self._build_ui)
