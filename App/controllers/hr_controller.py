from App.models import Participant, Registration, Result, Institution
from App.database import db


def get_hr_stats(institution_id):
    # Registration count: participants from this institution that have at least one registration
    total_reg = db.session.query(Registration)\
        .join(Participant)\
        .filter(Participant.institution_id == institution_id)\
        .distinct(Registration.participant_id).count()

    participated = db.session.query(Registration)\
        .join(Participant)\
        .filter(Participant.institution_id == institution_id)\
        .join(Result).distinct(Registration.participant_id).count()
        
    participants_query = Participant.query.join(Registration).filter(Participant.institution_id == institution_id).distinct().all()
    participants = []
    
    for p in participants_query:
        has_res = db.session.query(Result).join(Registration).filter(Registration.participant_id == p.id).first() is not None
        
        bib_no = "N/A"
        if p.registrations:
            reg = p.registrations[0]
            # Assumes relationship exists and returns at least one assignment
            if hasattr(reg, 'bib_no_assignments') and reg.bib_no_assignments:
                bib_no = reg.bib_no_assignments[0].bib_no.bib_value
                
        participants.append({
            "name": f"{p.first_name} {p.last_name}",
            "bib_number": bib_no,
            "division": p.division,
            "has_result": has_res
        })

    return {
        "reg_count": total_reg,
        "part_count": participated,
        "no_show_count": total_reg - participated,
        "participants": participants,
        "institution": Institution.query.get(institution_id)
    }