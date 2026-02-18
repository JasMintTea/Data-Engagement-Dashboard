from App import create_app
from App.database import db
from App.models import Admin, Institution, HR

def seed_data():
    app = create_app()
    with app.app_context():
        print("Seeding database...")
        
        # Create default institutions
        institutions = [
            {'name': 'Central Bank of Trinidad and Tobago', 'code': 'CBTT'},
            {'name': 'First Citizens Bank', 'code': 'FCIT'},
            {'name': 'Sagicor', 'code': 'SAGC'},
            {'name': 'Scotiabank', 'code': 'SCOT'},
            {'name': 'TT Mortgage Bank', 'code': 'TTMB'},
            {'name': 'TTUTC', 'code': 'TTUT'},
            {'name': 'Ministry of Finance', 'code': 'MOF'}
        ]
        
        for inst in institutions:
            existing = Institution.query.filter_by(code=inst['code']).first()
            if not existing:
                institution = Institution(name=inst['name'], code=inst['code'])
                db.session.add(institution)
                print(f"Added institution: {inst['name']}")
        
        # Create default admin
        admin = Admin.query.filter_by(email='admin@carifin.com').first()
        if not admin:
            admin = Admin(
                username='admin',
                email='admin@carifin.com',
                password='Admin123!'
            )
            db.session.add(admin)
            print("Added admin user: admin@carifin.com / Admin123!")
        
        # Commit all changes
        db.session.commit()
        print("seeding complete!")

if __name__ == '__main__':
    seed_data()