import json
import uuid
from os.path import join
from typing import Dict, List, Optional
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage

from opentelemetry import trace

from baserow.core.models import Application, Workspace
from baserow.core.registries import ImportExportConfig, application_type_registry
from baserow.core.storage import (
    _create_storage_dir_if_missing_and_open,
    get_default_storage,
)
from baserow.core.telemetry.utils import baserow_trace_methods
from baserow.core.utils import ChildProgressBuilder, Progress

tracer = trace.get_tracer(__name__)


class ImportExportHandler(metaclass=baserow_trace_methods(tracer)):
    def export_application(
        self,
        app: Application,
        import_export_config: ImportExportConfig,
        files_zip: ZipFile,
        storage: Storage,
        progress: Progress,
    ) -> Dict:
        """
        Exports a single application (structure, content and assets) to a zip file.
        :param app: Application instance that will be exported
        :param import_export_config: provides configuration options for the
            import/export process to customize how it works.
        :param files_zip: ZipFile instance to which the exported data will be written
        :param storage: The storage where the export will be stored.
        :param progress: Progress instance that allows tracking of the export progress.
        :return: The exported and serialized application.
        """

        application = app.specific
        application_type = application_type_registry.get_by_model(application)

        with application_type.export_safe_transaction_context(application):
            exported_application = application_type.export_serialized(
                application, import_export_config, files_zip, storage
            )
        progress.increment()
        return exported_application

    def export_multiple_applications(
        self,
        applications: List[Application],
        import_export_config: ImportExportConfig,
        files_zip: ZipFile,
        storage: Storage,
        progress: Progress,
    ) -> List[Dict]:
        """
        Exports multiple applications (structure, content and assets) to a zip file.
        :param applications: Application instances that will be exported
        :param import_export_config: provides configuration options for the
            import/export process to customize how it works.
        :param files_zip: ZipFile instance to which the exported data will be written
        :param storage: The storage where the export will be stored.
        :param progress: Progress instance that allows tracking of the export progress.
        :return: The exported and serialized application.
        """

        exported_applications = []

        for app in applications:
            exported_application = self.export_application(
                app, import_export_config, files_zip, storage, progress
            )
            exported_applications.append(exported_application)
        return exported_applications

    def export_json_data(
        self,
        file_name: str,
        exported_applications: List[Dict],
        files_zip: ZipFile,
        storage: Storage,
    ) -> None:
        """
        Export application data (structure and content) to a json file
        and put it in the zip file.

        :param file_name: name of the file that will be created with exported data
        :param exported_applications: exported and serialized applications
        :param files_zip: ZipFile instance to which the exported data will be written
        :param storage: The storage where the files will be stored
        """

        temp_json_file_name = f"temp_{file_name}_{uuid.uuid4()}.json"
        temp_json_file_path = storage.save(temp_json_file_name, ContentFile(""))

        with storage.open(temp_json_file_path, "w") as temp_json_file:
            json.dump(exported_applications, temp_json_file, indent=None)

        with storage.open(temp_json_file_path, "rb") as temp_json_file:
            files_zip.write(temp_json_file.name, file_name)
        storage.delete(temp_json_file_path)

    def export_file_path(self, file_name: str) -> str:
        """
        Returns the full path for given file_name, which will be used
        to store the file within storage

        :param file_name: name of file
        :return: full path to the file
        """

        return join(settings.EXPORT_FILES_DIRECTORY, file_name)

    def export_workspace_applications(
        self,
        workspace: Workspace,
        import_export_config: ImportExportConfig,
        applications: List[Application],
        storage: Optional[Storage] = None,
        progress_builder: Optional[ChildProgressBuilder] = None,
    ) -> str:
        """
        Create zip file with exported applications. If applications param is provided,
        only those applications will be exported.

        :param workspace: The workspace of which the applications will be exported.
        :param import_export_config: provides configuration options for the
            import/export process to customize how it works.
        :param applications: A list of Application instances that will be exported.
        :param storage: The storage where the files will be stored. If not provided
            the default storage will be used.
        :param progress_builder: A progress builder that allows for publishing progress.
        :return: name of the zip file with exported applications
        """

        storage = storage or get_default_storage()
        applications = applications or []

        progress = ChildProgressBuilder.build(progress_builder, child_total=100)
        export_app_progress = progress.create_child(80, len(applications))

        zip_file_name = f"workspace_{workspace.id}_{uuid.uuid4()}.zip"
        json_file_name = f"data/workspace_export.json"

        export_path = self.export_file_path(zip_file_name)

        with _create_storage_dir_if_missing_and_open(
            export_path, storage
        ) as files_buffer:
            with ZipFile(files_buffer, "a", ZIP_DEFLATED, False) as files_zip:
                exported_applications = self.export_multiple_applications(
                    applications,
                    import_export_config,
                    files_zip,
                    storage,
                    export_app_progress,
                )
                self.export_json_data(
                    json_file_name, exported_applications, files_zip, storage
                )
                progress.increment(by=20)
        return zip_file_name
