from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset
import datetime
import random
import string
import sqlite3
import os

def get_db_connection():
    """Établit une connexion à la base de données SQLite et crée la table si elle n'existe pas."""
    # Chemin local pour la base de données
    DB_PATH = 'C:\data\restaurant.db'
    
    if not os.path.exists(DB_PATH):
      conn = sqlite3.connect(DB_PATH)
      cursor = conn.cursor()
      cursor.execute('''
      CREATE TABLE IF NOT EXISTS reservations (
        id TEXT PRIMARY KEY,
        name TEXT,
        date TEXT,
        time TEXT,
        number_of_people INTEGER,
        phone_number TEXT,
        comment TEXT,
        status TEXT DEFAULT 'active'
      )
      ''')
      conn.commit()
    else:
      conn = sqlite3.connect(DB_PATH)
    return conn

class ActionCheckAvailability(Action):
    """Vérifie la disponibilité d'une table pour la réservation."""

    def name(self) -> Text:
        return "action_check_availability"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        date = tracker.get_slot("date")
        time = tracker.get_slot("time")
        number_of_people = tracker.get_slot("number_of_people")

        # Simuler une vérification de disponibilité
        availability = random.choice([True, True, True, False])

        if availability:
            dispatcher.utter_message(text=f"Bonne nouvelle! Nous avons une table disponible pour {number_of_people} personnes le {date} à {time}.")
        else:
            dispatcher.utter_message(text=f"Je suis désolé, nous n'avons pas de table disponible pour {number_of_people} personnes le {date} à {time}. Souhaitez-vous essayer un autre horaire?")

        return [SlotSet("availability", availability)]

class ValidateBookingForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_booking_form"

    def validate_date(self, slot_value: Any, dispatcher: CollectingDispatcher,
                      tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        return {"date": slot_value}

    def validate_time(self, slot_value: Any, dispatcher: CollectingDispatcher,
                      tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        return {"time": slot_value}

    def validate_number_of_people(self, slot_value: Any, dispatcher: CollectingDispatcher,
                                   tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            if isinstance(slot_value, str):
                slot_value = int(slot_value)

            if slot_value <= 0:
                dispatcher.utter_message(text="Le nombre de personnes doit être positif.")
                return {"number_of_people": None}
            if slot_value > 20:
                dispatcher.utter_message(text="Nous ne pouvons pas accueillir plus de 20 personnes. Contactez-nous pour les groupes.")
                return {"number_of_people": None}
            return {"number_of_people": slot_value}
        except ValueError:
            dispatcher.utter_message(text="Veuillez indiquer un nombre valide de personnes.")
            return {"number_of_people": None}

    def validate_phone_number(self, slot_value: Any, dispatcher: CollectingDispatcher,
                              tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        if len(slot_value.replace(" ", "")) < 10:
            dispatcher.utter_message(text="Le numéro de téléphone semble trop court.")
            return {"phone_number": None}
        return {"phone_number": slot_value}

class ActionGenerateReservationID(Action):
    def name(self) -> Text:
        return "action_generate_reservation_id"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        name = tracker.get_slot("name")
        date = tracker.get_slot("date")
        time = tracker.get_slot("time")
        number_of_people = tracker.get_slot("number_of_people")
        phone_number = tracker.get_slot("phone_number")

        reservation_id = "RES" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reservations (id, name, date, time, number_of_people, phone_number) VALUES (?, ?, ?, ?, ?, ?)",
            (reservation_id, name, date, time, number_of_people, phone_number)
        )
        conn.commit()
        conn.close()

        dispatcher.utter_message(text=f"Votre réservation est confirmée. Numéro: {reservation_id}.")

        return [SlotSet("reservation_id", reservation_id)]

class ActionGetReservationInfo(Action):
    def name(self) -> Text:
        return "action_get_reservation_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        reservation_id = tracker.get_slot("reservation_id")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reservations WHERE id = ? AND status = 'active'", (reservation_id,))
        reservation = cursor.fetchone()
        conn.close()

        if reservation:
            id, name, date, time, number_of_people, phone_number, comment, status = reservation
            message = f"Détails de la réservation {id}:\n- Nom: {name}\n- Date: {date}\n- Heure: {time}\n- Nombre de personnes: {number_of_people}\n- Téléphone: {phone_number}"
            if comment:
                message += f"\n- Commentaire: {comment}"
            dispatcher.utter_message(text=message)
            return [
                SlotSet("name", name), SlotSet("date", date), SlotSet("time", time),
                SlotSet("number_of_people", number_of_people), SlotSet("phone_number", phone_number),
                SlotSet("comment", comment)
            ]
        else:
            dispatcher.utter_message(text="Aucune réservation active trouvée.")
            return []

class ActionAddComment(Action):
    def name(self) -> Text:
        return "action_add_comment"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        reservation_id = tracker.get_slot("reservation_id")
        comment = tracker.get_slot("comment")

        if not reservation_id:
            dispatcher.utter_message(text="Merci de fournir un identifiant de réservation.")
            return []

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE reservations SET comment = ? WHERE id = ? AND status = 'active'", (comment, reservation_id))

        if cursor.rowcount > 0:
            conn.commit()
            dispatcher.utter_message(text="Commentaire ajouté avec succès.")
        else:
            dispatcher.utter_message(text="Réservation non trouvée ou déjà annulée.")
        conn.close()
        return []

class ActionModifyComment(Action):
    def name(self) -> Text:
        return "action_modify_comment"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        reservation_id = tracker.get_slot("reservation_id")
        comment = tracker.get_slot("comment")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE reservations SET comment = ? WHERE id = ? AND status = 'active'", (comment, reservation_id))

        if cursor.rowcount > 0:
            conn.commit()
            dispatcher.utter_message(text="Le commentaire a été mis à jour avec succès.")
        else:
            dispatcher.utter_message(text="Impossible de mettre à jour le commentaire. Réservation non trouvée.")
        conn.close()
        return []

class ActionCancelReservation(Action):
    def name(self) -> Text:
        return "action_cancel_reservation"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        reservation_id = tracker.get_slot("reservation_id")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE reservations SET status = 'cancelled' WHERE id = ? AND status = 'active'", (reservation_id,))

        if cursor.rowcount > 0:
            conn.commit()
            dispatcher.utter_message(text="Réservation annulée avec succès.")
            conn.close()
            return [AllSlotsReset()]
        else:
            conn.close()
            dispatcher.utter_message(text="Aucune réservation active trouvée.")
            return []

class ActionSubmitReservation(Action):
    def name(self) -> Text:
        return "action_submit_reservation"

    def run(self, dispatcher, tracker, domain):
        number_of_people = tracker.get_slot("number_of_people")
        date = tracker.get_slot("date")
        time = tracker.get_slot("time")
        name = tracker.get_slot("name")
        phone = tracker.get_slot("phone_number")

        dispatcher.utter_message(text=f"Voici un récapitulatif de votre réservation: "
                                      f"Table pour {number_of_people} personnes le {date} à {time}, "
                                      f"au nom de {name}, téléphone: {phone}. Est-ce correct ?")
        return []