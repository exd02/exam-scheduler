import json
from pathlib import Path
import flet as ft
from typing import Any, Dict


def confirm_and_save(
    page: ft.Page,
    output_file: str,
    data: Dict[str, Any],
    success_message: str,
) -> None:
    """
    Se `output_file` existir:
      - Exibe um AlertDialog pedindo confirmação.
      - Se o usuário clicar em “Sim”, grava `data` em `output_file` e mostra um SnackBar com `success_message`.
      - Se clicar em “Não”, apenas fecha o diálogo.
    Se `output_file` NÃO existir:
      - Grava `data` direto em `output_file` e mostra o SnackBar com `success_message`.
    """
    def _show_success(msg: str):
        page.open(ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.GREEN_100))

    def _save_to_disk():
        # Garante que a pasta exista
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    if Path(output_file).exists():
        def _overwrite(e: ft.ControlEvent):
            _save_to_disk()
            dlg.open = False
            page.update()
            _show_success(f"'{output_file}' sobrescrito com sucesso!")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmação"),
            content=ft.Text(
                f'Você tem certeza que quer sobrescrever o arquivo "{output_file}"?'
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
        _save_to_disk()
        _show_success(success_message)

    page.update()