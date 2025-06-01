import flet as ft
import os
import re
import json
from pathlib import Path

from src.recovery_utils import extract_json, merge_jsons

GREY_C = "#2A2D33"
HEADER_RE = re.compile(r'^[A-Z]+(?:,[A-Z]+)*$')


class RecoveryExtractor:
    """
    Classe que encapsula a interface Flet para:
    - permitir upload de uma ou mais planilhas .xlsx
    - solicitar ao usuário quais colunas (cabeçalhos) e linhas inicial/final
    - extrair, mesclar e salvar o AlunosEmRecuperacao.json
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

    def make_sheet_info(self, filename: str) -> ft.Container:
        """
        Monta o container que pergunta:
        - colunas de cabeçalho (texto, ex: “A,B,C”)
        - linha inicial do primeiro aluno
        - linha final do último aluno
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
        # armazenamos os três TextFields para validação depois:
        container.txt_fields = [txt_headers, txt_first, txt_last]
        return container

    def _on_file_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            # retorna uma lista de caminhos, separados por vírgula
            self.txt_path.value = ", ".join(f.path for f in e.files)
            self.txt_path.border_color = ft.Colors.BLUE_800
            self.page.update()

    def _build_ui(self, page: ft.Page):
        """
        Constrói as duas “páginas” da interface:
        1) initial_page: campo para selecionar planilhas e botão “Carregar”,
           que vai mostrar os containers para cabeçalhos/linhas.
        2) after_file_selected: depois que o usuário clica em “Carregar”,
           ele vê um container por planilha + botão “Carregar dados em JSON”.
        """
        self.page = page
        page.title = "Extrator JSON de Alunos em Recuperação"
        page.theme_mode = "dark"
        page.window.width = 790
        page.window.height = 265
        page.padding = 20

        # → campo de texto que armazena o(s) path(s) das planilhas
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

        # → primeira “página” (sem campos para cabeçalhos ainda)
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

        # → segunda “página”, inicialmente vazia
        self.after_file_selected = ft.Column([], expand=True, visible=False)
        self.sheet_containers = []

        # callback quando clica em “Carregar” (vai gerar campos de cabeçalhos/linhas)
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
                    ft.SnackBar(ft.Text("Selecione as planilhas no formato .xlsx!"), bgcolor=ft.Colors.YELLOW_100)
                )
                page.update()
                return

            # limpa containers antigos, se houver
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

            # para cada caminho, cria um container pedindo cabeçalhos/linhas
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

        # callback quando clica em “Carregar dados em JSON”
        def on_load(e: ft.ControlEvent):
            # valida todos os campos de cada container
            for idx, sheet in enumerate(self.sheet_containers):
                headers_tf, first_tf, last_tf = sheet.txt_fields
                # 1) nenhum campo pode ficar vazio
                if not headers_tf.value.strip() or not first_tf.value.strip() or not last_tf.value.strip():
                    for tf in sheet.txt_fields:
                        if not tf.value.strip():
                            tf.border_color = ft.Colors.RED
                    page.open(ft.SnackBar(ft.Text("Por favor, preencha todos os dados!"), bgcolor=ft.Colors.RED_100))
                    page.update()
                    return

                # 2) valida formato de cabeçalhos (apenas maiúsculas separadas por vírgula)
                if not HEADER_RE.match(headers_tf.value.strip()):
                    headers_tf.border_color = ft.Colors.YELLOW
                    page.open(
                        ft.SnackBar(
                            ft.Text("Cabeçalhos inválidos! Apenas letras maiúsculas separadas por vírgula."),
                            bgcolor=ft.Colors.YELLOW_100,
                        )
                    )
                    page.update()
                    return

                # 3) valida linha inicial
                val1 = first_tf.value.strip()
                if not val1.isdigit() or int(val1) <= 0:
                    first_tf.border_color = ft.Colors.YELLOW
                    page.open(
                        ft.SnackBar(
                            ft.Text("Linha primeiro Aluno deve ser inteiro > 0!"), bgcolor=ft.Colors.YELLOW_100
                        )
                    )
                    page.update()
                    return

                # 4) valida linha final
                val2 = last_tf.value.strip()
                if not val2.isdigit() or int(val2) <= int(val1):
                    last_tf.border_color = ft.Colors.YELLOW
                    page.open(
                        ft.SnackBar(
                            ft.Text("Linha último Aluno deve ser inteiro > primeiro!"), bgcolor=ft.Colors.YELLOW_100
                        )
                    )
                    page.update()
                    return

            # se tudo válido, inicia a extração e mescla
            paths = [p.strip() for p in self.txt_path.value.split(",")]
            jsons: list[dict] = []
            for idx, sheet in enumerate(self.sheet_containers):
                headers = sheet.txt_fields[0].value
                firstRow = int(sheet.txt_fields[1].value)
                lastRow = int(sheet.txt_fields[2].value)
                jsons.append(
                    extract_json(paths[idx], headers, firstRow, lastRow)
                )

            merged = merge_jsons(jsons)
            # grava no arquivo fixo “AlunosEmRecuperacao.json” na raiz de dados
            output_file = "dados/AlunosEmRecuperacao.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)

            page.open(
                ft.SnackBar(ft.Text(f"Exportado '{output_file}' com sucesso!"), bgcolor=ft.Colors.GREEN_100)
            )
            page.update()

        btn_load.on_click = on_load

        page.add(self.initial_page, self.after_file_selected)

    def run(self):
        ft.app(target=self._build_ui)
