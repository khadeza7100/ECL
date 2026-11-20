import flet as ft

from components.csv_profile_import import (
    PROFILE_IMPORT_SPECS,
    ProfileImportError,
    import_profile_csv,
)


def get_csv_upload_view(page: ft.Page, file_picker: ft.FilePicker, profile_type: str):
    spec = PROFILE_IMPORT_SPECS[profile_type]
    selected_file = {"bytes": None}

    selected_file_text = ft.Text("No CSV selected.", color="white70", size=13)
    status_text = ft.Text("", color="white70", size=13)
    import_button = ft.ElevatedButton(
        "Import CSV",
        disabled=True,
        style=ft.ButtonStyle(
            bgcolor="#78eb64",
            color="black",
            shape=ft.RoundedRectangleBorder(radius=20),
        ),
    )

    async def choose_file(e):
        try:
            files = await file_picker.pick_files(
                dialog_title=f"Select {spec.title} CSV",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["csv"],
                allow_multiple=False,
                with_data=True,
            )
        except Exception as error:
            status_text.value = f"Could not select the CSV file: {error}"
            status_text.color = "#ff8a80"
            page.update()
            return

        if not files:
            return

        selected = files[0]
        if not selected.name.lower().endswith(".csv"):
            selected_file["bytes"] = None
            selected_file_text.value = "No CSV selected."
            status_text.value = "Please choose a file with the .csv extension."
            status_text.color = "#ff8a80"
            import_button.disabled = True
            page.update()
            return

        if selected.bytes is None:
            selected_file["bytes"] = None
            selected_file_text.value = "No CSV selected."
            status_text.value = "The selected file could not be read. Please choose it again."
            status_text.color = "#ff8a80"
            import_button.disabled = True
            page.update()
            return

        selected_file["bytes"] = selected.bytes
        selected_file_text.value = selected.name
        status_text.value = ""
        import_button.disabled = False
        page.update()

    async def import_file(e):
        content = selected_file["bytes"]
        if content is None:
            status_text.value = "Choose a CSV file before importing."
            status_text.color = "#ff8a80"
            page.update()
            return

        import_button.disabled = True
        status_text.value = "Importing CSV..."
        status_text.color = "white70"
        page.update()

        try:
            imported_count = import_profile_csv(profile_type, content)
        except ProfileImportError as error:
            status_text.value = str(error)
            status_text.color = "#ff8a80"
        except Exception as error:
            status_text.value = f"CSV import failed: {error}"
            status_text.color = "#ff8a80"
        else:
            status_text.value = (
                f"Imported {imported_count} {spec.title} row(s). "
                "Existing records with the same key were updated."
            )
            status_text.color = "#00e676"
            selected_file["bytes"] = None
            selected_file_text.value = "No CSV selected."
        finally:
            import_button.disabled = selected_file["bytes"] is None
            page.update()

    import_button.on_click = import_file

    required_headers = ", ".join(spec.headers)
    if spec.optional_headers:
        optional_headers = ", ".join(spec.optional_headers)
        required_headers += f" (optional: {optional_headers})"

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    f"Upload {spec.title} CSV",
                    size=20,
                    weight="bold",
                    color="#00e676",
                ),
                ft.Text(
                    "CSV headers must match these database field names. "
                    "Columns may appear in any order.",
                    size=13,
                    color="white70",
                ),
                ft.Container(
                    content=ft.Text(required_headers, size=12, color="white"),
                    padding=12,
                    bgcolor="#0a2e27",
                    border=ft.Border.all(width=1, color="#144d41"),
                    border_radius=6,
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Choose CSV",
                            on_click=choose_file,
                            style=ft.ButtonStyle(
                                bgcolor="#00bfa5",
                                color="black",
                                shape=ft.RoundedRectangleBorder(radius=20),
                            ),
                        ),
                        selected_file_text,
                        import_button,
                    ],
                    wrap=True,
                    spacing=12,
                    vertical_alignment="center",
                ),
                status_text,
            ],
            spacing=16,
            horizontal_alignment="stretch",
        ),
        width=820,
        alignment=ft.Alignment(0, -1),
        padding=20,
        bgcolor="#061d19",
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=8,
    )
