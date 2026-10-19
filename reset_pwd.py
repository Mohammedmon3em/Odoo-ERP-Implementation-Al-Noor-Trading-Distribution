env['res.users'].search([('login', '=', 'admin')]).write({'password': 'admin'})
env.cr.commit()
print("PASSWORD RESET COMPLETE")
