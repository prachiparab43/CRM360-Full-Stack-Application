import fs from 'fs';
let content = fs.readFileSync('backend/app/schemas/employee.py', 'utf8');

// First add the import if missing
if (!content.includes('from .role import RoleResponse')) {
    content = content.replace('from datetime import date', 'from datetime import date\\nfrom typing import Any');
}

// Then replace the class definition
content = content.replace(
    'class EmployeeResponse(EmployeeBase):\\n    id: int\\n    \\n    class Config:\\n        from_attributes = True',
    'class EmployeeResponse(EmployeeBase):\\n    id: int\\n    role: Any = None\\n    \\n    class Config:\\n        from_attributes = True'
);

fs.writeFileSync('backend/app/schemas/employee.py', content);
console.log('Employee schema patched');
