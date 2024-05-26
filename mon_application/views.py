import logging
from datetime import datetime, timedelta, time
import random
from django.shortcuts import render
from collections import defaultdict

logger = logging.getLogger(__name__)

def renderIndex(request):
    logger.debug("Entered renderIndex view")
    try:
        salles, parametres, occupations_salles, enseignants = get_data()
        logger.debug("Data retrieved successfully")
        planning = generate_planning(salles, parametres, occupations_salles, enseignants)
        logger.debug("Planning generated successfully")
    except Exception as e:
        logger.error("Error in renderIndex view: %s", e)
        raise

    planning_hours = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    context = {
        'planning': planning,
        'planning_hours': planning_hours,
        'days': days,
    }
    
    return render(request, 'planning.html', context)

def get_data():
    # Generating 20 rooms dynamically
    salles = [{"num_bloc": random.randint(1, 3), "num_salle": random.randint(101, 120)} for _ in range(20)]

    # Setting parameters with a broader date range to ensure daily soutenances
    today = datetime.today()
    parametres = {
        "dateDebSoutenance": today + timedelta(days=1),
        "dateFinSoutenance": today + timedelta(days=60),  # Extended to two months
        "dureeSoutenance": 90,  # in minutes
        "ecartSoutenance": 30,  # in minutes
        "anneeSoutenance": today.year
    }

    # Generating a larger number of room occupations to simulate real-world scenarios
    occupations_salles = []
    for _ in range(100):
        date_occupation = today + timedelta(days=random.randint(1, 60))
        heure_debut = time(random.randint(8, 15), random.choice([0, 30]))
        duree = timedelta(minutes=parametres["dureeSoutenance"])
        heure_fin = (datetime.combine(datetime.today(), heure_debut) + duree).time()
        occupations_salles.append({
            "date_occupation": date_occupation,
            "heure_debut": heure_debut,
            "heure_fin": heure_fin,
            "num_bloc": random.randint(1, 3),
            "num_salle": random.randint(101, 120)
        })

    # Generating a larger set of teachers with dynamic unavailabilities
    enseignants = []
    for i in range(30):  # Increased to 30 teachers
        enseignants.append({
            "email": f"enseignant{i + 1}@example.com",
            "occupations": [],
            "indispos": generate_teacher_unavailabilities(today, parametres["dateFinSoutenance"])
        })

    return salles, parametres, occupations_salles, enseignants

def generate_teacher_unavailabilities(start_date, end_date):
    indispos = []
    current_date = start_date
    while current_date <= end_date:
        if random.random() < 0.2:  # 20% chance a teacher is unavailable for the whole day
            indispos.append({
                "date": current_date,
                "heure_debut": time(8, 0),
                "heure_fin": time(18, 0)
            })
        else:
            # 50% chance the teacher is unavailable for a random period within the day
            if random.random() < 0.5:
                heure_debut = time(random.randint(8, 15), random.choice([0, 30]))
                duree = timedelta(minutes=random.choice([90, 120, 180]))
                heure_fin = (datetime.combine(datetime.today(), heure_debut) + duree).time()
                indispos.append({
                    "date": current_date,
                    "heure_debut": heure_debut,
                    "heure_fin": heure_fin
                })
        current_date += timedelta(days=1)
    return indispos

def generate_creneaux(heure_debut, heure_fin, duree_soutenance, ecart_soutenance):
    creneaux = []
    current_time = datetime.combine(datetime.today(), heure_debut)
    end_time = datetime.combine(datetime.today(), heure_fin)
    duree_soutenance_delta = timedelta(minutes=duree_soutenance)
    ecart_soutenance_delta = timedelta(minutes=ecart_soutenance)

    while current_time + duree_soutenance_delta <= end_time:
        creneaux.append({
            "heureD": current_time.time(),
            "heureF": (current_time + duree_soutenance_delta).time()
        })
        current_time += duree_soutenance_delta + ecart_soutenance_delta

    return creneaux

def is_salle_disponible(date, heureD, heureF, occupations_salles, num_bloc, num_salle):
    for occupation in occupations_salles:
        if (occupation["date_occupation"].date() == date.date() and
            occupation["num_bloc"] == num_bloc and
            occupation["num_salle"] == num_salle and
            not (heureF <= occupation["heure_debut"] or heureD >= occupation["heure_fin"])):
            return False
    return True

def is_enseignant_disponible(email, jour, heureD, heureF, enseignants):
    for enseignant in enseignants:
        if enseignant["email"] == email:
            for occupation in enseignant["occupations"]:
                if not (heureF <= occupation["heure_debut"] or heureD >= occupation["heure_fin"]):
                    return False
            for indispo in enseignant["indispos"]:
                if (indispo["date"].date() == jour and
                    not (heureF <= indispo["heure_debut"] or heureD >= indispo["heure_fin"])):
                    return False
    return True

def assign_occupations(jury, current_date, creneau):
    for enseignant in jury:
        enseignant["occupations"].append({
            "date": current_date,
            "heure_debut": creneau["heureD"],
            "heure_fin": creneau["heureF"]
        })

def generate_planning(salles, parametres, occupations_salles, enseignants):
    planning = defaultdict(lambda: defaultdict(list))
    
    start_date = parametres["dateDebSoutenance"]
    end_date = parametres["dateFinSoutenance"]
    duree_soutenance = parametres["dureeSoutenance"]
    ecart_soutenance = parametres["ecartSoutenance"]

    jour_debut = time(8, 0)
    jour_fin = time(18, 0)

    current_date = start_date
    while current_date <= end_date:
        jour_semaine = current_date.strftime("%A")
        creneaux = generate_creneaux(jour_debut, jour_fin, duree_soutenance, ecart_soutenance)

        for creneau in creneaux:
            for salle in salles:
                if not is_salle_disponible(current_date, creneau["heureD"], creneau["heureF"], occupations_salles, salle["num_bloc"], salle["num_salle"]):
                    continue
                
                jury = random.sample(enseignants, 5)
                if all(is_enseignant_disponible(enseignant["email"], current_date, creneau["heureD"], creneau["heureF"], enseignants) for enseignant in jury):
                    assign_occupations(jury, current_date, creneau)

                    creneau_info = {
                        "heure_debut": creneau["heureD"].strftime("%H:%M"),
                        "heure_fin": creneau["heureF"].strftime("%H:%M"),
                        "salle": f"{salle['num_bloc']}-{salle['num_salle']}",
                        "enseignants": [enseignant["email"] for enseignant in jury],
                        "leader_groupe": "leader@example.com"  # Replace with actual data
                    }

                    planning[jour_semaine][creneau["heureD"].strftime("%H:%M")].append(creneau_info)

        current_date += timedelta(days=1)
        
    return planning


# Explanation:
# Rooms: We now generate 20 rooms to ensure a sufficient number of venues for the soutenances.

# Extended Date Range: The period for soutenances has been extended to 60 days, allowing for more scheduling opportunities.

# Room Occupations: A total of 100 room occupations are generated dynamically, representing a more realistic and varied schedule.

# Teachers: The number of teachers has been increased to 30, with dynamic unavailabilities ensuring realistic constraints in scheduling.

# Teacher Unavailabilities: Teachers' unavailabilities are generated to reflect different patterns, including full-day unavailabilities and partial-day periods.

# This comprehensive approach will ensure that the planning schedule is well-populated with multiple soutenances occurring daily, adhering to real-world constraints and requirements.