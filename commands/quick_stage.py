from collections import namedtuple
import sublime
from sublime_plugin import WindowCommand, TextCommand

from ..common import messages
from .base_command import BaseCommand

MenuOption = namedtuple("MenuOption", ["requires_action", "menu_text", "filename", "is_untracked"])


class QuickStageCommand(WindowCommand, TextCommand, BaseCommand):

    """
    Displays a quick bar menu of unstaged files in the current git repository,
    allowing the user to select one or more files for staging.

    Filenames will be displayed with one of the following indicators:

        * [M] modified
        * [A] added
        * [D] deleted
        * [R] renamed/moved
        * [C] copied
        * [U] updated but unmerged
        * [?] untracked

    """

    def run(self):
        menu_options = self.get_menu_options()
        menu_entries = [f.menu_text for f in menu_options]

        def on_selection(id):
            if id == -1:
                return

            selection = menu_options[id]

            if not selection.requires_action:
                return

            elif selection.menu_text == messages.ADD_ALL_UNSTAGED_FILES:
                cmd = self.git("add", "--update", ".")
                scope_of_action = "all unstaged files"

            elif selection.menu_text == messages.ADD_ALL_FILES:
                cmd = self.git("add", "--all")
                scope_of_action = "all files"

            elif selection.is_untracked:
                cmd = self.git("add", "--", selection.filename)
                scope_of_action = "`{}`".format(selection.filename)

            else:
                cmd = self.git("add", "--update", "--", selection.filename)
                scope_of_action = "`{}`".format(selection.filename)

            sublime.status_message("{success} {target}.".format(
                success="Successfully added" if cmd.success else "Failed to add",
                target=scope_of_action
            ))

            sublime.set_timeout_async(self.run, 10)

        # self.window.show_quick_panel(menu_entries, on_selection, sublime.MONOSPACE_FONT)
        self.window.window().show_quick_panel(menu_entries, on_selection, sublime.MONOSPACE_FONT)

    def get_menu_options(self):
        status_entries = self.get_status()
        menu_options = []

        for entry in status_entries:
            if entry.status in ("A", "M"):
                continue
            filename = (entry.path if not entry.status == "R"
                        else entry.path + " <- " + entry.path_alt)
            menu_text = "[{0}] {1}".format(entry.status, filename)
            menu_options.append(MenuOption(True, menu_text, filename, entry.status == "?"))

        if not menu_options:
            return [MenuOption(False, messages.CLEAN_WORKING_DIR, None, None)]

        menu_options.append(MenuOption(True, messages.ADD_ALL_UNSTAGED_FILES, None, None))
        menu_options.append(MenuOption(True, messages.ADD_ALL_FILES, None, None))

        return menu_options
