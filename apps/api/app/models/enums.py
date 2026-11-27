import enum


class EmployeeRole(str, enum.Enum):
    owner = "owner"
    branch_manager = "branch_manager"
    shift_supervisor = "shift_supervisor"
    staff = "staff"


class ShiftStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    cancelled = "cancelled"


class AttendanceStatus(str, enum.Enum):
    on_time = "on_time"
    late = "late"
    absent = "absent"


class KpiDirection(str, enum.Enum):
    higher_is_better = "higher_is_better"
    lower_is_better = "lower_is_better"
