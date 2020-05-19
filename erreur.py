from collections import OrderedDict
from operator import itemgetter
import json

class Erreur:
    """Classe définissant une erreur caractérisée par :
    - son type
    - identifie contexts ou utilisateurs
    - nombre affectés (contexts ou utilisateurs) 
    - format sortie
    - nom_complet erreur
    - message de sortie
    - Le Head du message de sortie"""

    
    def __init__(self, data_json):

        self.type_erreur = data_json["type"]
        self.name=data_json["full_name"]
        self.expression_to_check=data_json["expression_to_look"]
        self.identify = data_json["identify"]
        self.type_file = data_json["type_exit_file"]
        self.name_exit_file=data_json["full_name"]+data_json["type_exit_file"]
        self.nb_affected = 0
        self.exit_message=data_json["message_exit_file"]
        self.head_file=data_json["message_exit_file"]
        self.object=self.findTypeObect()
        self.path_to_past_results="Results_Job/"
    
    def findTypeObect(self):
        if self.identify=="users":
            return []
        else:
            return OrderedDict()
    
    def setObject(self,newObject):
        self.object=newObject
    
    def countErrors(self):
        self.nb_affected = len(self.object)
    
    def initiateErrorMessage(self):
        self.exit_message=str(self.nb_affected)+self.exit_message

    def sortObject(self):
        if self.name=="Contexts are missing" or self.name=="Roles are different" or self.name=="Organizational Context added" or self.name=="Organizational Context removed":
            if self.name=="Contexts are missing":
                    key_order = ('context', 'total_users', 'user')
                    itemToSort='total_users'
            elif self.name=="Roles are different":
                key_order=("context","total_change_for_context","differences")
                itemToSort='total_change_for_context'
            elif self.name=="Organizational Context added" or self.name=="Organizational Context removed":
                key_order=("context","nb users","users")
                itemToSort='nb users'
            current_error=self.object
            list_error=[]
            for dictionnary in current_error:
                if dictionnary!="total_added_admin_roles" and dictionnary!="total_removed_admin_roles" and dictionnary!="total_duplicated_admin_roles":
                    current_error[dictionnary]["context"]=dictionnary
                    new_queue = OrderedDict()
                    for k in key_order:
                        new_queue[k] = current_error[dictionnary][k]
                    current_error[dictionnary]=new_queue
                    list_error.append(current_error[dictionnary])
     
            list_error=sorted(list_error, key=itemgetter(itemToSort),reverse=True)
            if self.name=="Roles are different":
                list_error.insert(0,current_error["total_added_admin_roles"])
                list_error.insert(0,current_error["total_removed_admin_roles"])
                list_error.insert(0,current_error["total_duplicated_admin_roles"])

            self.object=list_error
    
    def createFilesResults(self):
        with open(self.path_to_past_results+self.name_exit_file,'w') as f:
            f.write("%s" % self.exit_message)
            if self.type_file==".json":
                json.dump(self.object, f,indent=4, separators=(',', ': '),ensure_ascii=True)
            else:
                for item in self.object:
                    f.write("%s\n" % item)
        