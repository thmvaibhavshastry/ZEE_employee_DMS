from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from models import db, Holiday
from datetime import datetime, date
from rbac import can_manage_holidays

holiday_bp = Blueprint('holidays', __name__, url_prefix='/holidays')


@holiday_bp.route('/')
@login_required
def list_holidays():
    year = request.args.get('year', date.today().year)
    holidays = Holiday.query.filter_by(year=int(year)).order_by(Holiday.date).all()
    return render_template('holidays.html', holidays=holidays, current_year=int(year))


@holiday_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_holiday():
    if not can_manage_holidays(current_user):
        abort(403)

    if request.method == 'POST':
        name = request.form.get('name')
        holiday_date = request.form.get('date')
        holiday_type = request.form.get('type')
        is_optional = request.form.get('is_optional') == 'on'
        description = request.form.get('description')

        dt = datetime.strptime(holiday_date, '%Y-%m-%d').date()

        holiday = Holiday(
            date=dt,
            name=name,
            type=holiday_type,
            year=dt.year,
            is_optional=is_optional,
            description=description
        )
        db.session.add(holiday)
        db.session.commit()
        flash('Holiday added successfully!', 'success')
        return redirect(url_for('holidays.list_holidays'))

    return render_template('add_holiday.html')


@holiday_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_holiday(id):
    if not can_manage_holidays(current_user):
        abort(403)

    holiday = Holiday.query.get_or_404(id)
    if request.method == 'POST':
        holiday.name = request.form.get('name')
        dt = request.form.get('date')
        holiday.date = datetime.strptime(dt, '%Y-%m-%d').date()
        holiday.type = request.form.get('type')
        holiday.is_optional = request.form.get('is_optional') == 'on'
        holiday.description = request.form.get('description')
        db.session.commit()
        flash('Holiday updated!', 'success')
        return redirect(url_for('holidays.list_holidays'))

    return render_template('edit_holiday.html', holiday=holiday)


@holiday_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_holiday(id):
    if not can_manage_holidays(current_user):
        abort(403)

    holiday = Holiday.query.get_or_404(id)
    db.session.delete(holiday)
    db.session.commit()
    flash('Holiday deleted!', 'success')
    return redirect(url_for('holidays.list_holidays'))


@holiday_bp.route('/api/holidays')
@login_required
def get_holidays_api():
    year = request.args.get('year', date.today().year)
    holidays = Holiday.query.filter_by(year=int(year)).order_by(Holiday.date).all()
    return jsonify([{
        'id': h.id,
        'title': h.name,
        'start': h.date.strftime('%Y-%m-%d'),
        'type': h.type,
        'display': 'background',
        'backgroundColor': '#ffc107' if h.type == 'national' else '#0dcaf0' if h.type == 'festival' else '#6f42c1',
        'borderColor': '#ffc107' if h.type == 'national' else '#0dcaf0' if h.type == 'festival' else '#6f42c1',
        'allDay': True
    } for h in holidays])


@holiday_bp.route('/seed')
def seed_holidays():
    if Holiday.query.first():
        flash('Holidays already seeded!', 'info')
        return redirect(url_for('holidays.list_holidays'))

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
    flash('Indian holidays for 2026 seeded successfully!', 'success')
    return redirect(url_for('holidays.list_holidays'))
