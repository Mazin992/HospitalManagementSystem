import os
from app import create_app, db
from app.models import User, Role, Patient, Appointment, Service, Bed, Invoice

# Get configuration from environment variable (default: development)
config_name = os.environ.get('FLASK_CONFIG', 'development')
app = create_app(config_name)

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'Patient': Patient,
        'Appointment': Appointment,
        'Service': Service,
        'Bed': Bed,
        'Invoice': Invoice
    }

@app.cli.command()
def test():
    """Run the unit tests"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
