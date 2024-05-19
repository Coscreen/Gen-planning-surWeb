import logging
from datetime import datetime, timedelta, time
import random
from django.shortcuts import render

logger = logging.getLogger(__name__)

def renderIndex(request):
    logger.debug("Entered renderIndex view")
    
    # Appel de la fonction pour récupérer les données
    salles, parametres, occupations_salles, enseignants = get_data()
    
    # Génération des données de planification
    planning = generate_planning(salles, parametres, occupations_salles, enseignants)
    logger.debug("Generated planning data: %s", planning)
    
    planning_hours = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Transmission des données au template
    context = {
        'planning': planning,
        'planning_hours': planning_hours,
        'days': days,
    }
    
    logger.debug("Context to be passed to template: %s", context)
    return render(request, 'planning.html', context)



def get_data():
    salles = [
        {"num_bloc": 1, "num_salle": 101},
        {"num_bloc": 1, "num_salle": 102},
        {"num_bloc": 1, "num_salle": 103},
        {"num_bloc": 1, "num_salle": 104},
        {"num_bloc": 2, "num_salle": 201},
        {"num_bloc": 2, "num_salle": 202},
        {"num_bloc": 2, "num_salle": 203},
        {"num_bloc": 2, "num_salle": 204}
    ]

    parametres = {
        "dateDebSoutenance": datetime(2024, 6, 1),
        "dateFinSoutenance": datetime(2024, 6, 30),
        "dureeSoutenance": 90,  # en minutes
        "ecartSoutenance": 30,  # en minutes
        "anneeSoutenance": 2024
    }

    occupations_salles = [
        {"date_occupation": datetime(2024, 6, 1), "heure_debut": time(8, 0), "heure_fin": time(10, 0), "num_bloc": 1, "num_salle": 101},
        {"date_occupation": datetime(2024, 6, 2), "heure_debut": time(9, 0), "heure_fin": time(11, 0), "num_bloc": 1, "num_salle": 102},
        {"date_occupation": datetime(2024, 6, 3), "heure_debut": time(14, 0), "heure_fin": time(16, 0), "num_bloc": 2, "num_salle": 201}
    ]

    enseignants = [
        {"email": f"enseignant{i + 1}@example.com", "occupations": [], "indispos": []} for i in range(8)
    ]

    return salles, parametres, occupations_salles, enseignants

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
    return True

def assign_occupations(jury, current_date, creneau):
    for enseignant in jury:
        enseignant["occupations"].append({
            "date": current_date,
            "heure_debut": creneau["heureD"],
            "heure_fin": creneau["heureF"]
        })

def generate_planning(salles, parametres, occupations_salles, enseignants):
    logger.debug("Data retrieved from get_data: salles=%s, parametres=%s, occupations_salles=%s, enseignants=%s", salles, parametres, occupations_salles, enseignants)
    
    # Inclure tous les jours de la semaine
    planning = {day: {} for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}
    
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
                if all(is_enseignant_disponible(enseignant["email"], jour_semaine, creneau["heureD"], creneau["heureF"], enseignants) for enseignant in jury):
                    assign_occupations(jury, current_date, creneau)

                    creneau_info = {
                        "heure_debut": creneau["heureD"].strftime("%H:%M"),
                        "heure_fin": creneau["heureF"].strftime("%H:%M"),
                        "salle": f"{salle['num_bloc']}-{salle['num_salle']}",
                        "enseignants": [enseignant["email"] for enseignant in jury],
                        "leader_groupe": "leader@example.com"  # Exemple, à remplacer par la donnée réelle
                    }

                    heure_str = creneau["heureD"].strftime("%H:%M")
                    if heure_str not in planning[jour_semaine]:
                        planning[jour_semaine][heure_str] = []
                    
                    planning[jour_semaine][heure_str].append(creneau_info)

        current_date += timedelta(days=1)
    
    logger.debug("Generated planning data: %s", planning)
    return planning


# def planning_view(request):
#     logger.debug("Entered planning_view")
#     salles, parametres, occupations_salles, enseignants = get_data()
#     planning = generate_planning(salles, parametres, occupations_salles, enseignants)
    
#     # Génération de la liste des heures
#     duree_soutenance = timedelta(minutes=parametres["dureeSoutenance"])
#     ecart_soutenance = timedelta(minutes=parametres["ecartSoutenance"])
#     planning_hours = []
#     current_time = datetime.combine(datetime.today(), time(8, 0))
#     end_time = datetime.combine(datetime.today(), time(18, 0))
#     while current_time < end_time:
#         planning_hours.append(current_time.strftime("%H:%M"))
#         current_time += duree_soutenance + ecart_soutenance

#     # Liste des jours de la semaine
#     days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

#     logger.debug("Planning data to be passed to template: %s", planning)
#     logger.debug("Planning hours: %s", planning_hours)
#     logger.debug("Days: %s", days)
    
#     return render(request, 'planning.html', {
#         'planning': planning, 
#         'planning_hours': planning_hours, 
#         'days': days
#     })


def planning_view(request):
    planning = {
        'Sunday': {
            '08:00': [
                {
                    'heure_debut': '08:00',
                    'heure_fin': '09:30',
                    'salle': '1-101',
                    'enseignants': ['Dr. Smith', 'Prof. Johnson'],
                    'leader_groupe': 'Alice'
                }
            ]
        },
        'Monday': {},
        'Tuesday': {},
        'Wednesday': {
            '10:00': [
                {
                    'heure_debut': '10:00',
                    'heure_fin': '11:30',
                    'salle': '2-201',
                    'enseignants': ['Prof. Brown', 'Dr. White'],
                    'leader_groupe': 'Bob'
                }
            ]
        },
        'Thursday': {},
        'Friday': {
            '14:00': [
                {
                    'heure_debut': '14:00',
                    'heure_fin': '15:30',
                    'salle': '3-301',
                    'enseignants': ['Dr. Green', 'Prof. Blue'],
                    'leader_groupe': 'Charlie'
                }
            ]
        },
        'Saturday': {
            '08:00': [
                {
                    'heure_debut': '08:00',
                    'heure_fin': '09:30',
                    'salle': '1-102',
                    'enseignants': ['Dr. Smith', 'Prof. Johnson'],
                    'leader_groupe': 'Alice'
                }
            ]
        }
    }

    planning_hours = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    context = {
        'planning': planning,
        'planning_hours': planning_hours,
        'days': days,
    }

    return render(request, 'dj/planning.html', context)






