class Erreur:
    """Classe définissant une erreur caractérisée par :
    - son type
    - identifie contexts ou utilisateurs
    - nombre affectés (contexts ou utilisateurs) 
    - format sortie
    - nom_complet erreur
    - message de sortie
    - Le Head du message de sortie"""

    
    def __init__(self, type_erreur, identify,type_file,full_name_error,exit_message,head_file):
        """Constructeur de notre classe"""
        self.type_erreur = type_erreur
        self.identify = identify
        self.type_file = type_file
        self.nb_affected = 0
        self.full_name_error=full_name_error
        self.exit_message=exit_message
        self.head_file=head_file