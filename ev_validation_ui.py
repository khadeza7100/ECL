import asyncio

import flet as ft


def get_recalculate_button(
    page,
    on_click=None,
    state=None,
    button_label="Recalculate",
    button_width=140,
    show_completed_label=False,
):
    if state is None:
        state = {}
    state.setdefault("progress", 0.0)
    state.setdefault("message", "")
    state.setdefault("running", False)
    state.setdefault("completed", False)

    def format_percentage(progress):
        percentage = f"{round(progress * 100)}%"
        return (
            f"{percentage} completed"
            if show_completed_label else percentage
        )

    progress_bar = ft.ProgressBar(
        value=state["progress"],
        width=160,
        bar_height=5,
        color="#00e676",
        bgcolor="#1e534b",
        border_radius=4,
    )
    percentage_text = ft.Text(
        format_percentage(state["progress"]),
        color="white70",
        size=11,
    )
    progress_display = ft.Row(
        controls=[progress_bar, percentage_text],
        spacing=8,
        visible=bool(state["message"]),
    )
    completion_text = ft.Text(
        state["message"],
        color="#78eb64" if state["completed"] else "#ffcc80",
        size=11,
        visible=bool(state["message"]),
    )
    recalculate_button = ft.ElevatedButton(
        content=ft.Text(
            button_label,
            color="#061d19",
            weight="bold",
            size=12,
        ),
        on_click=None,
        disabled=on_click is None or state["running"],
        style=ft.ButtonStyle(
            bgcolor="#78eb64",
            shape=ft.RoundedRectangleBorder(radius=20),
        ),
        height=38,
        width=button_width,
    )

    state["controls"] = (
        progress_display,
        progress_bar,
        percentage_text,
        completion_text,
        recalculate_button,
    )

    def update_progress_controls():
        controls = state.get("controls")
        if not controls:
            return
        current_row, current_bar, current_percentage, current_message, current_button = controls
        current_bar.value = state["progress"]
        current_percentage.value = format_percentage(state["progress"])
        current_row.visible = bool(state["message"])
        current_message.value = state["message"]
        current_message.visible = bool(state["message"])
        current_message.color = "#78eb64" if state["completed"] else "#ffcc80"
        current_button.disabled = on_click is None or state["running"]

    async def recalculate(e):
        if on_click is None or state["running"]:
            return

        state["running"] = True
        state["completed"] = False
        state["progress"] = 0.0
        state["message"] = "Recalculating..."
        update_progress_controls()
        page.update()
        completed = False
        completion_message = ""
        failure_message = ""

        try:
            for progress in (0.2, 0.4, 0.6, 0.8):
                await asyncio.sleep(0.06)
                state["progress"] = progress
                update_progress_controls()
                page.update()
            completion_message = on_click(e) or ""
            completed = True
        except Exception as error:
            failure_message = str(error)
        finally:
            state["running"] = False
            state["completed"] = completed
            state["progress"] = 1.0 if completed else 0.0
            state["message"] = (
                completion_message or "Recalculation completed successfully."
                if completed else f"Recalculation failed: {failure_message}"
            )
            update_progress_controls()
            page.update()

    recalculate_button.on_click = recalculate

    return ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Container(content=progress_display, expand=True),
                    recalculate_button,
                ],
                alignment="spaceBetween",
                vertical_alignment="center",
                spacing=12,
            ),
            completion_text,
        ],
        spacing=4,
    )
