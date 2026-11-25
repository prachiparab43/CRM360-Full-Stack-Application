"""CRM360 Dynamic RBAC Permission Catalog.

Single source of truth for all modules, valid actions per module, and valid data scopes.
"""
from typing import Dict, List, Set, Any

MODULE_COMPANY = "Company"
MODULE_EMPLOYEE = "Employee"
MODULE_ROLE = "Role"
MODULE_LEAD = "Lead"
MODULE_OPPORTUNITY = "Opportunity"
MODULE_CUSTOMER = "Customer"
MODULE_CONTACT = "Contact"
MODULE_ACTIVITY = "Activity"
MODULE_TASK = "Task"
MODULE_MEETING = "Meeting"
MODULE_VISIT = "Visit"
MODULE_DASHBOARD = "Dashboard"
MODULE_REPORT = "Report"
MODULE_AUDIT_LOG = "AuditLog"
MODULE_GEO = "Geo"

MODULES: List[str] = [
    MODULE_COMPANY,
    MODULE_EMPLOYEE,
    MODULE_ROLE,
    MODULE_LEAD,
    MODULE_OPPORTUNITY,
    MODULE_CUSTOMER,
    MODULE_CONTACT,
    MODULE_ACTIVITY,
    MODULE_TASK,
    MODULE_MEETING,
    MODULE_VISIT,
    MODULE_DASHBOARD,
    MODULE_REPORT,
    MODULE_AUDIT_LOG,
    MODULE_GEO,
]

SCOPES: List[str] = ["Own", "Team", "Company", "All"]

SCOPE_RANK: Dict[str, int] = {
    "Own": 1,
    "Team": 2,
    "Company": 3,
    "All": 4,
}

# Module-specific valid actions definition
MODULE_ACTIONS: Dict[str, List[str]] = {
    MODULE_COMPANY: [
        "View", "Create", "Edit", "Delete", "Export", "Import",
        "View Company Data",
    ],
    MODULE_EMPLOYEE: [
        "View", "Create", "Edit", "Delete", "Assign", "Export", "Import",
        "View Team Data", "View Company Data",
    ],
    MODULE_ROLE: [
        "View", "Create", "Edit", "Delete", "Assign", "Export",
    ],
    MODULE_LEAD: [
        "View", "Create", "Edit", "Delete", "Assign", "Export", "Import",
        "Qualify Lead", "Create Opportunity", "Reassign Lead",
        "View Team Data", "View Company Data",
    ],
    MODULE_OPPORTUNITY: [
        "View", "Create", "Edit", "Delete", "Assign", "Export", "Import",
        "Change Opportunity Stage", "Mark Opportunity Won", "Mark Opportunity Lost",
        "Reassign Opportunity", "View Team Data", "View Company Data",
    ],
    MODULE_CUSTOMER: [
        "View", "Create", "Edit", "Delete", "Assign", "Export", "Import",
        "View Team Data", "View Company Data",
    ],
    MODULE_CONTACT: [
        "View", "Create", "Edit", "Delete", "Assign", "Export", "Import",
    ],
    MODULE_ACTIVITY: [
        "View", "Create", "Edit", "Delete", "Export",
    ],
    MODULE_TASK: [
        "View", "Create", "Edit", "Delete", "Assign", "Export",
    ],
    MODULE_MEETING: [
        "View", "Create", "Edit", "Delete", "Assign", "Export",
    ],
    MODULE_VISIT: [
        "View", "Create", "Edit", "Delete", "Export",
    ],
    MODULE_DASHBOARD: [
        "View", "View Team Data", "View Company Data", "Export",
    ],
    MODULE_REPORT: [
        "View", "Export",
    ],
    MODULE_AUDIT_LOG: [
        "View", "Export",
    ],
    MODULE_GEO: [
        "Geo.CheckIn",
        "Geo.CheckOut",
        "Geo.ViewOwnLocation",
        "Geo.ViewTeamLocation",
        "Geo.ViewCompanyLocation",
        "Geo.ViewLiveLocation",
        "Geo.ViewLocationHistory",
        "Geo.ViewVisits",
        "Geo.Export",
        "View",
        "Export",
    ],
}

# Actions that are restricted to specific scopes
RESTRICTED_SCOPES: Dict[str, List[str]] = {
    "Geo.CheckIn": ["Own"],
    "Geo.CheckOut": ["Own"],
}

def is_valid_permission(module: str, action: str, data_scope: str) -> bool:
    """Validate a permission triple against the catalog."""
    if module not in MODULES:
        return False
    valid_actions = MODULE_ACTIONS.get(module, [])
    if action not in valid_actions:
        return False
    if data_scope not in SCOPES:
        return False
    if action in RESTRICTED_SCOPES:
        allowed = RESTRICTED_SCOPES[action]
        if data_scope not in allowed:
            return False
    return True

def get_catalog() -> Dict[str, Any]:
    """Return dictionary representation of the permission catalog."""
    return {
        "modules": MODULES,
        "actions": MODULE_ACTIONS,
        "scopes": SCOPES,
        "restricted_scopes": RESTRICTED_SCOPES,
    }

def get_all_catalog_permissions() -> List[Dict[str, str]]:
    """Return list of all valid (module, action, default_scope) for initial seeding."""
    perms = []
    for module, actions in MODULE_ACTIONS.items():
        for action in actions:
            default_scope = "Own" if action in RESTRICTED_SCOPES else "All"
            perms.append({
                "module": module,
                "action": action,
                "data_scope": default_scope,
            })
    return perms
