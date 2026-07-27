from app import create_app
from models import db, User, Employee, Manager, Holiday
from werkzeug.security import generate_password_hash
from datetime import datetime, date

def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        if User.query.filter_by(username='superadmin').first():
            print('Database already seeded!')
            return

        superadmin_user = User(
            username='superadmin',
            email='superadmin@company.com',
            password_hash=generate_password_hash('admin123'),
            role='superadmin'
        )
        db.session.add(superadmin_user)

        admin_user = User(
            username='admin',
            email='admin@company.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin_user)

        mgr_user = User(
            username='manager1',
            email='manager1@company.com',
            password_hash=generate_password_hash('manager123'),
            role='manager'
        )
        db.session.add(mgr_user)

        emp_user = User(
            username='employee1',
            email='employee1@company.com',
            password_hash=generate_password_hash('employee123'),
            role='employee'
        )
        db.session.add(emp_user)

        emp_user2 = User(
            username='employee2',
            email='employee2@company.com',
            password_hash=generate_password_hash('employee123'),
            role='employee'
        )
        db.session.add(emp_user2)

        db.session.flush()

        manager1 = Manager(
            user_id=mgr_user.id,
            manager_code='MGR0001',
            first_name='Rajesh',
            last_name='Kumar',
            email='manager1@company.com',
            phone='9876543210',
            department='Engineering',
            designation='Engineering Manager',
            date_of_joining=date(2020, 1, 15),
            created_by_admin_id=admin_user.id
        )
        db.session.add(manager1)
        db.session.flush()

        mgr_employee = Employee(
            user_id=mgr_user.id,
            employee_code='EMP0001',
            first_name='Rajesh',
            last_name='Kumar',
            email='manager1@company.com',
            phone='9876543210',
            department='Engineering',
            designation='Engineering Manager',
            date_of_joining=date(2020, 1, 15),
            salary=120000,
            address='Bangalore, Karnataka'
        )
        db.session.add(mgr_employee)
        db.session.flush()

        emp1 = Employee(
            user_id=emp_user.id,
            employee_code='EMP0002',
            first_name='Amit',
            last_name='Sharma',
            email='employee1@company.com',
            phone='9876543211',
            department='Engineering',
            designation='Software Developer',
            date_of_joining=date(2021, 6, 1),
            salary=75000,
            reporting_manager_id=mgr_employee.id,
            address='Mumbai, Maharashtra'
        )
        db.session.add(emp1)

        emp2 = Employee(
            user_id=emp_user2.id,
            employee_code='EMP0003',
            first_name='Priya',
            last_name='Patel',
            email='employee2@company.com',
            phone='9876543212',
            department='Engineering',
            designation='Senior Developer',
            date_of_joining=date(2020, 3, 15),
            salary=95000,
            reporting_manager_id=mgr_employee.id,
            address='Bangalore, Karnataka'
        )
        db.session.add(emp2)

        indian_holidays_2026 = [
            ('2026-01-26', 'Republic Day', 'national'),
            ('2026-01-29', 'Maha Shivaratri', 'festival'),
            ('2026-03-03', 'Holi', 'festival'),
            ('2026-03-27', 'Good Friday', 'festival'),
            ('2026-03-31', 'Id-ul-Fitr', 'festival'),
            ('2026-04-14', 'Ambedkar Jayanti', 'national'),
            ('2026-05-01', 'Labour Day', 'national'),
            ('2026-07-06', 'Id-ul-Zuha (Bakrid)', 'festival'),
            ('2026-08-15', 'Independence Day', 'national'),
            ('2026-08-27', 'Janmashtami', 'festival'),
            ('2026-10-02', 'Gandhi Jayanti', 'national'),
            ('2026-10-07', 'Dussehra', 'festival'),
            ('2026-10-26', 'Diwali', 'festival'),
            ('2026-10-28', 'Govardhan Puja', 'festival'),
            ('2026-11-05', 'Guru Nanak Jayanti', 'festival'),
            ('2026-12-25', 'Christmas Day', 'festival'),
        ]

        for date_str, name, htype in indian_holidays_2026:
            dt = datetime.strptime(date_str, '%Y-%m-%d').date()
            holiday = Holiday(date=dt, name=name, type=htype, year=dt.year)
            db.session.add(holiday)

        db.session.commit()
        print('Database seeded successfully!')
        print()
        print('=== LOGIN CREDENTIALS ===')
        print('Super Admin:  superadmin / admin123')
        print('Admin:        admin / admin123')
        print('Manager:      manager1 / manager123')
        print('Employee 1:   employee1 / employee123')
        print('Employee 2:   employee2 / employee123')

if __name__ == '__main__':
    seed()
