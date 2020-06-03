import os
import json
import sys
from collections import OrderedDict
from operator import itemgetter
import erreur
import re

countfailed=0
countwarning=0
countskipped=0
countcontext=0
list_successfull_users=[]
"""
Check the results from immigration from allure-results.json files. 
Take as input the repository that contains all allure-results folders.
The allure-results folders need to be in the same directory. 
The name of all allure-results folders need to contains "allure-results".
Example of names :
    -"allure-results_1" : directory for results for batch 1
    -"allure-results_2" : directory for results for batch 2
    .......


There is 1 folder as output named Results_Jobs that contains 6 files :
    -Results_Job/global report of errors.txt is a file that reports the numbers and kinds of errors that occured.
    -Results_Job/context_missing_with_users.txt identify all missing contexts matching with the users.
    -Results_Job/unique_context_missing.txt lists all unique missing contexts
    -Results_Job/length_element_bigger.txt reports users with failed error : Schema validation error\n[Error] Element length must be lower or equal to 50!
    -Results_Job/user_missing.txt reports users with failed error : User doesnt exist.
    -Results_Job/others_errors.txt reports all others issues matching with the users.

usage: python check_results_migration.py <folder with all allure_results directory>

"""
dictMapErrors={}
def createErrorsInstancesFromJson():
    json_to_read="errors.json"
    global dictMapErrors

    with open(json_to_read) as file_to_read:
        data = json.load(file_to_read)
    for error in data:
        name_dict=error["full_name"].replace(" ","_")
        dictMapErrors[name_dict]=erreur.Erreur(error)

def getTestsUsers():
    global dictMapErrors
    list_tests={}
    for error in dictMapErrors:
        if (dictMapErrors[error].type_erreur!="[USER DIFFERENCES]" and dictMapErrors[error].type_erreur!="User not migrated correctly" 
            and dictMapErrors[error].type_erreur not in list_tests.keys()):

            list_tests[(dictMapErrors[error].type_erreur)]=error

    return list_tests

def listAllAllureResultsFolder(path_allure_results):
    if path_allure_results[-1]!="/":
        path_allure_results+="/"
    list_allure_results_folders = [path_allure_results+ f+"/" for f in os.listdir(path_allure_results) if (os.path.isdir(path_allure_results+ f) and "allure-results" in f)]
    return list_allure_results_folders

def createFolderForCheckingResults():
    path_to_past_results="Results_Job/"
    try:
        os.mkdir(path_to_past_results)
    except OSError:
        print ("Creation of the directory %s failed, it probably already exists." % path_to_past_results)
    else:
        print ("Successfully created the directory Results_Job for results %s " % path_to_past_results)
    return path_to_past_results
    
def findTypeContext(context):
    context_number=re.sub("[^0-9]", "", context)
    if int(context_number)>999:
        return "partners"
    else:
        return "importers"

def treatRolesDifferent(message,user_id):
    global dictMapErrors
    dict_context_roles_users=dictMapErrors["Roles_are_different"].object          
    all_contexts_changes=message.split("Roles are different")[1:]
    if "total_added_admin_roles" not in dict_context_roles_users.keys():
        dict_context_roles_users["total_added_admin_roles"]=0
        dict_context_roles_users["total_removed_admin_roles"]=0
        dict_context_roles_users["total_duplicated_admin_roles"]=0
    for context_changed in all_contexts_changes:

        list_added=[]
        list_removed=[]
        list_duplicate=[]
        context=context_changed.split("in ")[1].split(" New")[0]
        roles_admin_partners=(1,22,27)
        roles_admin_importers=(1,22,2)
        type_context=findTypeContext(context)
        if type_context=="partners":
            roles_admin=roles_admin_partners
        else:
            roles_admin=roles_admin_importers
        

        new_old=context_changed.split("Old",1)

        new=new_old[0].split("New ")[1][2:-3]
        old=new_old[1].split("\n",1)[0].replace(" ", "")[1:-1]
        list_new=new.split(",")
        list_old=old.split(",")
        for new in list_new:
            try:
                list_new[list_new.index(new)]=int(new)
            except:
                list_new=[]
        for old in list_old:
            try:
                list_old[list_old.index(old)]=int(old)
            except:
                list_old=[]
        for new in list_new:
            if new not in list_old and new in roles_admin:
                list_added.append(new)
                dict_context_roles_users["total_added_admin_roles"]+=1
                
                
        for old in list_old:
            if old not in list_new and old in roles_admin:
                list_removed.append(old)
                dict_context_roles_users["total_removed_admin_roles"]+=1
            if list_new.count(old)>1 and old in roles_admin:
                list_duplicate.append(old)
                dict_context_roles_users["total_duplicated_admin_roles"]+=1
        
        if list_duplicate!=[] or list_removed!=[] or list_added!=[]:

            difference="+ : " + str(list_added)+ " ; - : "+str(list_removed)+" ; duplicate : "+str(list_duplicate)

            if context not in dict_context_roles_users.keys():
                dict_context_roles_users[context]={}
                dict_context_roles_users[context]["differences"]=OrderedDict()
                dict_context_roles_users[context]["total_change_for_context"]=0    
            if difference not in dict_context_roles_users[context]["differences"].keys():
                dict_context_roles_users[context]["differences"][difference]=OrderedDict()
                dict_context_roles_users[context]["differences"][difference]["number of users with this context with this difference"]=0
                dict_context_roles_users[context]["differences"][difference]["user"]=[]
                
            dict_context_roles_users[context]["differences"][difference]["number of users with this context with this difference"]+=1
            dict_context_roles_users[context]["differences"][difference]["user"].append(user_id)
            dict_context_roles_users[context]["total_change_for_context"]+=1

    dictMapErrors["Roles_are_different"].setObject(dict_context_roles_users)


def treatOrgaContextChanged(message,user_id):
    global dictMapErrors
    orga_context_added=dictMapErrors["Organizational_Context_added"].object
    orga_context_removed=dictMapErrors["Organizational_Context_removed"].object
    all_contexts_changed=message.split("Organizational Context")[1:]
    for context_changed in all_contexts_changed:
        action=context_changed.split("[")[0].replace(" ","")
        context=context_changed.split("[")[1].split("]",1)[0]
        if action=="added":
            dictionnaryToUse=orga_context_added
        else:
            dictionnaryToUse=orga_context_removed
        if context not in dictionnaryToUse.keys():
            dictionnaryToUse[context]={}
            dictionnaryToUse[context]["nb users"]=0
            dictionnaryToUse[context]["users"]=[]
        dictionnaryToUse[context]["nb users"]+=1
        dictionnaryToUse[context]["users"].append(user_id)
        if action=="added":
            orga_context_added=dictionnaryToUse
        else:
            orga_context_removed=dictionnaryToUse
    dictMapErrors["Organizational_Context_added"].setObject(orga_context_added)   
    dictMapErrors["Organizational_Context_removed"].setObject(orga_context_removed)
    

def getIdFromJson(data):
    name=data["name"]
    if 'UserFileDifference_test' in name :
        id=name.split("| ",1)[1].split("]",1)[0]
    elif 'ThirdPartyOrgsFileDifference_test' in name:
        id=name.split("[",1)[1].split("]",1)[0]
    elif 'UserMigration_test' in name:
        id=name.split("[",1)[1].split(" |",1)[0]
        """
        if len(id)>10:
            try:
                id=data["steps"][0]["name"].split("[",1)[1].split(",",1)[1][1:-1]
            except:
                id=data["steps"][0]["name"].split("[",1)[1].split(",",1)[0][:-1]
        """
    elif 'ThirdPartyOrg_test' in name:
        id=data["steps"][0]["name"].split(": ",1)[1]
    else:
        id=name
    return id

def IsKnownUserDiffError(message):
    if ("Organizational Context added" in message or "Organizational Context removed" in message 
        or "Communication Channel" in message or "First Name is incorrect" in message or "Last Name is incorrect" in message
        or "Roles are different" in message):
        return True
    else:
        return False

def isKnownError(message):
    listError=["User does not exist","Schema validation error\n[Error] Element length must be lower or equal to 50!",
        "[USER DIFFERENCES]","Context","[NEW USER]","[REMOVED USER]","[NEW ORGANIZATION]","[REMOVED ORGANIZATION]",
        "User not migrated correctly"]
    for error in listError:
        if error in message:
            return True
    else:
        return False


def treatUserNotMigratedCorrectly(message,total_of_failures_missing_context,other_errors,user_id):
    global dictMapErrors
    global countcontext
    dict_context_missing=dictMapErrors["Contexts_are_missing"].object
    dict_context_not_found_after_migration=dictMapErrors["Context_not_found_after_migration"].object
    list_users_not_found_w_uid=dictMapErrors["User_found_not_by_expected_UID"].object
    if "Context" in message and "not exists" in message:
        list_contexts=message.split("Context")[1:]
        for context in list_contexts:
            try:
                context = context.split("'")[1]
            except:
                context = context.split("not exists: ")[1].split("\n",1)[0]
            if context=="DEU189V":
                countcontext+=1
            if context not in dict_context_missing.keys():
                dict_context_missing[context]=OrderedDict()
                dict_context_missing[context]["total_users"]=0
                dict_context_missing[context]["user"]=[]
            dict_context_missing[context]["user"].append(user_id)
            dict_context_missing[context]["total_users"]+=1
            total_of_failures_missing_context+=1
    if "context not found after migration":
        list_contexts=message.split("Context not found after migration ")[1:]
        for context in list_contexts:
            try:
                context = context.split("[")[1].split("]")[0]
            except:
                context = context.split("not exists: ")[1].split("\n",1)[0]
            if context not in dict_context_not_found_after_migration.keys():
                dict_context_not_found_after_migration[context]=OrderedDict()
                dict_context_not_found_after_migration[context]["total_users"]=0
                dict_context_not_found_after_migration[context]["user"]=[]
            dict_context_not_found_after_migration[context]["user"].append(user_id)
            dict_context_not_found_after_migration[context]["total_users"]+=1
            total_of_failures_missing_context+=1
    if "Communication Channel" in message or "First Name" in message or "Last Name" in message:
        other_errors=treatUserDifferences(message,user_id,other_errors)
    if "User found not by expected UID" in message:
        list_users_not_found_w_uid.append(user_id)
    else:
        other_errors[user_id]=message
    dictMapErrors["Contexts_are_missing"].setObject(dict_context_missing)
    dictMapErrors["Context_not_found_after_migration"].setObject(dict_context_not_found_after_migration)
    dictMapErrors["User_found_not_by_expected_UID"].setObject(list_users_not_found_w_uid)
    return total_of_failures_missing_context,other_errors

def treatUserDifferences(message,user_id,other_errors):
    global dictMapErrors
    if IsKnownUserDiffError(message):
        if "Organizational Context added" in message or "Organizational Context removed" in message:
            treatOrgaContextChanged(message,user_id)
        if ("Communication Channel" in message or "First Name is incorrect" in message or "Last Name is incorrect" in message):
            dictMapErrors["User_data_changed"].object.append(user_id)
        if "Roles are different" in message:
            treatRolesDifferent(message,user_id)
    else:
        other_errors[user_id]=message
    
    return other_errors


def treat_json_file_results(json_file,total_of_failures_missing_context,list_test_users):
    global dictMapErrors
    global countfailed
    global countwarning
    global countskipped
    global countcontext
    global list_successfull_users
    other_errors={}
    with open(json_file) as file_to_read:
        data = json.load(file_to_read)
        if type(data) is list:
            print (json_file +" is not a result from migration")
        elif "status" in data.keys() and data["status"]=="failed":
            countfailed+=1
            user_id=getIdFromJson(data)
            message=data["statusDetails"]["message"]
            if isKnownError(message):
                for test in list_test_users:
                    if test==message:
                        dictMapErrors[list_test_users[test]].object.append(user_id)
                if "[USER DIFFERENCES]" in message:
                    other_errors=treatUserDifferences(message,user_id,other_errors)
                if "User not migrated correctly" in message:          
                    total_of_failures_missing_context,other_errors=treatUserNotMigratedCorrectly(message,total_of_failures_missing_context,other_errors,user_id)
                    
            else:
                other_errors[user_id]=message
        
        elif "status" in data.keys() and data["status"]=="broken":
            countwarning+=1
            user_id=getIdFromJson(data)
            message=data["statusDetails"]["message"]
            if "User not migrated correctly" in message:          
                total_of_failures_missing_context,other_errors=treatUserNotMigratedCorrectly(message,total_of_failures_missing_context,other_errors,user_id)
        elif "status" in data.keys() and data["status"]=="skipped":
            user_id=getIdFromJson(data)
            message=data["statusDetails"]["message"]
            countskipped+=1
            for test in list_test_users:
                if test==message:
                    dictMapErrors[list_test_users[test]].object.append(user_id)

        elif "UserMigration_test" in data["name"] and data["status"]=="passed":

            user_id=getIdFromJson(data)
            list_successfull_users.append(user_id)

    return total_of_failures_missing_context,other_errors

def countandCreateErrorsMessages(total_of_failures_missing_context,other_errors):
    global dictMapErrors
    global countfailed
    global countwarning
    global countskipped
    number_errors=OrderedDict()
   

    for error in dictMapErrors:
        dictMapErrors[error].countErrors()
        dictMapErrors[error].initiateErrorMessage()

    number_errors["other_errors"]=len(other_errors)
    number_errors["failures_missing_context"]=total_of_failures_missing_context
    number_errors["total_users_errors"]=countfailed
    number_errors["total_users_warning"]=countwarning
    number_errors["total_users_skipped"]=countskipped

    error_messages=[]
    error_messages.append(str(number_errors["total_users_errors"])+" users have at least 1 error")
    error_messages.append(str(number_errors["total_users_warning"])+" users have at least 1 warning")
    error_messages.append(str(number_errors["total_users_skipped"])+" users have at least 1 skipped error")
    error_messages.append(str(number_errors["failures_missing_context"])+" errors with missing contexts")
    error_messages.append(str(number_errors["other_errors"])+" other errors")
    return number_errors,error_messages

def printAndSaveReportErrorMessages(path_to_past_results,error_messages):
    global dictMapErrors
    global list_successfull_users
    with open(path_to_past_results+'global report of errors','w') as f:
        for error in dictMapErrors:
            f.write("%s\n" % dictMapErrors[error].exit_message)
            print(dictMapErrors[error].exit_message)
        for error in error_messages:
            f.write("%s\n" % error)
            print(error)
        f.write(str(len(list_successfull_users))+"users successfully migrated")
        print(str(len(list_successfull_users))+"users successfully migrated")
    print("Check Results_Job folders to see results in details")

def createFilesResults(path_to_past_results,error_messages,number_errors,other_errors):
    printAndSaveReportErrorMessages(path_to_past_results,error_messages)
    createFilesResultsByErrorTypes(path_to_past_results,number_errors,other_errors)

def sortDictionnaryForJson():
    global dictMapErrors
    for error in dictMapErrors:
        dictMapErrors[error].sortObject()


def createFilesResultsByErrorTypes(path_to_past_results,number_errors,other_errors):
    global dictMapErrors
    global list_successfull_users

    sortDictionnaryForJson()
    for error in dictMapErrors:
        dictMapErrors[error].createFilesResults()

    
    with open(path_to_past_results+'others_errors.json', 'w') as fp:
        fp.write("%s" % str(number_errors["other_errors"])+" errors. \nList of all others errors\n")
        json.dump(other_errors, fp,indent=4, separators=(',', ': '),ensure_ascii=True)

    with open(path_to_past_results+'successfull_users.txt', 'w') as fp:
        for user in list_successfull_users:
            fp.write("%s\n" % user )
        


def ProcessCheckResults(path_allure_results):
    createErrorsInstancesFromJson()
    list_test_users=getTestsUsers()
    list_allure_results_folders = listAllAllureResultsFolder(path_allure_results)
    path_to_past_results=createFolderForCheckingResults()
    
    total_of_failures_missing_context=0
    for allure_results_folder in list_allure_results_folders:

        list_json_files = [allure_results_folder+ f for f in os.listdir(allure_results_folder) if ".json" in f]

        for json_file in list_json_files:

            total_of_failures_missing_context,other_errors=treat_json_file_results(json_file,total_of_failures_missing_context,list_test_users)

    
    number_errors,error_messages=countandCreateErrorsMessages(total_of_failures_missing_context,other_errors)



    createFilesResults(path_to_past_results,error_messages,number_errors,other_errors)


if len(sys.argv) < 2:
    print("Check results errors from migration with json files in allure-results folders.\nusage: python check_results_migration.py <folder with all allure_results directory>")
    

path_allure_results=sys.argv[1]

#path_allure_results="/Users/nael/Work/Migration/results/"
ProcessCheckResults(path_allure_results)
print("nb occurence contexte="+str(countcontext))