import fs from 'fs';
let content = fs.readFileSync('frontend/src/pages/Roles.jsx', 'utf8');

const matrix_ui = `
              <div className="max-h-[50vh] overflow-y-auto border p-2 rounded text-sm">
                <h3 className="font-semibold mb-2 bg-gray-100 p-2 sticky top-0">Permissions</h3>
                {['Lead', 'Opportunity', 'Customer', 'Contact', 'Task', 'Meeting', 'Visit', 'Role', 'Employee', 'Company'].map(mod => (
                  <div key={mod} className="mb-4 border-b pb-2">
                    <div className="font-medium text-gray-700 mb-1">{mod}</div>
                    <div className="grid grid-cols-2 gap-2">
                      {['View', 'Edit', 'Create', 'Delete', 'Qualify Lead', 'Change Stage'].map(act => {
                        const existing = formData.permissions.find(p => p.module === mod && p.action === act);
                        return (
                          <div key={act} className="flex items-center gap-2">
                            <input 
                              type="checkbox" 
                              checked={!!existing} 
                              onChange={(e) => {
                                if(e.target.checked) {
                                  setFormData({...formData, permissions: [...formData.permissions, {module: mod, action: act, data_scope: 'Own'}]});
                                } else {
                                  setFormData({...formData, permissions: formData.permissions.filter(p => !(p.module===mod && p.action===act))});
                                }
                              }}
                            />
                            <span>{act}</span>
                            {existing && (
                              <select 
                                className="border text-xs p-1 rounded ml-auto bg-white"
                                value={existing.data_scope}
                                onChange={(e) => {
                                  const updated = formData.permissions.map(p => 
                                    (p.module===mod && p.action===act) ? {...p, data_scope: e.target.value} : p
                                  );
                                  setFormData({...formData, permissions: updated});
                                }}
                              >
                                <option value="Own">Own</option>
                                <option value="Team">Team</option>
                                <option value="Company">Company</option>
                                <option value="All">All</option>
                              </select>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
`;

content = content.replace('<p className="text-xs text-gray-500">Note: Advanced permissions matrix logic goes here.</p>', matrix_ui);
content = content.replace('max-w-md', 'max-w-3xl');

fs.writeFileSync('frontend/src/pages/Roles.jsx', content);
console.log('Roles.jsx updated');
