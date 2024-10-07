from baserow.core.models import Application

__all__ = [
    "Dashboard",
]


class Dashboard(Application):
    def get_parent(self):
        # Parent is the Application here even if it's at the "same" level
        # but it's a more generic type
        return self.application_ptr
