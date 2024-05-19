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
    
    # Transmission des données au template
    context = {
        'planning': planning,
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
        {"email": f"enseignant{i + 1}@example.com", "occupations": [], "indispos": []} for i in range(15)
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
    all_seances = []

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
        jour_planning = {
            "date": current_date.strftime("%Y-%m-%d"),
            "jour": jour_semaine,
            "creneaux": []
        }
        
        for creneau in creneaux:
            for salle in salles:
                if not is_salle_disponible(current_date, creneau["heureD"], creneau["heureF"], occupations_salles, salle["num_bloc"], salle["num_salle"]):
                    continue
                
                jury = random.sample(enseignants, 5)
                if all(is_enseignant_disponible(enseignant["email"], jour_semaine, creneau["heureD"], creneau["heureF"], enseignants) for enseignant in jury):
                    assign_occupations(jury, current_date, creneau)
                    peine = 0
                    if jour_semaine == "Sunday":
                        peine += 1
                    elif jour_semaine == "Thursday":
                        peine += 2
                    
                    if creneau["heureD"] == time(8, 0):
                        peine += 1
                    elif creneau["heureD"] == time(14, 40):
                        peine += 2
                    elif creneau["heureD"] == time(16, 20):
                        peine += 3

                    creneau_info = {
                        "heure_debut": creneau["heureD"].strftime("%H:%M"),
                        "heure_fin": creneau["heureF"].strftime("%H:%M"),
                        "salle": f"{salle['num_bloc']}-{salle['num_salle']}",
                        "enseignants": ", ".join([enseignant["email"] for enseignant in jury]),
                        "peine": peine
                    }
                    jour_planning["creneaux"].append(creneau_info)

        all_seances.append(jour_planning)
        current_date += timedelta(days=1)
    
    logger.debug("Generated planning data: %s", all_seances)
    return all_seances

def planning_view(request):
    logger.debug("Entered planning_view")
    planning = generate_planning(*get_data())
    logger.debug("Planning data to be passed to template: %s", planning)
    return render(request, 'planning.html', {'planning': planning})
