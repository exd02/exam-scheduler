import flet as ft
import os
import re
import json
from pathlib import Path

from src.recovery_utils import extract_json, merge_jsons

GREY_C = "#2A2D33"
HEADER_RE = re.compile(r'^[A-Z]+(?:,[A-Z]+)*$')


class GUIRecoveryExtractor:
    """
    Interface Flet para extrair e mesclar planilhas .xlsx de alunos em recuperação:
    - Permite selecionar múltiplos arquivos .xlsx
    - Solicita cabeçalhos e linhas inicial/final
    - Cria ou sobrescreve 'dados/AlunosEmRecuperacao.json'
    """

    def __init__(self):
        self.page: ft.Page | None = None
        self.txt_path: ft.TextField | None = None
        self.initial_page: ft.Column | None = None
        self.after_file_selected: ft.Column | None = None
        self.sheet_containers: list[ft.Container] = []

    def _on_header_focus(self, e: ft.ControlEvent):
        e.control.border_color = ft.Colors.BLUE_800
        e.page.update()

    def save(self, output_file: str, merged: dict[str, any]):
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=4)

        self.page.open(
            ft.SnackBar(ft.Text(f"Exportado '{output_file}' com sucesso!"), bgcolor=ft.Colors.GREEN_100)
        )

    def _confirm_and_save(self, page: ft.Page, output_file: str, merged: dict):
        """
        Se output_file existir:
          - exibe diálogo de confirmação
          - se "Sim", chama save() e exibe SnackBar
          - se "Não", fecha diálogo
        Se output_file não existir:
          - chama save() diretamente e exibe SnackBar
        """
        def _show_success_snackbar(msg: str):
            page.open(ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.GREEN_100))

        if Path(output_file).exists():
            def _overwrite(e: ft.ControlEvent):
                self.save(output_file, merged)
                dlg.open = False
                page.update()
                _show_success_snackbar(f"'{output_file}' sobrescrito com sucesso!")

            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmação"),
                content=ft.Text(
                    f'Você tem certeza que quer sobrescrever o arquivo "{output_file}" já existente?'
                ),
                actions=[
                    ft.TextButton("Sim", on_click=_overwrite),
                    ft.TextButton(
                        "Não",
                        on_click=lambda e: (
                            setattr(dlg, "open", False),
                            page.update()
                        )
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.open(dlg)
        else:
            self.save(output_file, merged)
            _show_success_snackbar(f"Exportado '{output_file}' com sucesso!")

        page.update()

    def make_sheet_info(self, filename: str) -> ft.Container:
        """
        Monta o container que solicita:
        - cabeçalhos (ex: "A,B,C")
        - linha inicial
        - linha final
        """
        txt_headers = ft.TextField(
            value="F,J,N,R,V,Z,AD,AH,AL,AP,AT,AX,BB,BF,BJ",
            expand=True,
            border_color=ft.Colors.BLUE_800,
            focused_border_color=ft.Colors.BLUE,
            on_focus=lambda e: self._on_header_focus(e),
        )
        txt_first = ft.TextField(
            value="3",
            width=60,
            border_color=ft.Colors.BLUE_800,
            focused_border_color=ft.Colors.BLUE,
            on_focus=lambda e: self._on_header_focus(e),
        )
        txt_last = ft.TextField(
            value="39",
            width=60,
            border_color=ft.Colors.BLUE_800,
            focused_border_color=ft.Colors.BLUE,
            on_focus=lambda e: self._on_header_focus(e),
        )

        container = ft.Container(
            ft.Column(
                [
                    ft.Text(f"{filename}:", weight="bold"),
                    ft.Row(
                        [
                            ft.Text("Cabeçalhos:"),
                            txt_headers,
                            ft.Text("Linha primeiro Aluno:"),
                            txt_first,
                            ft.Text("Linha último Aluno:"),
                            txt_last,
                        ],
                        spacing=10,
                    ),
                ],
                spacing=15,
            ),
            padding=15,
            border=ft.border.all(1, GREY_C),
            border_radius=5,
            expand=True,
        )
        container.txt_fields = [txt_headers, txt_first, txt_last]
        return container

    def _on_file_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.txt_path.value = ", ".join(f.path for f in e.files)
            self.txt_path.border_color = ft.Colors.BLUE_800
            self.page.update()

    def _build_ui(self, page: ft.Page):
        self.page = page
        page.title = "Extrator JSON de Alunos em Recuperação"
        page.theme_mode = "dark"
        page.window.width = 790
        page.window.height = 265
        page.padding = 20

        self.txt_path = ft.TextField(
            label="Selecionar Planilhas:",
            expand=True,
            read_only=True,
            border_color=ft.Colors.BLUE_800,
            focused_border_color=ft.Colors.BLUE,
        )

        file_picker = ft.FilePicker(on_result=self._on_file_result)
        page.overlay.append(file_picker)

        btn_upload = ft.ElevatedButton(
            text="Upload",
            width=200,
            height=50,
            on_click=lambda e: file_picker.pick_files(allow_multiple=True),
        )
        btn_carregar = ft.ElevatedButton(text="Carregar", expand=True, height=50)
        btn_load = ft.ElevatedButton(text="Carregar dados em JSON", expand=True, height=40)

        self.initial_page = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "Extrator JSON de Alunos em Recuperação",
                            style="headlineMedium",
                            color=ft.Colors.BLUE,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Divider(thickness=1),
                ft.Row([self.txt_path, btn_upload], spacing=10),
                ft.Row([btn_carregar], spacing=10),
            ],
            expand=True,
        )

        self.after_file_selected = ft.Column([], expand=True, visible=False)
        self.sheet_containers = []

        def switch_page(e: ft.ControlEvent):
            if not self.txt_path.value:
                self.txt_path.border_color = ft.Colors.RED
                page.open(
                    ft.SnackBar(ft.Text("Por favor, selecione as planilhas!"), bgcolor=ft.Colors.RED_100)
                )
                page.update()
                return

            paths = [p.strip() for p in self.txt_path.value.split(",")]
            if any(not p.lower().endswith(".xlsx") for p in paths):
                self.txt_path.border_color = ft.Colors.YELLOW
                page.open(
                    ft.SnackBar(
                        ft.Text("Selecione as planilhas no formato .xlsx!"),
                        bgcolor=ft.Colors.YELLOW_100
                    )
                )
                page.update()
                return

            self.sheet_containers.clear()
            controls: list = [
                ft.Row(
                    [
                        ft.Text(
                            "Extrator JSON de Alunos em Recuperação",
                            style="headlineMedium",
                            color=ft.Colors.BLUE,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Divider(thickness=1),
            ]

            for p in paths:
                c = self.make_sheet_info(os.path.basename(p))
                self.sheet_containers.append(c)
                controls.append(c)

            controls.append(ft.Row([btn_load], spacing=10))
            self.after_file_selected.controls = controls

            self.initial_page.visible = False
            self.after_file_selected.visible = True
            page.window.maximized = True
            page.update()

        btn_carregar.on_click = switch_page

        def on_load(e: ft.ControlEvent):
            for sheet in self.sheet_containers:
                headers_tf, first_tf, last_tf = sheet.txt_fields
                if not headers_tf.value.strip() or not first_tf.value.strip() or not last_tf.value.strip():
                    for tf in sheet.txt_fields:
                        if not tf.value.strip():
                            tf.border_color = ft.Colors.RED
                    page.open(
                        ft.SnackBar(
                            ft.Text("Por favor, preencha todos os dados!"),
                            bgcolor=ft.Colors.RED_100
                        )
                    )
                    page.update()
                    return

                if not HEADER_RE.match(headers_tf.value.strip()):
                    headers_tf.border_color = ft.Colors.YELLOW
                    page.open(
                        ft.SnackBar(
                            ft.Text("Cabeçalhos inválidos! Apenas letras maiúsculas separadas por vírgula."),
                            bgcolor=ft.Colors.YELLOW_100
                        )
                    )
                    page.update()
                    return

                val1 = first_tf.value.strip()
                if not val1.isdigit() or int(val1) <= 0:
                    first_tf.border_color = ft.Colors.YELLOW
                    page.open(
                        ft.SnackBar(
                            ft.Text("Linha primeiro Aluno deve ser inteiro > 0!"),
                            bgcolor=ft.Colors.YELLOW_100
                        )
                    )
                    page.update()
                    return

                val2 = last_tf.value.strip()
                if not val2.isdigit() or int(val2) <= int(val1):
                    last_tf.border_color = ft.Colors.YELLOW
                    page.open(
                        ft.SnackBar(
                            ft.Text("Linha último Aluno deve ser inteiro > primeiro!"),
                            bgcolor=ft.Colors.YELLOW_100
                        )
                    )
                    page.update()
                    return

            paths = [p.strip() for p in self.txt_path.value.split(",")]
            jsons: list[dict] = []
            for idx, sheet in enumerate(self.sheet_containers):
                headers = sheet.txt_fields[0].value
                firstRow = int(sheet.txt_fields[1].value)
                lastRow = int(sheet.txt_fields[2].value)
                jsons.append(extract_json(paths[idx], headers, firstRow, lastRow))

            output_file = "dados/AlunosEmRecuperacao.json"
            merged = merge_jsons(jsons)

            self._confirm_and_save(page, output_file, merged)

        btn_load.on_click = on_load

        page.add(self.initial_page, self.after_file_selected)

    def run(self):
        ft.app(target=self._build_ui)
