import csv

from django.core.files.uploadedfile import UploadedFile
from django_components import component
from pydantic import BaseModel

from livecomponents import CallContext, InitStateContext, LiveComponent, command


class CsvViewerState(BaseModel):
    # Note: For the sake of simplicity, we are storing the file contents in the state.
    # However, this is not recommended for large files. Instead, we recommend storing
    # the file contents in an external store and keeping in the state only the minimal
    # information necessary to restore the file.
    file_name: str | None = None
    header: list[str] | None = None
    records: list[list[str]] | None = None
    error: str | None = None

    def set_error(self, error_message: str):
        self.header = None
        self.records = None
        self.error = error_message


@component.register("csvviewer")
class CsvViewer(LiveComponent[CsvViewerState]):
    template_name = "csvviewer/csvviewer.html"

    def init_state(
        self, context: InitStateContext, **component_kwargs
    ) -> CsvViewerState:
        return CsvViewerState(**component_kwargs)

    @command
    def upload_file(self, call_context: CallContext[CsvViewerState], delimiter: str):
        """Parse CSV file and update state in place."""
        state = call_context.state
        csv_file: UploadedFile = call_context.request.FILES["csv_file"]

        try:
            csv_content = csv_file.read().decode("utf-8")
        except UnicodeDecodeError:
            state.set_error("File is not a valid UTF-8 file")
            return
        call_context.state.file_name = csv_file.name

        reader = csv.reader(csv_content.splitlines(), delimiter=delimiter)
        records = list(reader)
        if not records:
            state.set_error("File is empty")
            return

        state.header = records[0]
        state.records = records[1:]
        state.error = None
